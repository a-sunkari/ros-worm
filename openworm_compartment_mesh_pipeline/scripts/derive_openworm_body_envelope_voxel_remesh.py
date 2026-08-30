#!/usr/bin/env python3
"""
Derive a filled whole-body envelope mesh from OpenWorm Cuticle/hyp7 shell meshes.

This is NOT a Geant4 voxel phantom. It uses voxelization only as a robust
remeshing/interior-fill step, then exports a watertight-ish STL mesh suitable
as a candidate Geant4 parent volume.

Why this exists:
- OpenWorm's Cuticle is a biological shell/layer, not a filled body parent.
- Internal organs are visually inside the worm but not inside the Cuticle solid.
- We need a filled external contour mesh: WholeBodyEnvelope.

Dependencies:
  conda install -c conda-forge numpy pandas trimesh scipy scikit-image networkx
Optional:
  conda install -c conda-forge rtree
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import trimesh

try:
    from scipy import ndimage as ndi
except Exception as exc:  # pragma: no cover
    raise SystemExit("Missing scipy. Install with: conda install -c conda-forge scipy") from exc

try:
    from skimage import measure
except Exception as exc:  # pragma: no cover
    raise SystemExit("Missing scikit-image. Install with: conda install -c conda-forge scikit-image") from exc


def find_col(df: pd.DataFrame, candidates: Iterable[str]) -> str:
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    raise KeyError(f"Could not find any of columns {list(candidates)} in {list(df.columns)}")


def load_named_meshes(manifest: Path, names: list[str]) -> list[tuple[str, trimesh.Trimesh]]:
    df = pd.read_csv(manifest)
    name_col = find_col(df, ["object_name", "name", "Object", "object"])
    path_col = find_col(df, ["stl_path", "path", "filepath", "file"])

    out = []
    for name in names:
        row = df[df[name_col].astype(str) == name]
        if row.empty:
            raise SystemExit(f"Name {name!r} not found in manifest column {name_col}")
        path = Path(str(row.iloc[0][path_col])).expanduser()
        if not path.exists():
            # Allow relative paths relative to manifest directory
            rel = manifest.parent / path
            if rel.exists():
                path = rel
            else:
                raise SystemExit(f"STL path for {name!r} does not exist: {path}")
        mesh = trimesh.load_mesh(path, force="mesh", process=True)
        if not isinstance(mesh, trimesh.Trimesh):
            raise SystemExit(f"Loaded {path} but did not get a Trimesh")
        if len(mesh.faces) == 0:
            raise SystemExit(f"Mesh {name!r} has no faces")
        out.append((name, mesh))
    return out


def remove_small_components(mesh: trimesh.Trimesh, keep_largest: int = 1, min_volume_frac: float = 0.0) -> trimesh.Trimesh:
    comps = mesh.split(only_watertight=False)
    if len(comps) <= 1:
        return mesh
    comps_sorted = sorted(comps, key=lambda m: abs(float(m.volume)) if m.is_watertight else float(m.area), reverse=True)
    if keep_largest > 0:
        keep = comps_sorted[:keep_largest]
    else:
        largest_metric = abs(float(comps_sorted[0].volume)) if comps_sorted[0].is_watertight else float(comps_sorted[0].area)
        keep = []
        for comp in comps_sorted:
            metric = abs(float(comp.volume)) if comp.is_watertight else float(comp.area)
            if largest_metric == 0 or metric / largest_metric >= min_volume_frac:
                keep.append(comp)
    return trimesh.util.concatenate(keep)


def clean_mesh(mesh: trimesh.Trimesh, smooth_iters: int = 0) -> trimesh.Trimesh:
    mesh = mesh.copy()
    # Trimesh API changed over time; call only methods that exist.
    for method in ["remove_degenerate_faces", "remove_duplicate_faces", "remove_unreferenced_vertices"]:
        fn = getattr(mesh, method, None)
        if callable(fn):
            try:
                fn()
            except Exception:
                pass
    try:
        trimesh.repair.fix_normals(mesh)
    except Exception:
        pass
    if smooth_iters > 0:
        try:
            trimesh.smoothing.filter_laplacian(mesh, iterations=smooth_iters)
            trimesh.repair.fix_normals(mesh)
        except Exception as exc:
            print(f"[WARN] smoothing failed: {exc!r}")
    return mesh


def voxel_fill_envelope(
    source_mesh: trimesh.Trimesh,
    pitch: float,
    dilation_iters: int = 1,
    closing_iters: int = 1,
    fill_holes: bool = True,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Voxelize shell surface, thicken/close it, then fill interior.

    Returns: filled boolean matrix, origin vector, pitch.
    Matrix axes are x,y,z index axes. Coordinates are origin + index*pitch.
    """
    print(f"[Envelope] source faces={len(source_mesh.faces)} vertices={len(source_mesh.vertices)}")
    print(f"[Envelope] source bounds min={source_mesh.bounds[0]} max={source_mesh.bounds[1]} extents={source_mesh.extents}")
    print(f"[Envelope] voxelizing pitch={pitch:g} model units")

    vg = source_mesh.voxelized(pitch=pitch)
    mat = vg.matrix.astype(bool)
    origin = np.array(vg.transform[:3, 3], dtype=float)

    # Pad so flood fill / hole fill has outside space around the object.
    pad = max(3, dilation_iters + closing_iters + 2)
    mat = np.pad(mat, pad_width=pad, mode="constant", constant_values=False)
    origin = origin - pad * pitch

    print(f"[Envelope] raw voxel matrix shape={mat.shape} occupied={int(mat.sum())}")

    # Thicken thin shell enough to close tiny cracks/gaps introduced by voxelization.
    struct = ndi.generate_binary_structure(3, 2)  # 18-neighborhood
    if dilation_iters > 0:
        mat = ndi.binary_dilation(mat, structure=struct, iterations=dilation_iters)
        print(f"[Envelope] after dilation occupied={int(mat.sum())}")

    if closing_iters > 0:
        mat = ndi.binary_closing(mat, structure=struct, iterations=closing_iters)
        print(f"[Envelope] after closing occupied={int(mat.sum())}")

    if fill_holes:
        filled = ndi.binary_fill_holes(mat, structure=struct)
        print(f"[Envelope] after fill occupied={int(filled.sum())}, added={int(filled.sum() - mat.sum())}")
    else:
        filled = mat

    return filled.astype(bool), origin, pitch


def marching_cubes_to_mesh(filled: np.ndarray, origin: np.ndarray, pitch: float) -> trimesh.Trimesh:
    # marching_cubes expects values where surface at 0.5 splits false/true.
    data = filled.astype(np.float32)
    verts, faces, normals, values = measure.marching_cubes(data, level=0.5, spacing=(pitch, pitch, pitch))
    verts = verts + origin[None, :]
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    return mesh


def main() -> int:
    ap = argparse.ArgumentParser(description="Derive filled whole-body envelope mesh from OpenWorm shell STLs using voxel remeshing.")
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--sources", default="Cuticle,hyp7", help="Comma-separated source object names, default Cuticle,hyp7")
    ap.add_argument("--voxel-um", type=float, default=2.0, help="Voxel pitch in micrometers for intermediate remesh. 1 um = 0.01 model units.")
    ap.add_argument("--um-per-unit", type=float, default=100.0, help="Micrometers per model unit. Default 100, i.e. 0.01 units = 1 um.")
    ap.add_argument("--dilation-iters", type=int, default=1)
    ap.add_argument("--closing-iters", type=int, default=1)
    ap.add_argument("--smooth-iters", type=int, default=2, help="Laplacian smoothing iterations on output mesh. Use 0 to disable.")
    ap.add_argument("--keep-largest", type=int, default=1, help="Keep this many largest connected output components. Default 1.")
    ap.add_argument("--output-name", default="whole_body_envelope.stl")
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    pitch = args.voxel_um / args.um_per_unit

    named = load_named_meshes(args.manifest, sources)
    for name, mesh in named:
        print(f"[Envelope] source {name}: faces={len(mesh.faces)} watertight={mesh.is_watertight} vol={mesh.volume:g} extents={mesh.extents}")

    combined = trimesh.util.concatenate([m for _, m in named])
    # No boolean here. We use combined surfaces only as a shell/barrier for volumetric filling.
    filled, origin, pitch = voxel_fill_envelope(
        combined,
        pitch=pitch,
        dilation_iters=args.dilation_iters,
        closing_iters=args.closing_iters,
        fill_holes=True,
    )

    env = marching_cubes_to_mesh(filled, origin, pitch)
    print(f"[Envelope] marching cubes mesh faces={len(env.faces)} verts={len(env.vertices)} watertight={env.is_watertight} vol={env.volume:g}")

    env = remove_small_components(env, keep_largest=args.keep_largest)
    env = clean_mesh(env, smooth_iters=args.smooth_iters)
    # Ensure positive orientation if possible.
    if env.is_watertight and env.volume < 0:
        env.invert()

    out_stl = args.outdir / args.output_name
    env.export(out_stl)

    meta = {
        "manifest": str(args.manifest),
        "sources": sources,
        "voxel_um": args.voxel_um,
        "um_per_unit": args.um_per_unit,
        "pitch_model_units": pitch,
        "dilation_iters": args.dilation_iters,
        "closing_iters": args.closing_iters,
        "smooth_iters": args.smooth_iters,
        "keep_largest": args.keep_largest,
        "output_stl": str(out_stl),
        "output_faces": int(len(env.faces)),
        "output_vertices": int(len(env.vertices)),
        "output_watertight": bool(env.is_watertight),
        "output_volume": float(env.volume),
        "output_bounds_min": env.bounds[0].tolist(),
        "output_bounds_max": env.bounds[1].tolist(),
        "output_extents": env.extents.tolist(),
        "filled_matrix_shape": list(map(int, filled.shape)),
        "filled_voxels": int(filled.sum()),
    }
    (args.outdir / "whole_body_envelope_meta.json").write_text(json.dumps(meta, indent=2))

    print(f"[Envelope] wrote {out_stl}")
    print(f"[Envelope] output watertight={env.is_watertight} volume={env.volume:g} bounds={env.bounds}")
    print(f"[Envelope] wrote {args.outdir / 'whole_body_envelope_meta.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
