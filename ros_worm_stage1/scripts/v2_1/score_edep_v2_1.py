#!/usr/bin/env python3
"""Score actual Geant4 deposited energy against neural anatomy for v2.1."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import vtk
# VTK must be loaded before ROOT in the project conda environment so ROOT's
# bundled libcurl does not pre-empt VTK's OpenSSL-linked dependency chain.
import ROOT

sys.path.insert(0, str(Path(__file__).resolve().parent))
from neural_roi import (  # noqa: E402
    SparseVoxelROI, body_center_and_path, inside_member_union, load_member_surfaces,
    stl_polydata,
)

SHELLS = [(0.0, 1.0), (1.0, 2.0), (2.0, 5.0), (5.0, 10.0),
          (10.0, 25.0), (25.0, 50.0), (50.0, np.inf)]
KEV_TO_J = 1.602176634e-16


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def root_arrays(path: Path, tree: str, branches: list[str]) -> dict[str, np.ndarray]:
    frame = ROOT.RDataFrame(tree, str(path))
    available = {str(name) for name in frame.GetColumnNames()}
    missing = [name for name in branches if name not in available]
    if missing:
        raise SystemExit(f"{tree} tree lacks required v2.1 branches: {missing}")
    return {key: np.asarray(value) for key, value in frame.AsNumpy(branches).items()}


def closest_distance(points_um: np.ndarray, surface: vtk.vtkPolyData) -> np.ndarray:
    locator = vtk.vtkStaticCellLocator()
    locator.SetDataSet(surface)
    locator.BuildLocator()
    distances = np.empty(len(points_um), dtype=np.float32)
    cell = vtk.vtkGenericCell()
    for index, point in enumerate(points_um):
        target = [0.0, 0.0, 0.0]
        cell_id, sub_id, distance2 = vtk.reference(0), vtk.reference(0), vtk.reference(0.0)
        locator.FindClosestPoint(point, target, cell, cell_id, sub_id, distance2)
        distances[index] = float(distance2) ** 0.5
    return distances


def event_metric(mask: np.ndarray, event_id: np.ndarray, edep: np.ndarray,
                 event_total: np.ndarray) -> dict:
    count = len(event_total)
    values = np.bincount(event_id[mask], weights=edep[mask], minlength=count).astype(float)
    x_mean = float(values.mean())
    y_mean = float(event_total.mean())
    x_var = float(values.var(ddof=1)) if count > 1 else 0.0
    y_var = float(event_total.var(ddof=1)) if count > 1 else 0.0
    covariance = float(np.cov(values, event_total, ddof=1)[0, 1]) if count > 1 else 0.0
    fraction = x_mean / y_mean if y_mean > 0 else np.nan
    mean_se = math.sqrt(x_var / count) if count else np.nan
    ratio_variance = ((x_var + fraction * fraction * y_var - 2 * fraction * covariance) /
                      (count * y_mean * y_mean)) if count > 1 and y_mean > 0 else np.nan
    ratio_se = math.sqrt(max(0.0, ratio_variance)) if np.isfinite(ratio_variance) else np.nan
    return {
        "total_edep_keV": float(values.sum()), "edep_per_history_keV": x_mean,
        "edep_per_history_se_keV": mean_se,
        "whole_worm_edep_fraction": fraction, "whole_worm_edep_fraction_se": ratio_se,
        "whole_worm_edep_fraction_ci95_low": max(0.0, fraction - 1.96 * ratio_se) if np.isfinite(ratio_se) else np.nan,
        "whole_worm_edep_fraction_ci95_high": fraction + 1.96 * ratio_se if np.isfinite(ratio_se) else np.nan,
        "contributing_events": int(np.count_nonzero(values)),
    }


def dose_metric(label: str, mask: np.ndarray, mass_kg: float, density: float,
                event_id: np.ndarray, edep: np.ndarray, event_total: np.ndarray,
                whole_mass_kg: float, events: int, pitch: float | None = None) -> dict:
    stats = event_metric(mask, event_id, edep, event_total)
    total_j = stats["total_edep_keV"] * KEV_TO_J
    dose_simulated = total_j / mass_kg
    whole_dose = float(event_total.sum()) * KEV_TO_J / whole_mass_kg
    ratio = dose_simulated / whole_dose if whole_dose else np.nan
    relative_se = stats["whole_worm_edep_fraction_se"] / stats["whole_worm_edep_fraction"] if stats["whole_worm_edep_fraction"] else np.nan
    return {
        "roi": label, "pitch_um": pitch, "density_g_cm3": density,
        "mass_kg": mass_kg, **stats, "simulated_roi_dose_Gy": dose_simulated,
        "simulated_whole_worm_dose_Gy": whole_dose,
        "dose_ratio_roi_to_whole_worm": ratio,
        "dose_ratio_stochastic_se": ratio * relative_se if np.isfinite(relative_se) else np.nan,
        "edep_steps": int(mask.sum()), "events": events,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--transport-summary", type=Path, required=True)
    parser.add_argument("--placement-manifest", type=Path, required=True)
    parser.add_argument("--nervous-stl", type=Path, required=True)
    parser.add_argument("--source-member-manifest", type=Path, required=True)
    parser.add_argument("--neural-roi", type=Path, action="append", default=[])
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--density-g-cm3", type=float, default=1.04)
    parser.add_argument("--skip-exact-member-union", action="store_true")
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    repo = Path(__file__).resolve().parents[3]

    branches = ["eventID", "regionID", "pdg", "trackID", "parentID", "edep_keV",
                "ekin_pre_keV", "step_um", "midX_um", "midY_um", "midZ_um",
                "insideBodyMid", "processType", "processSubtype",
                "creatorProcessType", "creatorProcessSubtype"]
    step = root_arrays(args.root.resolve(), "steps", branches)
    event = root_arrays(args.root.resolve(), "event", ["eventID", "Edep_total_worm_keV"])
    events = len(event["eventID"])
    event_ids = event["eventID"].astype(np.int64)
    if not np.array_equal(np.sort(event_ids), np.arange(events)):
        raise SystemExit("event IDs are not a permutation of the expected contiguous 0..N-1 sequence")
    # Geant4 MT ntuple merging does not promise event-row order.
    event_total = np.empty(events, dtype=float)
    event_total[event_ids] = event["Edep_total_worm_keV"].astype(float)
    points = np.column_stack([step["midX_um"], step["midY_um"], step["midZ_um"]]).astype(float)
    edep = step["edep_keV"].astype(float)
    event_id = step["eventID"].astype(np.int64)
    finite = np.isfinite(points).all(axis=1) & np.isfinite(edep) & (edep > 0)
    recorded_inside = step["insideBodyMid"].astype(bool)
    eligible = finite & recorded_inside

    summary = json.loads(args.transport_summary.read_text())
    masses = [float(row["scoring_mass_kg"]) for row in summary["regions"]
              if row["scoring_mass_kg"] != ""]
    whole_mass = float(sum(masses))
    modeled_dose_per_history = event_total.sum() * KEV_TO_J / whole_mass / events
    sum_difference = float(edep.sum() - event_total.sum())
    if not np.isclose(edep.sum(), event_total.sum(), rtol=1e-10, atol=1e-9):
        raise SystemExit(f"Positive step edep does not reproduce event edep: delta={sum_difference} keV")

    center_model, _ = body_center_and_path(args.placement_manifest.resolve(), repo)
    nervous = stl_polydata(args.nervous_stl.resolve(), center_model, 100.0)
    distance = np.full(len(edep), np.nan, dtype=np.float32)
    distance[eligible] = closest_distance(points[eligible], nervous)
    np.savez_compressed(args.outdir / "edep_step_scoring_cache.npz",
                        eventID=event_id, regionID=step["regionID"], pdg=step["pdg"],
                        edep_keV=edep, ekin_pre_keV=step["ekin_pre_keV"],
                        midX_um=points[:, 0], midY_um=points[:, 1], midZ_um=points[:, 2],
                        distance_to_nervous_surface_um=distance, eligible=eligible)

    shell_rows = []
    for lower, upper in SHELLS:
        mask = eligible & (distance >= lower)
        if np.isfinite(upper):
            mask &= distance < upper
        stats = event_metric(mask, event_id, edep, event_total)
        shell_rows.append({"shell_lower_um": lower, "shell_upper_um": upper,
                           "shell_label": f"{lower:g}-{upper:g}" if np.isfinite(upper) else ">=50",
                           **stats,
                           "edep_keV_per_whole_worm_Gy": stats["edep_per_history_keV"] / modeled_dose_per_history,
                           "edep_steps": int(mask.sum()),
                           "mean_step_edep_keV": float(edep[mask].mean()) if mask.any() else np.nan})
    pd.DataFrame(shell_rows).to_csv(args.outdir / "nervous_surface_edep_shells.csv", index=False)

    composition = pd.DataFrame({name: step[name] for name in ["pdg", "processType", "processSubtype"]})
    composition["edep_keV"] = edep
    composition = composition.loc[eligible].groupby(["pdg", "processType", "processSubtype"], as_index=False).agg(
        edep_keV=("edep_keV", "sum"), edep_steps=("edep_keV", "size"))
    composition["fraction_eligible_edep"] = composition.edep_keV / edep[eligible].sum()
    composition.to_csv(args.outdir / "edep_particle_process_composition.csv", index=False)

    dose_rows = []
    for roi_path in args.neural_roi:
        roi = SparseVoxelROI.load(roi_path)
        inside = eligible & roi.contains(points)
        volume_um3 = len(roi.flat_indices) * roi.pitch_um ** 3
        mass = volume_um3 * 1e-18 * args.density_g_cm3 * 1000.0
        dose_rows.append(dose_metric(f"neural_voxel_{roi.pitch_um:g}um", inside, mass,
                                     args.density_g_cm3, event_id, edep, event_total,
                                     whole_mass, events, roi.pitch_um))

    exact_inside = None
    if not args.skip_exact_member_union:
        members, _, _ = load_member_surfaces(args.source_member_manifest.resolve(),
                                             args.placement_manifest.resolve(), repo)
        exact_inside = np.zeros(len(points), dtype=bool)
        exact_inside[eligible] = inside_member_union(points[eligible], members)
        np.savez_compressed(args.outdir / "exact_member_union_step_membership.npz", inside=exact_inside)

    muscle_rows = [row for row in summary["regions"] if row["region_key"] == "bodywall"]
    if len(muscle_rows) != 1 or muscle_rows[0]["scoring_mass_kg"] == "":
        raise SystemExit("Transport summary lacks one physical body-wall muscle mass")
    muscle_mass = float(muscle_rows[0]["scoring_mass_kg"])
    muscle = eligible & (step["regionID"].astype(int) == 3)
    dose_rows.append(dose_metric("physical_body_wall_muscle", muscle, muscle_mass, 1.05,
                                 event_id, edep, event_total, whole_mass, events))
    pd.DataFrame(dose_rows).to_csv(args.outdir / "neural_muscle_dose_by_roi.csv", index=False)

    spectrum_edges = np.geomspace(0.01, max(100.0, float(step["ekin_pre_keV"].max())), 101)
    spectrum_rows = []
    masks = {"all_eligible": eligible, "within_5um_nervous_surface": eligible & (distance < 5),
             "physical_body_wall_muscle": muscle}
    if args.neural_roi:
        finest = SparseVoxelROI.load(min(args.neural_roi, key=lambda path: SparseVoxelROI.load(path).pitch_um))
        masks["finest_neural_roi"] = eligible & finest.contains(points)
    for label, mask in masks.items():
        electron = mask & (np.abs(step["pdg"].astype(int)) == 11)
        weights, _ = np.histogram(step["ekin_pre_keV"][electron], bins=spectrum_edges, weights=edep[electron])
        counts, _ = np.histogram(step["ekin_pre_keV"][electron], bins=spectrum_edges)
        for left, right, count, weight in zip(spectrum_edges[:-1], spectrum_edges[1:], counts, weights):
            spectrum_rows.append({"roi": label, "energy_low_keV": left, "energy_high_keV": right,
                                  "electron_steps": int(count), "electron_edep_keV": float(weight)})
    pd.DataFrame(spectrum_rows).to_csv(args.outdir / "local_edep_weighted_electron_spectra.csv", index=False)

    metadata = {
        "endpoint": "nervous-surface-referenced deposited energy at Geant4 step midpoints",
        "not_equivalent_to": ["secondary-electron birth energy", "nervous absorbed dose without an explicit ROI mass"],
        "root_file": str(args.root.resolve()), "root_sha256": sha256(args.root.resolve()),
        "steps": len(edep), "events": events, "positive_step_edep_keV": float(edep.sum()),
        "event_edep_keV": float(event_total.sum()), "step_minus_event_edep_keV": sum_difference,
        "eligible_steps": int(eligible.sum()), "nonfinite_steps_excluded": int((~finite).sum()),
        "midpoint_outside_body_steps_excluded": int((finite & ~recorded_inside).sum()),
        "midpoint_outside_body_edep_keV_excluded": float(edep[finite & ~recorded_inside].sum()),
        "whole_worm_mass_kg": whole_mass, "whole_worm_dose_per_history_Gy": modeled_dose_per_history,
        "distance_surface": str(args.nervous_stl.resolve()), "distance_surface_sha256": sha256(args.nervous_stl.resolve()),
        "distance_units": "um", "position_definition": "midpoint of Geant4 pre-step and post-step positions",
        "roi_density_g_cm3": args.density_g_cm3, "exact_member_union_membership_computed": exact_inside is not None,
        "stochastic_uncertainty": "event-level sample variance; ratio SE uses first-order covariance propagation",
        "process_caveat": "process-defined-step categories are diagnostic labels and do not uniquely cause continuous energy loss",
    }
    (args.outdir / "edep_scoring_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
