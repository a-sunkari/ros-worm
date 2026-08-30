#!/usr/bin/env python3
"""
Repair per-object OpenWorm STL files before Geant4 tessellated-solid validation.

This is intentionally stronger than the conservative Blender cleanup pass.
It uses trimesh for deterministic sanitation and optionally pymeshfix for
watertight/orientation repair.

Typical use:
  python repair_openworm_stls_meshfix.py \
    --manifest /home/asunkari/ros-worm/openworm_geometry/object_stls/openworm_object_stl_manifest.csv \
    --outdir /home/asunkari/ros-worm/openworm_geometry/object_stls_repaired_meshfix \
    --meshfix defective \
    --geant4-log /home/asunkari/ros-worm/openworm_geant4_object_validator/build/all_object_overlap_check.log

Install deps in your conda/env if needed:
  python -m pip install numpy pandas trimesh pymeshfix

Notes:
- Coordinates are preserved. No recentering/scaling is done.
- MeshFix can change topology by filling holes and repairing non-manifold edges.
- Run the Geant4 validator after this and compare solid defects before/after.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import numpy as np

try:
    import trimesh
except Exception as e:
    print("[FATAL] trimesh is required. Install with: python -m pip install trimesh", file=sys.stderr)
    raise

try:
    import pymeshfix  # type: ignore
    HAVE_MESHFIX = True
except Exception:
    HAVE_MESHFIX = False


NAME_COL_CANDIDATES = ["object_name", "name", "object", "blender_name", "Object", "Name"]
PATH_COL_CANDIDATES = ["stl_path", "path", "filepath", "file", "filename", "stl", "STL"]


@dataclass
class MeshStats:
    name: str
    input_path: str
    output_path: str
    status: str
    used_meshfix: bool
    error: str
    vertices_before: int
    faces_before: int
    watertight_before: bool
    winding_before: bool
    euler_before: Optional[int]
    volume_before: Optional[float]
    components_before: Optional[int]
    degenerate_removed: int
    tiny_components_removed: int
    vertices_after: int
    faces_after: int
    watertight_after: bool
    winding_after: bool
    euler_after: Optional[int]
    volume_after: Optional[float]
    components_after: Optional[int]


def clean_name_from_geant4_solid(s: str) -> str:
    # Geant4 names are like ow_AVAL_solid or ow_mu_bod_DL2_solid
    s = s.strip()
    if s.startswith("ow_"):
        s = s[3:]
    if s.endswith("_solid"):
        s = s[:-6]
    if s.endswith("_phys"):
        s = s[:-5]
    return s


def parse_defective_names(geant4_log: Optional[Path]) -> Set[str]:
    names: Set[str] = set()
    if not geant4_log:
        return names
    text = geant4_log.read_text(errors="replace")
    for m in re.finditer(r"Defects in solid:\s+(\S+)", text):
        names.add(clean_name_from_geant4_solid(m.group(1)))
    # also catch small/narrow facet blocks if object names are nearby is hard; not needed.
    return names


def detect_columns(fieldnames: Sequence[str]) -> Tuple[str, str]:
    name_col = next((c for c in NAME_COL_CANDIDATES if c in fieldnames), None)
    path_col = next((c for c in PATH_COL_CANDIDATES if c in fieldnames), None)
    if name_col is None:
        raise RuntimeError(f"Could not find object-name column. Columns: {fieldnames}")
    if path_col is None:
        raise RuntimeError(f"Could not find STL path column. Columns: {fieldnames}")
    return name_col, path_col


def resolve_stl_path(raw: str, manifest_path: Path) -> Path:
    p = Path(raw).expanduser()
    if p.is_absolute():
        return p
    # Try relative to manifest dir first, then manifest_dir/stl
    c1 = manifest_path.parent / p
    if c1.exists():
        return c1
    c2 = manifest_path.parent / "stl" / p.name
    if c2.exists():
        return c2
    return c1


def read_manifest(path: Path) -> Tuple[List[Dict[str, str]], str, str]:
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise RuntimeError("Manifest has no header")
        name_col, path_col = detect_columns(reader.fieldnames)
        return list(reader), name_col, path_col


def load_as_mesh(path: Path):
    loaded = trimesh.load_mesh(str(path), process=False)
    if isinstance(loaded, trimesh.Scene):
        geoms = [g for g in loaded.geometry.values()]
        if not geoms:
            raise RuntimeError("Loaded empty scene")
        mesh = trimesh.util.concatenate(tuple(geoms))
    else:
        mesh = loaded
    if mesh.vertices is None or mesh.faces is None or len(mesh.faces) == 0:
        raise RuntimeError("Loaded empty mesh")
    return mesh


def safe_bool(x):
    try:
        return bool(x)
    except Exception:
        return False


def safe_volume(mesh) -> Optional[float]:
    try:
        v = float(mesh.volume)
        if not np.isfinite(v):
            return None
        return v
    except Exception:
        return None


def safe_components(mesh) -> Optional[int]:
    try:
        return int(len(mesh.split(only_watertight=False)))
    except Exception:
        return None


def remove_degenerate_faces_by_area(mesh, min_area: float) -> int:
    if len(mesh.faces) == 0:
        return 0
    areas = mesh.area_faces
    keep = np.isfinite(areas) & (areas > min_area)
    removed = int(np.count_nonzero(~keep))
    if removed:
        mesh.update_faces(keep)
        mesh.remove_unreferenced_vertices()
    return removed


def remove_tiny_components(mesh, min_faces: int) -> Tuple[object, int]:
    if min_faces <= 0:
        return mesh, 0
    parts = mesh.split(only_watertight=False)
    if len(parts) <= 1:
        return mesh, 0
    keep = [p for p in parts if len(p.faces) >= min_faces]
    removed = len(parts) - len(keep)
    if not keep:
        # Keep largest to avoid nuking the object.
        keep = [max(parts, key=lambda p: len(p.faces))]
        removed = len(parts) - 1
    return trimesh.util.concatenate(tuple(keep)), removed


def basic_repair(mesh, merge_digits: int, min_face_area: float, min_component_faces: int):
    # Trimesh API changed across versions; use guarded calls.
    for fn in ["remove_duplicate_faces", "remove_degenerate_faces"]:
        try:
            getattr(mesh, fn)()
        except Exception:
            pass
    try:
        mesh.remove_unreferenced_vertices()
    except Exception:
        pass
    try:
        mesh.merge_vertices(digits_vertex=merge_digits)
    except TypeError:
        try:
            mesh.merge_vertices()
        except Exception:
            pass
    except Exception:
        pass

    deg_removed = remove_degenerate_faces_by_area(mesh, min_face_area)
    mesh, tiny_removed = remove_tiny_components(mesh, min_component_faces)

    # Fix normals/winding. multibody=True avoids forcing disconnected components into one winding basis.
    try:
        trimesh.repair.fix_normals(mesh, multibody=True)
    except Exception:
        try:
            mesh.fix_normals()
        except Exception:
            pass

    # If watertight and negative volume, invert winding globally.
    vol = safe_volume(mesh)
    if vol is not None and vol < 0:
        try:
            mesh.invert()
        except Exception:
            pass

    return mesh, deg_removed, tiny_removed


def meshfix_repair(mesh, joincomp: bool, remove_smallest_components: bool):
    if not HAVE_MESHFIX:
        raise RuntimeError("pymeshfix is not installed")
    verts = np.asarray(mesh.vertices, dtype=np.float64)
    faces = np.asarray(mesh.faces, dtype=np.int64)

    # PyMeshFix 0.18.x API:
    #   MeshFix.repair(joincomp=False, remove_smallest_components=True)
    # There is no repair(verbose=...) keyword; verbosity belongs to the
    # MeshFix constructor in current documentation. Keep remove_smallest_components
    # under CLI control because removing smaller connected components can delete
    # anatomically meaningful branches/cell pieces.
    mf = pymeshfix.MeshFix(verts, faces, verbose=False)
    mf.repair(joincomp=joincomp, remove_smallest_components=remove_smallest_components)

    # Current PyMeshFix exposes repaired arrays as .points/.faces. Older examples
    # sometimes use .v/.f, so support both.
    v_raw = getattr(mf, "points", None)
    f_raw = getattr(mf, "faces", None)
    if v_raw is None:
        v_raw = getattr(mf, "v", None)
    if f_raw is None:
        f_raw = getattr(mf, "f", None)
    if v_raw is None or f_raw is None:
        raise RuntimeError("MeshFix did not expose repaired points/faces")

    v = np.asarray(v_raw, dtype=np.float64)
    f = np.asarray(f_raw, dtype=np.int64)
    if len(v) == 0 or len(f) == 0:
        raise RuntimeError("MeshFix returned empty mesh")
    repaired = trimesh.Trimesh(vertices=v, faces=f, process=False)
    try:
        trimesh.repair.fix_normals(repaired, multibody=True)
    except Exception:
        pass
    vol = safe_volume(repaired)
    if vol is not None and vol < 0:
        repaired.invert()
    return repaired


def should_meshfix(mode: str, name: str, defective_names: Set[str], mesh) -> bool:
    if mode == "never":
        return False
    if mode == "all":
        return True
    if mode == "defective":
        return name in defective_names
    if mode == "if-needed":
        return (not safe_bool(mesh.is_watertight)) or (not safe_bool(mesh.is_winding_consistent)) or ((safe_volume(mesh) or 0) < 0)
    raise ValueError(mode)


def export_mesh(mesh, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(str(out), file_type="stl")


def process_one(row: Dict[str, str], name_col: str, path_col: str, manifest_path: Path, outdir: Path,
                args, defective_names: Set[str]) -> Tuple[MeshStats, Dict[str, str]]:
    name = row[name_col]
    in_path = resolve_stl_path(row[path_col], manifest_path)
    out_path = outdir / "stl" / f"{name}.stl"

    stats = MeshStats(
        name=name, input_path=str(in_path), output_path=str(out_path), status="", used_meshfix=False, error="",
        vertices_before=0, faces_before=0, watertight_before=False, winding_before=False,
        euler_before=None, volume_before=None, components_before=None,
        degenerate_removed=0, tiny_components_removed=0,
        vertices_after=0, faces_after=0, watertight_after=False, winding_after=False,
        euler_after=None, volume_after=None, components_after=None,
    )
    out_row = dict(row)
    try:
        mesh = load_as_mesh(in_path)
        stats.vertices_before = int(len(mesh.vertices))
        stats.faces_before = int(len(mesh.faces))
        stats.watertight_before = safe_bool(mesh.is_watertight)
        stats.winding_before = safe_bool(mesh.is_winding_consistent)
        try:
            stats.euler_before = int(mesh.euler_number)
        except Exception:
            pass
        stats.volume_before = safe_volume(mesh)
        stats.components_before = safe_components(mesh)

        mesh, deg_removed, tiny_removed = basic_repair(
            mesh,
            merge_digits=args.merge_digits,
            min_face_area=args.min_face_area,
            min_component_faces=args.min_component_faces,
        )
        stats.degenerate_removed = deg_removed
        stats.tiny_components_removed = tiny_removed

        if should_meshfix(args.meshfix, name, defective_names, mesh):
            try:
                mesh = meshfix_repair(mesh, joincomp=args.meshfix_join, remove_smallest_components=args.meshfix_remove_smallest)
                stats.used_meshfix = True
                # run basic cleanup once more after MeshFix
                mesh, d2, t2 = basic_repair(
                    mesh,
                    merge_digits=args.merge_digits,
                    min_face_area=args.min_face_area,
                    min_component_faces=args.min_component_faces,
                )
                stats.degenerate_removed += d2
                stats.tiny_components_removed += t2
            except Exception as e:
                if args.meshfix_required:
                    raise
                print(f"[WARN] {name}: MeshFix failed, using basic repair only: {repr(e)}")

        stats.vertices_after = int(len(mesh.vertices))
        stats.faces_after = int(len(mesh.faces))
        stats.watertight_after = safe_bool(mesh.is_watertight)
        stats.winding_after = safe_bool(mesh.is_winding_consistent)
        try:
            stats.euler_after = int(mesh.euler_number)
        except Exception:
            pass
        stats.volume_after = safe_volume(mesh)
        stats.components_after = safe_components(mesh)

        if stats.faces_after == 0:
            raise RuntimeError("No faces after repair")

        export_mesh(mesh, out_path)
        out_row[path_col] = str(out_path)
        # Add useful columns if not present.
        out_row["stl_path"] = str(out_path)
        out_row["repair_used_meshfix"] = str(stats.used_meshfix)
        out_row["repair_watertight_after"] = str(stats.watertight_after)
        out_row["repair_winding_after"] = str(stats.winding_after)
        out_row["repair_faces_after"] = str(stats.faces_after)
        stats.status = "ok"
    except Exception as e:
        stats.status = "error"
        stats.error = repr(e)
        if args.copy_on_error and in_path.exists():
            out_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(in_path, out_path)
            out_row[path_col] = str(out_path)
            out_row["stl_path"] = str(out_path)
        print(f"[ERROR] {name}: {repr(e)}")
    return stats, out_row


def write_manifest(rows: List[Dict[str, str]], out_path: Path):
    # preserve all keys encountered
    keys: List[str] = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                keys.append(k); seen.add(k)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--geant4-log", type=Path, default=None,
                    help="Optional validator log. With --meshfix defective, only objects with Geant4 solid defects get MeshFix.")
    ap.add_argument("--meshfix", choices=["never", "defective", "if-needed", "all"], default="defective")
    ap.add_argument("--meshfix-required", action="store_true")
    ap.add_argument("--meshfix-join", action="store_true", default=False,
                    help="Allow MeshFix to join nearby components. Default false preserves components better.")
    ap.add_argument("--meshfix-remove-smallest", action="store_true", default=False,
                    help="Allow MeshFix to remove smaller components. Default false preserves anatomy better.")
    ap.add_argument("--merge-digits", type=int, default=8,
                    help="trimesh vertex merge precision. 8 is conservative; 6 is stronger.")
    ap.add_argument("--min-face-area", type=float, default=1e-14,
                    help="Remove triangles with area <= this in STL/model units^2.")
    ap.add_argument("--min-component-faces", type=int, default=0,
                    help="Remove disconnected components with fewer than N faces. 0 disables.")
    ap.add_argument("--only-defective", action="store_true",
                    help="Only process objects named in --geant4-log; copy others unchanged.")
    ap.add_argument("--copy-on-error", action="store_true", default=True)
    args = ap.parse_args(argv)

    print(f"[OpenWorm MeshFix] trimesh version: {getattr(trimesh, '__version__', 'unknown')}")
    print(f"[OpenWorm MeshFix] pymeshfix available: {HAVE_MESHFIX}")
    if args.meshfix != "never" and not HAVE_MESHFIX:
        print("[WARN] pymeshfix is not installed; MeshFix repair will be skipped/fail. Install: python -m pip install pymeshfix")

    manifest_path = args.manifest.expanduser().resolve()
    outdir = args.outdir.expanduser().resolve()
    rows, name_col, path_col = read_manifest(manifest_path)
    defective_names = parse_defective_names(args.geant4_log.expanduser().resolve() if args.geant4_log else None)
    print(f"[OpenWorm MeshFix] rows: {len(rows)}")
    print(f"[OpenWorm MeshFix] name_col={name_col} path_col={path_col}")
    print(f"[OpenWorm MeshFix] defective names from Geant4 log: {len(defective_names)}")

    out_rows: List[Dict[str, str]] = []
    stats: List[MeshStats] = []

    for i, row in enumerate(rows, 1):
        name = row[name_col]
        if args.only_defective and name not in defective_names:
            # Copy unchanged so the output manifest is complete.
            in_path = resolve_stl_path(row[path_col], manifest_path)
            out_path = outdir / "stl" / f"{name}.stl"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if in_path.exists():
                shutil.copy2(in_path, out_path)
            out_row = dict(row)
            out_row[path_col] = str(out_path)
            out_row["stl_path"] = str(out_path)
            out_row["repair_used_meshfix"] = "False"
            out_rows.append(out_row)
            continue

        st, out_row = process_one(row, name_col, path_col, manifest_path, outdir, args, defective_names)
        stats.append(st)
        out_rows.append(out_row)
        if i % 25 == 0 or st.status != "ok":
            print(f"[OpenWorm MeshFix] {i}/{len(rows)} {name}: {st.status}, faces {st.faces_before}->{st.faces_after}, watertight {st.watertight_before}->{st.watertight_after}, meshfix={st.used_meshfix}")

    cleaned_manifest = outdir / "openworm_object_stl_manifest_repaired.csv"
    write_manifest(out_rows, cleaned_manifest)

    stats_path = outdir / "repair_stats.csv"
    with stats_path.open("w", newline="") as f:
        keys = list(asdict(stats[0]).keys()) if stats else list(MeshStats.__annotations__.keys())
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for st in stats:
            w.writerow(asdict(st))

    summary = {
        "input_manifest": str(manifest_path),
        "output_manifest": str(cleaned_manifest),
        "outdir": str(outdir),
        "total_rows": len(rows),
        "processed_count": len(stats),
        "ok_count": sum(1 for s in stats if s.status == "ok"),
        "error_count": sum(1 for s in stats if s.status != "ok"),
        "meshfix_used_count": sum(1 for s in stats if s.used_meshfix),
        "watertight_before_count": sum(1 for s in stats if s.watertight_before),
        "watertight_after_count": sum(1 for s in stats if s.watertight_after),
        "winding_before_count": sum(1 for s in stats if s.winding_before),
        "winding_after_count": sum(1 for s in stats if s.winding_after),
        "faces_before_total": sum(s.faces_before for s in stats),
        "faces_after_total": sum(s.faces_after for s in stats),
        "degenerate_removed_total": sum(s.degenerate_removed for s in stats),
        "tiny_components_removed_total": sum(s.tiny_components_removed for s in stats),
        "pymeshfix_available": HAVE_MESHFIX,
        "args": vars(args),
    }
    (outdir / "repair_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"[OpenWorm MeshFix] wrote: {cleaned_manifest}")
    print(f"[OpenWorm MeshFix] wrote: {stats_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
