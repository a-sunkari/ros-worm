#!/usr/bin/env python3
"""Collect compact corrected production artifacts into validation/v2_1."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd


def copy_if_present(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--focused", type=Path, required=True)
    parser.add_argument("--diffuse", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    combined_dose = []
    combined_shells = []
    index_rows = []
    for label, result in [("focused", args.focused.resolve()), ("diffuse", args.diffuse.resolve())]:
        target = args.outdir / label
        score = result / "anatomy_edep_v2_1"
        files = [
            "neural_muscle_dose_by_roi.csv", "nervous_surface_edep_shells.csv",
            "edep_particle_process_composition.csv", "local_edep_weighted_electron_spectra.csv",
            "edep_scoring_metadata.json", "edep_position_assignment_sensitivity.csv",
            "deposition_step_length_qc.csv", "position_sensitivity_metadata.json",
        ]
        for name in files:
            copy_if_present(score / name, target / name)
        for name in ["neural_roi_registration_sensitivity.csv", "nervous_surface_edep_matched_nulls.csv",
                     "edep_control_metadata.json"]:
            copy_if_present(score / "controls_1M_prefix" / name, target / "controls_1M_prefix" / name)
        for name in ["neural_roi_registration_sensitivity.csv", "edep_control_metadata.json"]:
            copy_if_present(score / "controls_full_registration" / name,
                            target / "controls_full_registration" / name)
        for name in ["transport.mac", "transport_summary.json", "navigation_warning_summary.json",
                     "run_manifest.json", "v2_1_run_manifest.json"]:
            copy_if_present(result / name, target / name)

        macro = (result / "transport.mac").read_text()
        log = (result / "transport.log").read_text(errors="replace")
        if "/rosworm/maxStep_um 0.5 um" not in macro or "[ROS-WORM][STEP_LIMIT] charged_max_step_um=0.5" not in log:
            raise SystemExit(f"{label} is not the corrected 0.5-um production run")
        dose = pd.read_csv(score / "neural_muscle_dose_by_roi.csv")
        dose.insert(0, "irradiation", label)
        combined_dose.append(dose)
        shells = pd.read_csv(score / "nervous_surface_edep_shells.csv")
        shells.insert(0, "irradiation", label)
        combined_shells.append(shells)
        metadata = json.loads((score / "edep_scoring_metadata.json").read_text())
        warnings = json.loads((result / "navigation_warning_summary.json").read_text())
        index_rows.append({"irradiation": label, "result_directory_at_collection": str(result),
                           "root_sha256": metadata["root_sha256"], "events": metadata["events"],
                           "steps": metadata["steps"], "positive_step_edep_keV": metadata["positive_step_edep_keV"],
                           "invalid_steps": metadata["nonfinite_steps_excluded"],
                           "outside_body_steps": metadata["scoring_position_outside_body_steps_excluded"],
                           "navigation_warning_incidents": warnings["geomnav1002_incidents"],
                           "charged_max_step_um": 0.5})
    pd.concat(combined_dose, ignore_index=True).to_csv(args.outdir / "production_neural_muscle_dose.csv", index=False)
    pd.concat(combined_shells, ignore_index=True).to_csv(args.outdir / "production_nervous_surface_edep_shells.csv", index=False)
    pd.DataFrame(index_rows).to_csv(args.outdir / "production_run_index.csv", index=False)


if __name__ == "__main__":
    main()
