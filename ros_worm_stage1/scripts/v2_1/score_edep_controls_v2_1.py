#!/usr/bin/env python3
"""Matched-atlas null and registration controls for v2.1 deposited energy."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from vtk.util.numpy_support import vtk_to_numpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from neural_roi import (  # noqa: E402
    SparseVoxelROI, body_center_and_path, closest_surface_distances_file,
    enclosed_points, stl_polydata,
)


def inverse_rigid(points: np.ndarray, angle_y_deg: float, shift_um: np.ndarray) -> np.ndarray:
    angle = np.deg2rad(angle_y_deg)
    c, s = np.cos(angle), np.sin(angle)
    rotation = np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])
    return (points - shift_um[None, :]) @ rotation


def forward_rigid(points: np.ndarray, angle_y_deg: float, shift_um: np.ndarray) -> np.ndarray:
    angle = np.deg2rad(angle_y_deg)
    c, s = np.cos(angle), np.sin(angle)
    rotation = np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])
    return points @ rotation.T + shift_um[None, :]


def threshold_stats(distance: np.ndarray, edep: np.ndarray, thresholds: list[float]) -> dict:
    result = {}
    for threshold in thresholds:
        mask = distance < threshold
        result[f"steps_within_{threshold:g}um"] = int(mask.sum())
        result[f"step_fraction_within_{threshold:g}um"] = float(mask.mean())
        result[f"edep_keV_within_{threshold:g}um"] = float(edep[mask].sum())
        result[f"edep_fraction_within_{threshold:g}um"] = float(edep[mask].sum() / edep.sum())
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scoring-cache", type=Path, required=True)
    parser.add_argument("--nervous-stl", type=Path, required=True)
    parser.add_argument("--placement-manifest", type=Path, required=True)
    parser.add_argument("--neural-roi", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--null-count", type=int, default=12)
    parser.add_argument("--null-seed", type=int, default=20260831)
    parser.add_argument("--distance-workers", type=int, default=4)
    parser.add_argument("--skip-nulls", action="store_true")
    parser.add_argument("--max-event-id-exclusive", type=int,
                        help="Use a deterministic event-ID prefix for affordable null controls")
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    repo = Path(__file__).resolve().parents[3]

    cache = np.load(args.scoring_cache)
    eligible = cache["eligible"].astype(bool)
    if args.max_event_id_exclusive is not None:
        eligible &= cache["eventID"].astype(np.int64) < args.max_event_id_exclusive
    xyz = ["scoreX_um", "scoreY_um", "scoreZ_um"] if "scoreX_um" in cache.files else ["midX_um", "midY_um", "midZ_um"]
    points = np.column_stack([cache[name] for name in xyz])[eligible]
    edep = cache["edep_keV"].astype(float)[eligible]
    real_distance = cache["distance_to_nervous_surface_um"].astype(float)[eligible]
    if not np.isfinite(real_distance).all() and not args.skip_nulls:
        raise SystemExit("Cache lacks real full-atlas distances")

    center_model, body_path = body_center_and_path(args.placement_manifest.resolve(), repo)
    body = stl_polydata(body_path, center_model, 100.0)
    nervous = stl_polydata(args.nervous_stl.resolve(), center_model, 100.0)
    vertices = vtk_to_numpy(nervous.GetPoints().GetData()).astype(float)
    sampled_vertices = vertices[::max(1, len(vertices) // 20_000)]
    baseline_containment = float(enclosed_points(sampled_vertices, body).mean())

    # Registration bracket: explicit measurement/model uncertainty, not a null.
    registration_transforms = [
        ("baseline", 0.0, (0.0, 0.0, 0.0)),
        ("x_minus_2um", 0.0, (-2.0, 0.0, 0.0)), ("x_plus_2um", 0.0, (2.0, 0.0, 0.0)),
        ("y_minus_5um", 0.0, (0.0, -5.0, 0.0)), ("y_plus_5um", 0.0, (0.0, 5.0, 0.0)),
        ("z_minus_2um", 0.0, (0.0, 0.0, -2.0)), ("z_plus_2um", 0.0, (0.0, 0.0, 2.0)),
        ("rotation_minus_3deg", -3.0, (0.0, 0.0, 0.0)),
        ("rotation_plus_3deg", 3.0, (0.0, 0.0, 0.0)),
    ]
    roi = SparseVoxelROI.load(args.neural_roi)
    roi_volume_um3 = len(roi.flat_indices) * roi.pitch_um ** 3
    registration_rows = []
    total_edep = float(edep.sum())
    for label, angle, shift_tuple in registration_transforms:
        shift = np.asarray(shift_tuple, dtype=float)
        query = inverse_rigid(points, angle, shift)
        inside = roi.contains(query)
        moved_vertices = forward_rigid(sampled_vertices, angle, shift)
        registration_rows.append({
            "registration_case": label, "rotation_y_deg": angle,
            "shift_x_um": shift[0], "shift_y_um": shift[1], "shift_z_um": shift[2],
            "sampled_atlas_containment": float(enclosed_points(moved_vertices, body).mean()),
            "inside_steps": int(inside.sum()), "inside_edep_keV": float(edep[inside].sum()),
            "inside_edep_fraction_whole_worm": float(edep[inside].sum() / total_edep),
            "roi_pitch_um": roi.pitch_um, "roi_volume_um3": roi_volume_um3,
        })
    registration = pd.DataFrame(registration_rows)
    baseline_edep = float(registration.loc[registration.registration_case == "baseline", "inside_edep_keV"].iloc[0])
    registration["edep_ratio_to_baseline"] = registration.inside_edep_keV / baseline_edep
    registration.to_csv(args.outdir / "neural_roi_registration_sensitivity.csv", index=False)

    null_rows = []
    thresholds = [1.0, 2.0, 5.0, 10.0, 25.0, 50.0]
    if not args.skip_nulls:
        rng = np.random.default_rng(args.null_seed)
        attempts = 0
        while len(null_rows) < args.null_count and attempts < args.null_count * 200:
            attempts += 1
            angle = float(rng.uniform(-15.0, 15.0))
            shift = np.array([rng.uniform(-5.0, 5.0), rng.uniform(-25.0, 25.0), rng.uniform(-5.0, 5.0)])
            moved = forward_rigid(sampled_vertices, angle, shift)
            containment = float(enclosed_points(moved, body).mean())
            if containment < baseline_containment - 0.01:
                continue
            query = inverse_rigid(points, angle, shift)
            distance = closest_surface_distances_file(query, args.nervous_stl.resolve(), center_model,
                                                      100.0, args.distance_workers)
            null_rows.append({"null_id": len(null_rows) + 1, "rotation_y_deg": angle,
                              "shift_x_um": shift[0], "shift_y_um": shift[1], "shift_z_um": shift[2],
                              "sampled_atlas_containment": containment,
                              **threshold_stats(distance, edep, thresholds)})
            print(f"completed matched-atlas null {len(null_rows)}/{args.null_count}", flush=True)
        pd.DataFrame(null_rows).to_csv(args.outdir / "nervous_surface_edep_matched_nulls.csv", index=False)
    else:
        attempts = 0

    real = threshold_stats(real_distance, edep, thresholds) if np.isfinite(real_distance).all() else {}
    null_5 = np.array([row["edep_fraction_within_5um"] for row in null_rows], dtype=float)
    metadata = {
        "control": "same full-resolution atlas under anatomically contained rigid perturbations; surface area and triangle content exactly matched",
        "event_id_prefix_exclusive": args.max_event_id_exclusive,
        "real": real, "null_seed": args.null_seed, "null_requested": args.null_count,
        "null_accepted": len(null_rows), "null_attempts": attempts,
        "baseline_sampled_atlas_containment": baseline_containment,
        "registration_bracket": "assumed +/-2 um transverse, +/-5 um longitudinal, and +/-3 degree Y rotation",
        "real_over_null_mean_edep_fraction_within_5um": (
            real.get("edep_fraction_within_5um", np.nan) / null_5.mean()) if len(null_5) and null_5.mean() else None,
        "null_empirical_upper_tail_p_within_5um": (
            float((1 + np.sum(null_5 >= real["edep_fraction_within_5um"])) / (1 + len(null_5)))) if len(null_5) else None,
        "interpretation": "tests spatial enrichment of deposited energy near the real atlas; does not test molecular targeting",
    }
    (args.outdir / "edep_control_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
