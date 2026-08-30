#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import trimesh
from scipy.spatial import cKDTree


def find_xyz_columns(df: pd.DataFrame):
    """
    Return (columns, scale_to_mm, unit_label).

    Stage-1 extractor currently writes x_um/y_um/z_um.
    Geant4/nervous-reference geometry below is in mm, so micrometer
    coordinates must be multiplied by 1e-3.
    """
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


def compute_global_center_model_from_manifest(manifest: Path) -> np.ndarray:
    """
    Compute placement center from the actual STL files, not stale manifest
    min/max metadata. This must match the visualization/QC transform.

    We intentionally ignore min_x/max_x columns because earlier manifests
    can retain old bounds after STL paths are swapped.
    """
    df = pd.read_csv(manifest)

    mins, maxs = [], []
    for stl_path in df["stl_path"]:
        m = trimesh.load_mesh(Path(stl_path), force="mesh")
        mins.append(m.bounds[0])
        maxs.append(m.bounds[1])

    global_min = np.min(np.vstack(mins), axis=0)
    global_max = np.max(np.vstack(maxs), axis=0)
    return 0.5 * (global_min + global_max)


def build_nervous_reference_points(mesh: trimesh.Trimesh, sample_points: int, seed: int) -> np.ndarray:
    pts = [np.asarray(mesh.vertices, dtype=np.float64)]

    if sample_points and sample_points > 0:
        rng = np.random.default_rng(seed)
        # trimesh uses np.random global in some versions; seed anyway for reproducibility.
        np.random.seed(seed)
        try:
            samp, _ = trimesh.sample.sample_surface(mesh, sample_points)
            pts.append(np.asarray(samp, dtype=np.float64))
        except Exception as e:
            print("[WARN] surface sampling failed; using vertices only:", repr(e))

    return np.vstack(pts)


def write_spectrum(df_near: pd.DataFrame, ecol: str, out_header: Path, out_noheader: Path, bins: int, emax_keV: float | None):
    if len(df_near) == 0:
        spec = pd.DataFrame({"energy_keV": [], "weight": []})
    else:
        emax = float(emax_keV) if emax_keV is not None else max(float(df_near[ecol].max()), 1.0)
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
    ap.add_argument("--threshold-scan-um", default="1,2,5,10,25,50")
    ap.add_argument("--surface-samples", type=int, default=500000)
    ap.add_argument("--bins", type=int, default=100)
    ap.add_argument("--emax-kev", type=float, default=None)
    ap.add_argument("--seed", type=int, default=12345)
    args = ap.parse_args()

    secondaries = Path(args.secondaries)
    nervous_stl = Path(args.nervous_stl)
    placement_manifest = Path(args.placement_manifest)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(secondaries)
    (xcol, ycol, zcol), position_scale_to_mm, position_unit = find_xyz_columns(df)
    ecol = find_energy_column(df)

    center_model = compute_global_center_model_from_manifest(placement_manifest)
    mesh = trimesh.load_mesh(nervous_stl, force="mesh")

    ref_model = build_nervous_reference_points(mesh, args.surface_samples, args.seed)

    # Geant4 placement transform: model coordinates are centered by global center, then scaled to mm.
    ref_mm = (ref_model - center_model[None, :]) * args.mm_per_model_unit

    tree = cKDTree(ref_mm)

    pts_mm = df[[xcol, ycol, zcol]].to_numpy(dtype=np.float64) * position_scale_to_mm
    dist_mm, nearest_idx = tree.query(pts_mm, k=1, workers=-1)

    df["distance_to_highres_nervous_mm"] = dist_mm
    df["distance_to_highres_nervous_um"] = dist_mm * 1000.0
    df["nearest_highres_nervous_ref_index"] = nearest_idx

    threshold_mm = args.threshold_um * 1e-3
    df["near_highres_nervous"] = df["distance_to_highres_nervous_mm"] <= threshold_mm

    near = df[df["near_highres_nervous"]].copy()

    out_all = outdir / "secondary_electrons_with_highres_nervous_distance.csv"
    out_near = outdir / "secondary_electrons_near_highres_nervous.csv"
    df.to_csv(out_all, index=False)
    near.to_csv(out_near, index=False)

    write_spectrum(
        near,
        ecol,
        outdir / "electron_spectrum_near_highres_nervous_with_header.csv",
        outdir / "electron_spectrum_near_highres_nervous.csv",
        args.bins,
        args.emax_kev,
    )

    thresholds = [float(x) for x in args.threshold_scan_um.split(",") if x.strip()]
    scan_rows = []
    for um in thresholds:
        mask = df["distance_to_highres_nervous_um"] <= um
        sub = df[mask]
        scan_rows.append({
            "threshold_um": um,
            "n_secondaries_near": int(mask.sum()),
            "fraction_near": float(mask.mean()) if len(mask) else 0.0,
            "mean_energy_keV_near": float(sub[ecol].mean()) if len(sub) else np.nan,
            "median_energy_keV_near": float(sub[ecol].median()) if len(sub) else np.nan,
        })
    scan = pd.DataFrame(scan_rows)
    scan.to_csv(outdir / "nervous_threshold_scan.csv", index=False)

    summary = {
        "secondaries_csv": str(secondaries),
        "nervous_stl": str(nervous_stl),
        "placement_manifest": str(placement_manifest),
        "mm_per_model_unit": args.mm_per_model_unit,
        "global_center_model_units": center_model.tolist(),
        "position_columns": [xcol, ycol, zcol],
        "position_unit_detected": position_unit,
        "position_scale_to_mm": position_scale_to_mm,
        "energy_column": ecol,
        "n_input_secondaries": int(len(df)),
        "n_reference_points": int(len(ref_mm)),
        "threshold_um_primary": args.threshold_um,
        "n_near_primary": int(len(near)),
        "fraction_near_primary": float(len(near) / len(df)) if len(df) else 0.0,
        "median_distance_um_all": float(np.median(df["distance_to_highres_nervous_um"])) if len(df) else None,
        "p05_distance_um_all": float(np.percentile(df["distance_to_highres_nervous_um"], 5)) if len(df) else None,
        "p95_distance_um_all": float(np.percentile(df["distance_to_highres_nervous_um"], 95)) if len(df) else None,
        "mean_energy_keV_near_primary": float(near[ecol].mean()) if len(near) else None,
        "median_energy_keV_near_primary": float(near[ecol].median()) if len(near) else None,
    }

    (outdir / "highres_nervous_scoring_metadata.json").write_text(json.dumps(summary, indent=2))

    print("[OK] high-res nervous proximity scoring complete")
    print(json.dumps(summary, indent=2))
    print()
    print("threshold scan:")
    print(scan.to_string(index=False))
    print()
    print("outputs:")
    for p in [
        out_all,
        out_near,
        outdir / "electron_spectrum_near_highres_nervous.csv",
        outdir / "electron_spectrum_near_highres_nervous_with_header.csv",
        outdir / "nervous_threshold_scan.csv",
        outdir / "highres_nervous_scoring_metadata.json",
    ]:
        print(" ", p)


if __name__ == "__main__":
    main()
