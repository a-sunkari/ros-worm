#!/usr/bin/env python3
"""
derive_openworm_body_envelope_surface_offset.py

Build a smooth filled whole-body parent envelope from the OpenWorm Cuticle/hyp7
shell mesh without turning the final geometry into a voxel phantom.

Purpose:
    The OpenWorm "Cuticle" is visually the outer shell but is not a filled
    whole-body parent volume. This script extracts the exterior-facing surface,
    optionally offsets it slightly outward, repairs/fills it into a watertight
    STL, and writes whole_body_envelope.stl for use as the Geant4 parent body.

Core idea:
    - Load one or more source shell STLs from the repaired object manifest.
    - Estimate the worm centerline along the long axis.
    - For each triangle, compare its normal to the local radial direction
      away from the centerline.
    - Keep exterior-facing triangles plus end-cap candidates.
    - Optionally offset along vertex normals.
    - Run PyMeshFix to close/repair the resulting exterior surface.
    - Export a smooth filled STL mesh.

Dependencies:
    python -m pip install numpy pandas trimesh scipy pymeshfix
    or conda install -c conda-forge numpy pandas trimesh scipy pymeshfix networkx

Example:
    python derive_openworm_body_envelope_surface_offset.py \
      --manifest /home/asunkari/ros-worm/openworm_geometry/object_stls_repaired_meshfix_defective/openworm_object_stl_manifest_repaired.csv \
      --outdir /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/body_envelope_surface_offset \
      --sources Cuticle \
      --axis y \
      --bins 240 \
      --outer-dot-threshold 0.05 \
      --offset-um 0.5 \
      --smooth-iters 3
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd
import trimesh

try:
    from scipy.ndimage import gaussian_filter1d
except Exception:
    gaussian_filter1d = None

try:
    import pymeshfix
except Exception:
    pymeshfix = None


AXIS_INDEX = {"x": 0, "y": 1, "z": 2}

def clean_mesh_compat(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """
    Trimesh 4.x removed some old in-place cleanup methods like
    remove_duplicate_faces/remove_degenerate_faces. Use the new update_faces
    API when available, with fallbacks for older versions.
    """
    # Remove duplicate faces
    try:
        mesh.update_faces(mesh.unique_faces())
    except Exception:
        try:
            mesh.remove_duplicate_faces()
        except Exception:
            pass

    # Remove degenerate / zero-area faces
    try:
        mesh.update_faces(mesh.nondegenerate_faces())
    except Exception:
        try:
            mesh.remove_degenerate_faces()
        except Exception:
            pass

    try:
        mesh.remove_unreferenced_vertices()
    except Exception:
        pass

    try:
        mesh.process(validate=True)
    except Exception:
        pass

    return mesh



def require_columns(df: pd.DataFrame) -> Tuple[str, str]:
    name_candidates = ["object_name", "name", "object", "Object"]
    path_candidates = ["stl_path", "path", "filepath", "file_path", "stl"]

    name_col = next((c for c in name_candidates if c in df.columns), None)
    path_col = next((c for c in path_candidates if c in df.columns), None)

    if name_col is None:
        raise ValueError(f"Could not find object-name column in manifest columns={list(df.columns)}")
    if path_col is None:
        raise ValueError(f"Could not find STL-path column in manifest columns={list(df.columns)}")
    return name_col, path_col


def load_sources(manifest: Path, sources: Sequence[str]) -> Tuple[trimesh.Trimesh, List[Dict]]:
    df = pd.read_csv(manifest)
    name_col, path_col = require_columns(df)

    selected = []
    source_set = {s.strip() for s in sources if s.strip()}
    for _, row in df.iterrows():
        name = str(row[name_col])
        if name in source_set:
            selected.append((name, Path(str(row[path_col]))))

    missing = sorted(source_set - {n for n, _ in selected})
    if missing:
        raise FileNotFoundError(f"Source objects not found in manifest: {missing}")

    meshes = []
    info = []
    for name, path in selected:
        if not path.exists():
            raise FileNotFoundError(f"{name}: STL path does not exist: {path}")
        m = trimesh.load_mesh(path, force="mesh", process=True)
        if not isinstance(m, trimesh.Trimesh):
            raise TypeError(f"{name}: loaded object is not a Trimesh: {type(m)}")
        # Do light cleanup but do not repair too aggressively here.
        clean_mesh_compat(m)
        meshes.append(m)
        info.append({
            "name": name,
            "path": str(path),
            "vertices": int(len(m.vertices)),
            "faces": int(len(m.faces)),
            "watertight": bool(m.is_watertight),
            "volume": float(m.volume),
            "bounds": np.asarray(m.bounds).tolist(),
            "extents": np.asarray(m.extents).tolist(),
        })

    combined = trimesh.util.concatenate(meshes)
    combined.process(validate=True)
    return combined, info


def estimate_centerline(vertices: np.ndarray, axis_i: int, bins: int, smooth_sigma: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Estimate a centerline using median transverse coordinates in bins along the long axis.
    This is not used to reconstruct the body; it is only used to decide which shell
    faces are exterior-facing.
    """
    coord = vertices[:, axis_i]
    lo, hi = float(coord.min()), float(coord.max())
    edges = np.linspace(lo, hi, bins + 1)
    centers_axis = 0.5 * (edges[:-1] + edges[1:])

    centerline = np.zeros((bins, 3), dtype=float)
    counts = np.zeros(bins, dtype=int)

    global_med = np.median(vertices, axis=0)
    for i in range(bins):
        mask = (coord >= edges[i]) & (coord < edges[i + 1] if i < bins - 1 else coord <= edges[i + 1])
        counts[i] = int(mask.sum())
        if counts[i] >= 10:
            centerline[i] = np.median(vertices[mask], axis=0)
        else:
            centerline[i] = global_med
        centerline[i, axis_i] = centers_axis[i]

    # Fill low-count bins by interpolation from good bins
    good = counts >= 10
    if good.sum() >= 2:
        for dim in range(3):
            centerline[:, dim] = np.interp(centers_axis, centers_axis[good], centerline[good, dim])
        centerline[:, axis_i] = centers_axis

    # Smooth transverse coordinates only
    if gaussian_filter1d is not None and smooth_sigma > 0:
        for dim in range(3):
            if dim == axis_i:
                continue
            centerline[:, dim] = gaussian_filter1d(centerline[:, dim], sigma=smooth_sigma, mode="nearest")

    return centers_axis, centerline


def interpolate_centerline(query_axis: np.ndarray, centers_axis: np.ndarray, centerline: np.ndarray) -> np.ndarray:
    out = np.zeros((len(query_axis), 3), dtype=float)
    for dim in range(3):
        out[:, dim] = np.interp(query_axis, centers_axis, centerline[:, dim])
    return out


def select_outer_faces(
    mesh: trimesh.Trimesh,
    axis_i: int,
    centers_axis: np.ndarray,
    centerline: np.ndarray,
    outer_dot_threshold: float,
    end_fraction: float,
    end_normal_threshold: float,
) -> Tuple[np.ndarray, Dict]:
    mesh.rezero()  # no-op-ish center? Actually shifts to positive; avoid? We'll not call this. 
    raise RuntimeError("internal placeholder should not be called")


def select_outer_faces_no_rezero(
    mesh: trimesh.Trimesh,
    axis_i: int,
    centers_axis: np.ndarray,
    centerline: np.ndarray,
    outer_dot_threshold: float,
    end_fraction: float,
    end_normal_threshold: float,
) -> Tuple[np.ndarray, Dict]:
    centers = mesh.triangles_center
    normals = mesh.face_normals
    axis_coord = centers[:, axis_i]

    cl = interpolate_centerline(axis_coord, centers_axis, centerline)
    radial = centers - cl
    # For sidewall classification, ignore longitudinal component.
    radial[:, axis_i] = 0.0

    radial_norm = np.linalg.norm(radial, axis=1)
    good_rad = radial_norm > 1e-12
    radial_unit = np.zeros_like(radial)
    radial_unit[good_rad] = radial[good_rad] / radial_norm[good_rad, None]

    dot = np.einsum("ij,ij->i", normals, radial_unit)
    side_keep = good_rad & (dot >= outer_dot_threshold)

    # Keep end-cap-ish faces near the extreme ends whose normals point outward along the axis.
    lo, hi = float(mesh.bounds[0, axis_i]), float(mesh.bounds[1, axis_i])
    span = hi - lo
    end_pad = max(span * end_fraction, 1e-9)
    n_axis = normals[:, axis_i]
    low_end_keep = (axis_coord <= lo + end_pad) & (n_axis <= -end_normal_threshold)
    high_end_keep = (axis_coord >= hi - end_pad) & (n_axis >= end_normal_threshold)
    keep = side_keep | low_end_keep | high_end_keep

    meta = {
        "faces_total": int(len(mesh.faces)),
        "faces_kept": int(keep.sum()),
        "faces_side_kept": int(side_keep.sum()),
        "faces_low_end_kept": int(low_end_keep.sum()),
        "faces_high_end_kept": int(high_end_keep.sum()),
        "outer_dot_threshold": float(outer_dot_threshold),
        "end_fraction": float(end_fraction),
        "end_normal_threshold": float(end_normal_threshold),
        "dot_min": float(np.nanmin(dot)),
        "dot_median": float(np.nanmedian(dot)),
        "dot_max": float(np.nanmax(dot)),
    }
    return keep, meta


def subset_mesh_by_faces(mesh: trimesh.Trimesh, keep_faces: np.ndarray) -> trimesh.Trimesh:
    faces = mesh.faces[keep_faces]
    used = np.unique(faces.reshape(-1))
    remap = -np.ones(len(mesh.vertices), dtype=np.int64)
    remap[used] = np.arange(len(used))
    new_vertices = mesh.vertices[used]
    new_faces = remap[faces]
    out = trimesh.Trimesh(vertices=new_vertices, faces=new_faces, process=True)
    clean_mesh_compat(out)
    return out


def offset_mesh_along_normals(mesh: trimesh.Trimesh, offset_units: float) -> trimesh.Trimesh:
    if abs(offset_units) < 1e-15:
        return mesh.copy()
    m = mesh.copy()
    # trimesh vertex_normals are area-weighted. For open surfaces this still works for outward-ish offset.
    normals = m.vertex_normals
    m.vertices = m.vertices + offset_units * normals
    return m


def smooth_mesh(mesh: trimesh.Trimesh, iterations: int, lamb: float) -> trimesh.Trimesh:
    if iterations <= 0:
        return mesh
    m = mesh.copy()
    try:
        trimesh.smoothing.filter_laplacian(m, lamb=lamb, iterations=iterations, implicit_time_integration=False)
    except Exception as e:
        print(f"[WARN] smoothing failed: {e!r}")
    return m


def meshfix_repair(mesh: trimesh.Trimesh, joincomp: bool, remove_smallest_components: bool) -> Tuple[trimesh.Trimesh, Dict]:
    meta = {
        "pymeshfix_available": pymeshfix is not None,
        "ran_meshfix": False,
        "meshfix_error": None,
    }
    if pymeshfix is None:
        return mesh, meta

    try:
        verts = np.asarray(mesh.vertices, dtype=np.float64)
        faces = np.asarray(mesh.faces, dtype=np.int64)
        mf = pymeshfix.MeshFix(verts, faces, verbose=False)
        mf.repair(joincomp=joincomp, remove_smallest_components=remove_smallest_components)
        rv = np.asarray(getattr(mf, "points", getattr(mf, "v", None)), dtype=np.float64)
        rf = np.asarray(getattr(mf, "faces", getattr(mf, "f", None)), dtype=np.int64)
        if rv is None or rf is None or len(rv) == 0 or len(rf) == 0:
            raise RuntimeError("MeshFix returned empty points/faces")
        repaired = trimesh.Trimesh(vertices=rv, faces=rf, process=True)
        clean_mesh_compat(repaired)
        meta["ran_meshfix"] = True
        return repaired, meta
    except Exception as e:
        meta["meshfix_error"] = repr(e)
        print(f"[WARN] MeshFix failed, using un-meshfixed exterior surface: {e!r}")
        return mesh, meta


def safe_json(obj):
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--sources", default="Cuticle", help="Comma-separated source object names. Default: Cuticle")
    ap.add_argument("--axis", choices=["x", "y", "z"], default="y", help="Approximate worm long axis in STL coordinates")
    ap.add_argument("--bins", type=int, default=240, help="Centerline bins along long axis")
    ap.add_argument("--centerline-smooth-sigma", type=float, default=3.0)
    ap.add_argument("--outer-dot-threshold", type=float, default=0.05,
                    help="Keep sidewall faces if dot(face_normal, local_radial_dir) >= threshold")
    ap.add_argument("--end-fraction", type=float, default=0.025,
                    help="Fraction of length near each end to keep end-cap-like faces")
    ap.add_argument("--end-normal-threshold", type=float, default=0.25)
    ap.add_argument("--offset-um", type=float, default=0.5,
                    help="Offset exterior surface outward by this many microns. Units assume 1 STL unit = 100 um.")
    ap.add_argument("--unit-um", type=float, default=100.0,
                    help="Microns per STL/Blender unit. Existing pipeline uses 100 um/unit.")
    ap.add_argument("--smooth-iters-before", type=int, default=0)
    ap.add_argument("--smooth-iters-after", type=int, default=3)
    ap.add_argument("--smooth-lambda", type=float, default=0.25)
    ap.add_argument("--meshfix-joincomp", action="store_true", default=True)
    ap.add_argument("--meshfix-remove-smallest", action="store_true", default=False)
    ap.add_argument("--no-meshfix", action="store_true")
    ap.add_argument("--write-debug", action="store_true", default=True)
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    axis_i = AXIS_INDEX[args.axis]

    source_mesh, source_info = load_sources(args.manifest, sources)
    print(f"[Envelope surface-offset] sources={sources}")
    print(f"[Envelope surface-offset] source vertices={len(source_mesh.vertices)} faces={len(source_mesh.faces)}")
    print(f"[Envelope surface-offset] source bounds={source_mesh.bounds.tolist()}")
    print(f"[Envelope surface-offset] source watertight={source_mesh.is_watertight} volume={source_mesh.volume}")

    centers_axis, centerline = estimate_centerline(
        source_mesh.vertices,
        axis_i=axis_i,
        bins=args.bins,
        smooth_sigma=args.centerline_smooth_sigma,
    )

    keep, select_meta = select_outer_faces_no_rezero(
        source_mesh,
        axis_i=axis_i,
        centers_axis=centers_axis,
        centerline=centerline,
        outer_dot_threshold=args.outer_dot_threshold,
        end_fraction=args.end_fraction,
        end_normal_threshold=args.end_normal_threshold,
    )
    print(f"[Envelope surface-offset] kept faces={select_meta['faces_kept']}/{select_meta['faces_total']}")

    exterior = subset_mesh_by_faces(source_mesh, keep)
    print(f"[Envelope surface-offset] exterior candidate faces={len(exterior.faces)} watertight={exterior.is_watertight} volume={exterior.volume}")

    if args.write_debug:
        exterior.export(args.outdir / "debug_exterior_faces_before_offset.stl")

    exterior = smooth_mesh(exterior, args.smooth_iters_before, args.smooth_lambda)

    offset_units = args.offset_um / args.unit_um
    exterior = offset_mesh_along_normals(exterior, offset_units)
    exterior.process(validate=True)
    if args.write_debug:
        exterior.export(args.outdir / "debug_exterior_faces_offset.stl")

    if args.no_meshfix:
        repaired = exterior
        meshfix_meta = {"ran_meshfix": False, "disabled": True}
    else:
        repaired, meshfix_meta = meshfix_repair(
            exterior,
            joincomp=args.meshfix_joincomp,
            remove_smallest_components=args.meshfix_remove_smallest,
        )

    # Smooth after repair, then fix normals.
    repaired = smooth_mesh(repaired, args.smooth_iters_after, args.smooth_lambda)
    try:
        trimesh.repair.fix_normals(repaired)
    except Exception as e:
        print(f"[WARN] final fix_normals failed: {e!r}")

    repaired.process(validate=True)
    if repaired.volume < 0:
        repaired.invert()

    out_stl = args.outdir / "whole_body_envelope.stl"
    repaired.export(out_stl)

    # Write a one-row manifest for validators if desired.
    out_manifest = args.outdir / "whole_body_envelope_manifest.csv"
    pd.DataFrame([{
        "object_name": "WholeBodyEnvelope",
        "stl_path": str(out_stl),
        "role": "whole_body_parent_envelope",
        "source_objects": ",".join(sources),
    }]).to_csv(out_manifest, index=False)

    meta = {
        "method": "surface_offset_outer_face_extraction",
        "sources": sources,
        "source_info": source_info,
        "axis": args.axis,
        "bins": args.bins,
        "centerline_smooth_sigma": args.centerline_smooth_sigma,
        "selection": select_meta,
        "offset_um": args.offset_um,
        "unit_um": args.unit_um,
        "smooth_iters_before": args.smooth_iters_before,
        "smooth_iters_after": args.smooth_iters_after,
        "smooth_lambda": args.smooth_lambda,
        "meshfix": meshfix_meta,
        "output": {
            "stl": str(out_stl),
            "manifest": str(out_manifest),
            "vertices": int(len(repaired.vertices)),
            "faces": int(len(repaired.faces)),
            "watertight": bool(repaired.is_watertight),
            "volume": float(repaired.volume),
            "bounds": np.asarray(repaired.bounds).tolist(),
            "extents": np.asarray(repaired.extents).tolist(),
        },
    }
    (args.outdir / "body_envelope_meta.json").write_text(json.dumps(meta, indent=2, default=safe_json))

    print("[Envelope surface-offset] wrote:", out_stl)
    print("[Envelope surface-offset] final vertices:", len(repaired.vertices), "faces:", len(repaired.faces))
    print("[Envelope surface-offset] final watertight:", repaired.is_watertight, "volume:", repaired.volume)
    print("[Envelope surface-offset] final bounds:", repaired.bounds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
