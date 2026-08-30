#!/usr/bin/env python3
"""
cap_openworm_body_envelope_tips.py

Post-process a whole_body_envelope.stl to remove long needle-like terminal
spikes and replace them with clean capped ends.

This is intended for the surface-offset envelope workflow where the main body
looks good but MeshFix/outer-surface extraction leaves a sharp artificial tail
or head spike.

It does NOT voxelize the final geometry. It uses plane cuts + caps on the STL.

Dependencies:
    conda install -c conda-forge trimesh numpy pandas scipy shapely networkx pymeshfix
or:
    python -m pip install trimesh numpy scipy shapely networkx pymeshfix

Example:
    python cap_openworm_body_envelope_tips.py \
      --input-stl /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/body_envelope_surface_offset_tuned_tail/whole_body_envelope.stl \
      --outdir /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/body_envelope_surface_offset_tuned_tail_capped \
      --axis y \
      --cap-high auto \
      --cap-low none \
      --min-radius-um 8 \
      --smooth-iters 3

If auto cuts too much or too little, manually specify:
    --cap-high 4.10
or disable:
    --cap-high none
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import trimesh

try:
    import pymeshfix
except Exception:
    pymeshfix = None

AXIS_INDEX = {"x": 0, "y": 1, "z": 2}


def clean_mesh_compat(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    try:
        mesh.update_faces(mesh.unique_faces())
    except Exception:
        pass
    try:
        mesh.update_faces(mesh.nondegenerate_faces())
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


def fix_mesh(mesh: trimesh.Trimesh, run_meshfix: bool = True) -> Tuple[trimesh.Trimesh, Dict]:
    meta = {"ran_meshfix": False, "meshfix_error": None}

    mesh = clean_mesh_compat(mesh)

    if run_meshfix and pymeshfix is not None:
        try:
            mf = pymeshfix.MeshFix(np.asarray(mesh.vertices, dtype=np.float64),
                                   np.asarray(mesh.faces, dtype=np.int64),
                                   verbose=False)
            mf.repair(joincomp=True, remove_smallest_components=False)
            verts = np.asarray(getattr(mf, "points", getattr(mf, "v", None)), dtype=np.float64)
            faces = np.asarray(getattr(mf, "faces", getattr(mf, "f", None)), dtype=np.int64)
            if len(verts) and len(faces):
                mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
                meta["ran_meshfix"] = True
        except Exception as e:
            meta["meshfix_error"] = repr(e)

    try:
        trimesh.repair.fix_normals(mesh)
    except Exception:
        pass

    clean_mesh_compat(mesh)
    if mesh.volume < 0:
        mesh.invert()

    return mesh, meta


def smooth_mesh(mesh: trimesh.Trimesh, iterations: int, lamb: float) -> trimesh.Trimesh:
    if iterations <= 0:
        return mesh
    m = mesh.copy()
    try:
        trimesh.smoothing.filter_laplacian(
            m,
            lamb=lamb,
            iterations=iterations,
            implicit_time_integration=False
        )
    except Exception as e:
        print(f"[WARN] smoothing failed: {e!r}")
    return m


def radius_profile(mesh: trimesh.Trimesh, axis_i: int, bins: int, radius_percentile: float) -> Dict:
    v = np.asarray(mesh.vertices)
    a = v[:, axis_i]
    lo, hi = float(a.min()), float(a.max())
    edges = np.linspace(lo, hi, bins + 1)
    centers_axis = 0.5 * (edges[:-1] + edges[1:])

    other = [i for i in range(3) if i != axis_i]
    radii = np.full(bins, np.nan)
    counts = np.zeros(bins, dtype=int)
    centers = np.full((bins, 3), np.nan)

    global_center = np.median(v, axis=0)
    for i in range(bins):
        mask = (a >= edges[i]) & (a < edges[i + 1] if i < bins - 1 else a <= edges[i + 1])
        counts[i] = int(mask.sum())
        if counts[i] < 5:
            continue
        pts = v[mask]
        c = np.median(pts, axis=0)
        centers[i] = c
        r = np.linalg.norm(pts[:, other] - c[other], axis=1)
        radii[i] = np.percentile(r, radius_percentile)

    # Fill NaNs by interpolation so auto detection does not break.
    good = np.isfinite(radii)
    if good.sum() >= 2:
        radii = np.interp(centers_axis, centers_axis[good], radii[good])
    else:
        radii[:] = 0.0

    return {
        "axis_min": lo,
        "axis_max": hi,
        "edges": edges,
        "axis_centers": centers_axis,
        "radii": radii,
        "counts": counts,
    }


def auto_cut(profile: Dict, side: str, threshold_units: float, consecutive_good: int, margin_units: float) -> float | None:
    centers = profile["axis_centers"]
    radii = profile["radii"]

    if side == "high":
        idxs = range(len(centers) - 1, -1, -1)
        # Move inward from high end until radius is stably above threshold.
        for idx in idxs:
            start = max(0, idx - consecutive_good + 1)
            window = radii[start:idx + 1]
            if len(window) >= consecutive_good and np.nanmin(window) >= threshold_units:
                return float(centers[idx] + margin_units)
        return None

    if side == "low":
        for idx in range(len(centers)):
            end = min(len(centers), idx + consecutive_good)
            window = radii[idx:end]
            if len(window) >= consecutive_good and np.nanmin(window) >= threshold_units:
                return float(centers[idx] - margin_units)
        return None

    raise ValueError(side)


def slice_cap(mesh: trimesh.Trimesh, axis_i: int, side: str, cut_value: float) -> trimesh.Trimesh:
    origin = np.zeros(3, dtype=float)
    origin[axis_i] = cut_value

    if side == "high":
        # keep x_axis <= cut_value -> positive side of plane with normal -axis
        normal = np.zeros(3, dtype=float)
        normal[axis_i] = -1.0
    elif side == "low":
        # keep x_axis >= cut_value -> positive side of plane with normal +axis
        normal = np.zeros(3, dtype=float)
        normal[axis_i] = 1.0
    else:
        raise ValueError(side)

    # cap=True requires shapely in many trimesh versions.
    out = trimesh.intersections.slice_mesh_plane(mesh, plane_normal=normal, plane_origin=origin, cap=True)
    if out is None:
        raise RuntimeError(f"slice_mesh_plane returned None for {side} cut={cut_value}")
    if isinstance(out, list):
        out = trimesh.util.concatenate(out)
    out = trimesh.Trimesh(vertices=out.vertices, faces=out.faces, process=True)
    return clean_mesh_compat(out)


def parse_cap_value(value: str) -> str | float:
    s = str(value).strip().lower()
    if s in {"none", "off", "false", "no"}:
        return "none"
    if s in {"auto", "true", "yes"}:
        return "auto"
    return float(value)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-stl", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--axis", choices=["x", "y", "z"], default="y")
    ap.add_argument("--cap-high", default="auto", help="auto, none, or explicit coordinate in STL units")
    ap.add_argument("--cap-low", default="none", help="auto, none, or explicit coordinate in STL units")
    ap.add_argument("--unit-um", type=float, default=100.0, help="microns per STL unit")
    ap.add_argument("--min-radius-um", type=float, default=8.0,
                    help="Auto cap starts after the terminal radius exceeds this value")
    ap.add_argument("--margin-um", type=float, default=2.0,
                    help="Extra length beyond detected radius threshold before cap plane")
    ap.add_argument("--bins", type=int, default=300)
    ap.add_argument("--radius-percentile", type=float, default=90.0)
    ap.add_argument("--consecutive-good", type=int, default=3)
    ap.add_argument("--smooth-iters", type=int, default=3)
    ap.add_argument("--smooth-lambda", type=float, default=0.2)
    ap.add_argument("--no-meshfix", action="store_true")
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    axis_i = AXIS_INDEX[args.axis]

    mesh = trimesh.load_mesh(args.input_stl, force="mesh", process=True)
    if not isinstance(mesh, trimesh.Trimesh):
        raise TypeError(f"Input is not a Trimesh: {type(mesh)}")
    mesh = clean_mesh_compat(mesh)
    print("[cap tips] input:", args.input_stl)
    print("[cap tips] input vertices/faces:", len(mesh.vertices), len(mesh.faces))
    print("[cap tips] input watertight:", mesh.is_watertight, "volume:", mesh.volume, "bounds:", mesh.bounds.tolist())

    profile = radius_profile(mesh, axis_i=axis_i, bins=args.bins, radius_percentile=args.radius_percentile)
    threshold_units = args.min_radius_um / args.unit_um
    margin_units = args.margin_um / args.unit_um

    cap_high = parse_cap_value(args.cap_high)
    cap_low = parse_cap_value(args.cap_low)

    cuts = {}
    if cap_high == "auto":
        cuts["high"] = auto_cut(profile, "high", threshold_units, args.consecutive_good, margin_units)
    elif cap_high != "none":
        cuts["high"] = float(cap_high)

    if cap_low == "auto":
        cuts["low"] = auto_cut(profile, "low", threshold_units, args.consecutive_good, margin_units)
    elif cap_low != "none":
        cuts["low"] = float(cap_low)

    print("[cap tips] proposed cuts:", cuts)

    # Save profile for debugging.
    import pandas as pd
    pd.DataFrame({
        "axis": profile["axis_centers"],
        "radius_units": profile["radii"],
        "radius_um": profile["radii"] * args.unit_um,
        "count": profile["counts"],
    }).to_csv(args.outdir / "radius_profile.csv", index=False)

    mesh.export(args.outdir / "debug_before_cap.stl")

    if cuts.get("low") is not None:
        print("[cap tips] applying low cut:", cuts["low"])
        mesh = slice_cap(mesh, axis_i, "low", cuts["low"])
        mesh.export(args.outdir / "debug_after_low_cap.stl")

    if cuts.get("high") is not None:
        print("[cap tips] applying high cut:", cuts["high"])
        mesh = slice_cap(mesh, axis_i, "high", cuts["high"])
        mesh.export(args.outdir / "debug_after_high_cap.stl")

    mesh = smooth_mesh(mesh, args.smooth_iters, args.smooth_lambda)
    mesh, repair_meta = fix_mesh(mesh, run_meshfix=not args.no_meshfix)
    mesh = smooth_mesh(mesh, max(0, args.smooth_iters // 2), args.smooth_lambda)
    mesh, repair_meta2 = fix_mesh(mesh, run_meshfix=not args.no_meshfix)

    out = args.outdir / "whole_body_envelope_capped.stl"
    mesh.export(out)

    # Also write name expected by downstream steps.
    out2 = args.outdir / "whole_body_envelope.stl"
    mesh.export(out2)

    meta = {
        "input_stl": str(args.input_stl),
        "axis": args.axis,
        "min_radius_um": args.min_radius_um,
        "margin_um": args.margin_um,
        "cuts": cuts,
        "repair_meta": repair_meta,
        "repair_meta2": repair_meta2,
        "output": {
            "stl": str(out2),
            "vertices": int(len(mesh.vertices)),
            "faces": int(len(mesh.faces)),
            "watertight": bool(mesh.is_watertight),
            "volume": float(mesh.volume),
            "bounds": np.asarray(mesh.bounds).tolist(),
            "extents": np.asarray(mesh.extents).tolist(),
        }
    }
    (args.outdir / "cap_tips_meta.json").write_text(json.dumps(meta, indent=2, default=str))

    print("[cap tips] wrote:", out2)
    print("[cap tips] final vertices/faces:", len(mesh.vertices), len(mesh.faces))
    print("[cap tips] final watertight:", mesh.is_watertight, "volume:", mesh.volume, "bounds:", mesh.bounds.tolist())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
