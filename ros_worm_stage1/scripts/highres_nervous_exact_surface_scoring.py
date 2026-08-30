#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import trimesh


def find_xyz_columns(df: pd.DataFrame):
    candidates = [
        (("x_mm", "y_mm", "z_mm"), 1.0, "mm"),
        (("pos_x_mm", "pos_y_mm", "pos_z_mm"), 1.0, "mm"),
        (("x0_mm", "y0_mm", "z0_mm"), 1.0, "mm"),
        (("x_um", "y_um", "z_um"), 1.0e-3, "um"),
        (("pos_x_um", "pos_y_um", "pos_z_um"), 1.0e-3, "um"),
        (("x", "y", "z"), 1.0, "assumed_mm"),
    ]
    for cols, scale, unit in candidates:
        if all(c in df.columns for c in cols):
            return cols, scale, unit
    raise SystemExit("Could not identify position columns. Columns:\n" + "\n".join(df.columns.astype(str)))


def find_energy_column(df: pd.DataFrame):
    for c in ["ekin_keV", "energy_keV", "e_keV", "kinetic_energy_keV"]:
        if c in df.columns:
            return c
    raise SystemExit("Could not identify electron energy column. Columns:\n" + "\n".join(df.columns.astype(str)))


def compute_center_from_actual_stls(manifest: Path) -> np.ndarray:
    df = pd.read_csv(manifest)
    mins, maxs = [], []
    for stl_path in df["stl_path"]:
        m = trimesh.load_mesh(Path(stl_path), force="mesh")
        mins.append(m.bounds[0])
        maxs.append(m.bounds[1])
    return 0.5 * (np.min(np.vstack(mins), axis=0) + np.max(np.vstack(maxs), axis=0))


def write_spectrum(df_near: pd.DataFrame, ecol: str, out_header: Path, out_noheader: Path, bins: int, emax_kev: float | None):
    if len(df_near) == 0:
        spec = pd.DataFrame({"energy_keV": [], "weight": []})
    else:
        emax = float(emax_kev) if emax_kev is not None else max(float(df_near[ecol].max()), 1.0)
        counts, edges = np.histogram(df_near[ecol].to_numpy(float), bins=bins, range=(0.0, emax))
        centers = 0.5 * (edges[:-1] + edges[1:])
        spec = pd.DataFrame({"energy_keV": centers, "weight": counts})
        spec = spec[spec["weight"] > 0].copy()

    spec.to_csv(out_header, index=False)
    spec.to_csv(out_noheader, index=False, header=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secondaries", required=True)
    ap.add_argument("--nervous-stl", required=True)
    ap.add_argument("--placement-manifest", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--mm-per-model-unit", type=float, default=0.1)
    ap.add_argument("--threshold-um", type=float, default=5.0)
    ap.add_argument("--threshold-scan-um", default="0.5,1,2,5,10,25,50")
    ap.add_argument("--bins", type=int, default=120)
    ap.add_argument("--emax-kev", type=float, default=None)
    ap.add_argument("--chunk-size", type=int, default=50000)
    args = ap.parse_args()

    secondaries = Path(args.secondaries)
    nervous_stl = Path(args.nervous_stl)
    placement_manifest = Path(args.placement_manifest)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(secondaries)
    (xcol, ycol, zcol), scale_to_mm, unit = find_xyz_columns(df)
    ecol = find_energy_column(df)

    pts_mm = df[[xcol, ycol, zcol]].to_numpy(float) * scale_to_mm

    center_model = compute_center_from_actual_stls(placement_manifest)

    mesh = trimesh.load_mesh(nervous_stl, force="mesh")
    mesh.vertices = (mesh.vertices - center_model[None, :]) * args.mm_per_model_unit

    print("[INFO] secondaries:", secondaries)
    print("[INFO] nervous STL:", nervous_stl)
    print("[INFO] position columns:", (xcol, ycol, zcol), "unit:", unit, "scale_to_mm:", scale_to_mm)
    print("[INFO] center_model_units:", center_model.tolist())
    print("[INFO] mesh watertight:", mesh.is_watertight, "winding:", mesh.is_winding_consistent)
    print("[INFO] mesh faces:", len(mesh.faces), "verts:", len(mesh.vertices))
    print("[INFO] exact closest-point query in chunks:", args.chunk_size)

    pq = trimesh.proximity.ProximityQuery(mesh)

    n = len(pts_mm)
    closest_all = np.empty_like(pts_mm)
    dist_all = np.empty(n, dtype=float)
    tri_all = np.empty(n, dtype=np.int64)

    for start in range(0, n, args.chunk_size):
        stop = min(start + args.chunk_size, n)
        closest, dist, tri_id = pq.on_surface(pts_mm[start:stop])
        closest_all[start:stop] = closest
        dist_all[start:stop] = dist
        tri_all[start:stop] = tri_id
        print(f"[INFO] processed {stop}/{n}")

    dist_um = dist_all * 1000.0

    df["distance_to_highres_nervous_surface_mm"] = dist_all
    df["distance_to_highres_nervous_surface_um"] = dist_um
    df["closest_nervous_x_mm"] = closest_all[:, 0]
    df["closest_nervous_y_mm"] = closest_all[:, 1]
    df["closest_nervous_z_mm"] = closest_all[:, 2]
    df["closest_nervous_triangle_id"] = tri_all
    df["near_highres_nervous"] = dist_um <= args.threshold_um

    near = df[df["near_highres_nervous"]].copy()

    df.to_csv(outdir / "secondary_electrons_with_exact_nervous_surface_distance.csv", index=False)
    near.to_csv(outdir / "secondary_electrons_near_exact_highres_nervous_surface.csv", index=False)

    write_spectrum(
        near,
        ecol,
        outdir / "electron_spectrum_near_exact_highres_nervous_surface_with_header.csv",
        outdir / "electron_spectrum_near_exact_highres_nervous_surface.csv",
        args.bins,
        args.emax_kev,
    )

    scan_rows = []
    for um in [float(x) for x in args.threshold_scan_um.split(",") if x.strip()]:
        mask = dist_um <= um
        sub = df[mask]
        scan_rows.append({
            "threshold_um": um,
            "n_secondaries_near": int(mask.sum()),
            "fraction_near": float(mask.mean()) if n else 0.0,
            "mean_energy_keV_near": float(sub[ecol].mean()) if len(sub) else np.nan,
            "median_energy_keV_near": float(sub[ecol].median()) if len(sub) else np.nan,
        })

    scan = pd.DataFrame(scan_rows)
    scan.to_csv(outdir / "exact_nervous_surface_threshold_scan.csv", index=False)

    summary = {
        "method": "exact closest point on high-resolution nervous STL triangle surface",
        "interpretation": "near_highres_nervous means point lies inside an implicit surface shell of radius threshold_um; this is not a closed-volume inside test",
        "secondaries_csv": str(secondaries),
        "nervous_stl": str(nervous_stl),
        "placement_manifest": str(placement_manifest),
        "mm_per_model_unit": args.mm_per_model_unit,
        "global_center_model_units": center_model.tolist(),
        "position_columns": [xcol, ycol, zcol],
        "position_unit_detected": unit,
        "position_scale_to_mm": scale_to_mm,
        "energy_column": ecol,
        "n_input_secondaries": int(n),
        "threshold_um_primary": args.threshold_um,
        "n_near_primary": int(len(near)),
        "fraction_near_primary": float(len(near) / n) if n else 0.0,
        "distance_um_min": float(np.min(dist_um)) if n else None,
        "distance_um_p05": float(np.percentile(dist_um, 5)) if n else None,
        "distance_um_p25": float(np.percentile(dist_um, 25)) if n else None,
        "distance_um_median": float(np.median(dist_um)) if n else None,
        "distance_um_p75": float(np.percentile(dist_um, 75)) if n else None,
        "distance_um_p95": float(np.percentile(dist_um, 95)) if n else None,
        "distance_um_max": float(np.max(dist_um)) if n else None,
        "secondary_bounds_mm_min": pts_mm.min(axis=0).tolist() if n else None,
        "secondary_bounds_mm_max": pts_mm.max(axis=0).tolist() if n else None,
        "nervous_mesh_bounds_mm_min": mesh.bounds[0].tolist(),
        "nervous_mesh_bounds_mm_max": mesh.bounds[1].tolist(),
    }

    (outdir / "exact_nervous_surface_scoring_metadata.json").write_text(json.dumps(summary, indent=2))

    print("[OK] exact nervous surface scoring complete")
    print(json.dumps(summary, indent=2))
    print()
    print("threshold scan:")
    print(scan.to_string(index=False))


if __name__ == "__main__":
    main()
