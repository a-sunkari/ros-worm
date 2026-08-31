#!/usr/bin/env python3
"""Distance-, sector-, muscle-, and matched-null scoring for v2 transport."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import vtk
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from score_nervous_surface_v1 import (  # noqa: E402
    body_geometry, closest_surface, enclosed_points, find_xyz, resolve_from_manifest,
    transformed_polydata,
)

SHELLS = [(0, 1), (1, 2), (2, 5), (5, 10), (10, 25), (25, 50), (50, np.inf)]
SECTORS = ["head_sector", "anterior_sector", "midbody_sector", "posterior_sector", "tail_sector"]


def row_stats(frame: pd.DataFrame, energy: str, events: int, dose_per_history: float) -> dict:
    values = frame[energy].to_numpy(float)
    total = float(values.sum()) if len(values) else 0.0
    return {
        "n_electron_births": int(len(frame)),
        "births_per_primary": float(len(frame) / events),
        "births_per_whole_worm_Gy_conditional": float(len(frame) / events / dose_per_history) if dose_per_history > 0 else np.nan,
        "energy_sum_keV": total,
        "energy_per_primary_keV": total / events,
        "mean_energy_keV": float(values.mean()) if len(values) else np.nan,
        "median_energy_keV": float(np.median(values)) if len(values) else np.nan,
        "p10_energy_keV": float(np.percentile(values, 10)) if len(values) else np.nan,
        "p90_energy_keV": float(np.percentile(values, 90)) if len(values) else np.nan,
    }


def write_spectrum(frame: pd.DataFrame, energy_column: str, path: Path) -> None:
    edges = np.geomspace(0.05, 100.0, 81)
    counts, _ = np.histogram(frame[energy_column].to_numpy(float), bins=edges)
    centers = np.sqrt(edges[:-1] * edges[1:])
    with path.open("w") as handle:
        handle.write("# energy_keV,weight\n")
        for energy, weight in zip(centers[counts > 0], counts[counts > 0]):
            handle.write(f"{energy:.9g},{int(weight)}\n")


def inverse_rigid(points: np.ndarray, angle_deg: float, shift: np.ndarray) -> np.ndarray:
    angle = np.deg2rad(angle_deg)
    c, s = np.cos(angle), np.sin(angle)
    rotation = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return (points - shift[None, :]) @ rotation


def transformed_vertices(mesh: vtk.vtkPolyData, angle_deg: float, shift: np.ndarray) -> np.ndarray:
    points = vtk_to_numpy(mesh.GetPoints().GetData()).astype(float)
    angle = np.deg2rad(angle_deg)
    c, s = np.cos(angle), np.sin(angle)
    rotation = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return points @ rotation.T + shift[None, :]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--secondaries", required=True, type=Path)
    parser.add_argument("--transport-summary", required=True, type=Path)
    parser.add_argument("--nervous-stl", required=True, type=Path)
    parser.add_argument("--placement-manifest", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--mm-per-model-unit", type=float, default=0.1)
    parser.add_argument("--null-count", type=int, default=12)
    parser.add_argument("--null-seed", type=int, default=20260830)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(args.secondaries)
    summary = json.loads(args.transport_summary.read_text())
    events = int(summary["events"])
    masses = [float(r["scoring_mass_kg"]) for r in summary["regions"] if r["scoring_mass_kg"] != ""]
    total_mass = sum(masses)
    dose_per_history = float(summary["total_scored_edep_keV"]) * 1.602176634e-16 / total_mass / events
    xyz, to_mm, _ = find_xyz(data)
    points = data[xyz].to_numpy(float) * to_mm
    energy = next(name for name in ["ekin_keV", "energy_keV"] if name in data)
    body_path, center_model = body_geometry(args.placement_manifest)
    body = transformed_polydata(body_path, center_model, args.mm_per_model_unit)
    nervous = transformed_polydata(args.nervous_stl, center_model, args.mm_per_model_unit)
    manifest = pd.read_csv(args.placement_manifest)
    muscle_row = manifest[manifest["safe_name"] == "BodyWallMuscle"].iloc[0]
    muscle = transformed_polydata(resolve_from_manifest(args.placement_manifest, muscle_row["stl_path"]), center_model, args.mm_per_model_unit)

    electron = data["secondaryPDG"].astype(int).eq(11).to_numpy() if "secondaryPDG" in data else np.ones(len(data), bool)
    finite = np.isfinite(points).all(axis=1)
    recorded = data["insideBody"].astype(int).eq(1).to_numpy() if "insideBody" in data else np.ones(len(data), bool)
    geometric = np.zeros(len(data), bool)
    candidates = electron & finite
    geometric[candidates] = enclosed_points(points[candidates], body)
    eligible = electron & finite & recorded & geometric
    scored = data.loc[eligible].copy().reset_index(drop=True)
    scored_points = points[eligible]
    _, neural_distance_mm, _ = closest_surface(scored_points, nervous)
    _, muscle_distance_mm, _ = closest_surface(scored_points, muscle)
    scored["distance_to_nervous_surface_um"] = neural_distance_mm * 1000
    scored["distance_to_bodywall_surface_um"] = muscle_distance_mm * 1000
    scored["inside_bodywall_physical_compartment"] = scored["regionID"].astype(int).eq(3)
    neural_bounds = np.asarray(nervous.GetBounds()).reshape(3, 2)
    sector_edges = np.linspace(neural_bounds[1, 0], neural_bounds[1, 1], 6)
    sector_index = np.clip(np.digitize(scored_points[:, 1], sector_edges[1:-1]), 0, 4)
    scored["longitudinal_sector"] = np.asarray(SECTORS)[sector_index]
    scored.to_csv(args.outdir / "eligible_electrons_anatomy_scored.csv", index=False)

    rows = []
    for lower, upper in SHELLS:
        mask = scored["distance_to_nervous_surface_um"].ge(lower)
        if np.isfinite(upper): mask &= scored["distance_to_nervous_surface_um"].lt(upper)
        row = {"shell_lower_um": lower, "shell_upper_um": upper, "shell_label": f"{lower:g}-{upper:g}" if np.isfinite(upper) else ">=50"}
        row.update(row_stats(scored[mask], energy, events, dose_per_history))
        row["fraction_of_eligible_births"] = float(mask.mean()) if len(mask) else 0.0
        rows.append(row)
        label = f"{lower:g}_{upper:g}um" if np.isfinite(upper) else "ge50um"
        write_spectrum(scored[mask], energy, args.outdir / f"electron_spectrum_neural_shell_{label}.csv")
    pd.DataFrame(rows).to_csv(args.outdir / "neural_distance_shells.csv", index=False)

    sector_rows = []
    for sector in SECTORS:
        for threshold in [1, 2, 5, 10, 25, 50]:
            subset = scored[(scored["longitudinal_sector"] == sector) & (scored["distance_to_nervous_surface_um"] < threshold)]
            row = {"longitudinal_sector": sector, "threshold_um": threshold}
            row.update(row_stats(subset, energy, events, dose_per_history)); sector_rows.append(row)
    pd.DataFrame(sector_rows).to_csv(args.outdir / "neural_longitudinal_sectors.csv", index=False)

    tissue_rows = []
    for label, mask in {
        "inside_bodywall_physical_compartment": scored["inside_bodywall_physical_compartment"],
        "within_5um_nervous_surface": scored["distance_to_nervous_surface_um"] < 5,
        "within_5um_bodywall_surface": scored["distance_to_bodywall_surface_um"] < 5,
        "all_eligible_in_body": np.ones(len(scored), bool),
    }.items():
        row = {"tissue_metric": label}; row.update(row_stats(scored[mask], energy, events, dose_per_history)); tissue_rows.append(row)
    pd.DataFrame(tissue_rows).to_csv(args.outdir / "neural_muscle_comparison.csv", index=False)
    write_spectrum(scored[scored["distance_to_nervous_surface_um"] < 5], energy,
                   args.outdir / "electron_spectrum_neural_within_5um.csv")
    write_spectrum(scored[scored["distance_to_bodywall_surface_um"] < 5], energy,
                   args.outdir / "electron_spectrum_muscle_within_5um.csv")
    write_spectrum(scored[scored["inside_bodywall_physical_compartment"]], energy,
                   args.outdir / "electron_spectrum_inside_bodywall.csv")

    # Exact-surface matched null: small rigid perturbations of the same atlas.
    # Perturbations are admitted only if sampled vertex containment is close to
    # the unperturbed atlas, so the control does not simply move anatomy outside.
    rng = np.random.default_rng(args.null_seed)
    vertices = vtk_to_numpy(nervous.GetPoints().GetData()).astype(float)
    sampled = vertices[::max(1, len(vertices)//10000)]
    baseline_containment = float(enclosed_points(sampled, body).mean())
    null_rows = []
    attempts = 0
    while len(null_rows) < args.null_count and attempts < args.null_count * 100:
        attempts += 1
        angle = float(rng.uniform(-15, 15))
        shift = np.array([rng.uniform(-0.005, 0.005), rng.uniform(-0.025, 0.025), rng.uniform(-0.005, 0.005)])
        moved = transformed_vertices(nervous, angle, shift)[::max(1, len(vertices)//10000)]
        containment = float(enclosed_points(moved, body).mean())
        if containment < baseline_containment - 0.01: continue
        query = inverse_rigid(scored_points, angle, shift)
        _, distance, _ = closest_surface(query, nervous)
        null_rows.append({"null_id": len(null_rows) + 1, "rotation_y_deg": angle,
                          "shift_x_um": shift[0]*1000, "shift_y_um": shift[1]*1000, "shift_z_um": shift[2]*1000,
                          "sampled_atlas_containment": containment,
                          **{f"fraction_within_{t:g}um": float(np.mean(distance*1000 < t)) for t in [1,2,5,10,25,50]}})
    null = pd.DataFrame(null_rows)
    null.to_csv(args.outdir / "neural_matched_atlas_null.csv", index=False)
    real_fraction = float(np.mean(neural_distance_mm * 1000 < 5)) if len(scored) else 0.0
    null_fraction = null["fraction_within_5um"].to_numpy(float) if len(null) else np.array([])
    metadata = {
        "interpretation": "near-neural secondary-electron birth proximity; not nervous dose or intracellular chemistry",
        "events": events, "n_input_records": len(data), "n_eligible_electrons": len(scored),
        "exclusions": {"non_electron": int((~electron).sum()), "nonfinite": int((~finite).sum()),
                       "recorded_outside_body": int((electron & ~recorded).sum()),
                       "geometrically_outside_body": int((electron & finite & ~geometric).sum())},
        "eligible_coordinate_ranges_mm": {
            axis: [float(scored_points[:, i].min()), float(scored_points[:, i].max())] if len(scored_points) else [None, None]
            for i, axis in enumerate(["x", "y", "z"])
        },
        "whole_worm_mass_kg": total_mass, "whole_worm_dose_per_incident_history_Gy": dose_per_history,
        "per_Gy_normalization": "Conditional on identifying the reported experimental Gy with model whole-worm mean absorbed dose.",
        "longitudinal_sectors": "Equal fifths of atlas Y bounds; coordinate sectors, not named neuron classes.",
        "neural_bounds_mm": neural_bounds.tolist(), "body_bounds_mm": np.asarray(body.GetBounds()).reshape(3,2).tolist(),
        "null_model": {"type": "same-atlas small rigid perturbation", "seed": args.null_seed,
                       "requested": args.null_count, "accepted": len(null_rows), "attempts": attempts,
                       "baseline_sampled_atlas_containment": baseline_containment,
                       "real_fraction_within_5um": real_fraction,
                       "null_mean_fraction_within_5um": float(null_fraction.mean()) if len(null_fraction) else None,
                       "enrichment_ratio_real_over_null_mean": float(real_fraction/null_fraction.mean()) if len(null_fraction) and null_fraction.mean() else None,
                       "empirical_upper_tail_p": float((1 + np.sum(null_fraction >= real_fraction))/(1 + len(null_fraction))) if len(null_fraction) else None},
    }
    (args.outdir / "anatomy_scoring_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
