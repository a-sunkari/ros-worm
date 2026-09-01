#!/usr/bin/env python3
"""Pre/mid/post/hybrid energy-deposition position sensitivity for v2.1."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import vtk  # load before ROOT in the project conda environment
import ROOT

sys.path.insert(0, str(Path(__file__).resolve().parent))
from neural_roi import SparseVoxelROI  # noqa: E402

KEV_TO_J = 1.602176634e-16


def arrays(path: Path, tree: str, names: list[str]) -> dict[str, np.ndarray]:
    return {name: np.asarray(value) for name, value in ROOT.RDataFrame(tree, str(path)).AsNumpy(names).items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--transport-summary", type=Path, required=True)
    parser.add_argument("--neural-roi", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    names = ["eventID", "pdg", "edep_keV", "step_um",
             "preX_um", "preY_um", "preZ_um", "midX_um", "midY_um", "midZ_um",
             "postX_um", "postY_um", "postZ_um", "edepX_um", "edepY_um", "edepZ_um",
             "edepPositionCode", "insideBodyEdep"]
    step = arrays(args.root.resolve(), "steps", names)
    event = arrays(args.root.resolve(), "event", ["eventID", "Edep_total_worm_keV"])
    summary = json.loads(args.transport_summary.read_text())
    whole_mass = sum(float(row["scoring_mass_kg"]) for row in summary["regions"] if row["scoring_mass_kg"] != "")
    total_edep = float(event["Edep_total_worm_keV"].sum())
    whole_dose = total_edep * KEV_TO_J / whole_mass
    roi = SparseVoxelROI.load(args.neural_roi)
    volume_um3 = len(roi.flat_indices) * roi.pitch_um ** 3
    mass = volume_um3 * 1e-18 * 1.04 * 1000.0
    edep = step["edep_keV"].astype(float)

    definitions = {
        "pre_step_all_particles": ["preX_um", "preY_um", "preZ_um"],
        "midpoint_all_particles": ["midX_um", "midY_um", "midZ_um"],
        "post_step_all_particles": ["postX_um", "postY_um", "postZ_um"],
        "v2_1_hybrid_charged_mid_neutral_post": ["edepX_um", "edepY_um", "edepZ_um"],
    }
    rows = []
    for label, xyz in definitions.items():
        points = np.column_stack([step[name] for name in xyz]).astype(float)
        finite = np.isfinite(points).all(axis=1)
        inside = finite & roi.contains(points)
        inside_edep = float(edep[inside].sum())
        rows.append({"position_definition": label, "inside_steps": int(inside.sum()),
                     "inside_edep_keV": inside_edep,
                     "inside_edep_fraction_whole_worm": inside_edep / total_edep,
                     "dose_ratio_neural_to_whole_worm": (inside_edep * KEV_TO_J / mass) / whole_dose})
    table = pd.DataFrame(rows)
    baseline = float(table.loc[table.position_definition == "v2_1_hybrid_charged_mid_neutral_post", "inside_edep_keV"].iloc[0])
    table["edep_ratio_to_v2_1_hybrid"] = table.inside_edep_keV / baseline
    table.to_csv(args.outdir / "edep_position_assignment_sensitivity.csv", index=False)

    length_rows = []
    for pdg in sorted(np.unique(step["pdg"].astype(int))):
        values = step["step_um"][step["pdg"].astype(int) == pdg].astype(float)
        length_rows.append({"pdg": pdg, "steps": len(values), "maximum_step_um": float(values.max()),
                            "p50_step_um": float(np.percentile(values, 50)),
                            "p95_step_um": float(np.percentile(values, 95)),
                            "p99_step_um": float(np.percentile(values, 99)),
                            "steps_above_0p5um": int((values > 0.500001).sum()),
                            "steps_above_2um": int((values > 2.000001).sum())})
    pd.DataFrame(length_rows).to_csv(args.outdir / "deposition_step_length_qc.csv", index=False)
    metadata = {
        "primary_position_definition": "charged midpoint after enforced 0.5 um maximum; neutral post-step interaction point",
        "roi_pitch_um": roi.pitch_um, "roi_density_g_cm3": 1.04,
        "position_code_counts": {str(int(key)): int(value) for key, value in zip(*np.unique(step["edepPositionCode"], return_counts=True))},
        "position_codes": {"1": "charged midpoint", "2": "neutral post-step"},
        "all_primary_positions_inside_body": bool(step["insideBodyEdep"].astype(bool).all()),
    }
    (args.outdir / "position_sensitivity_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
