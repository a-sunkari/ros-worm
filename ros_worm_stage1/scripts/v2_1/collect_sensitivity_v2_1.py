#!/usr/bin/env python3
"""Collect corrected v2.1 source/environment/seed sensitivity results."""
from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path

import pandas as pd


CASES = [
    ("focused", "soft_spectrum", "v2_1_sensitivity_corrected_focused_soft_ngm_1M"),
    ("focused", "hard_spectrum", "v2_1_sensitivity_corrected_focused_hard_ngm_1M"),
    ("diffuse", "soft_spectrum", "v2_1_sensitivity_corrected_diffuse_soft_m9_1M"),
    ("diffuse", "hard_spectrum", "v2_1_sensitivity_corrected_diffuse_hard_m9_1M"),
    ("focused", "worm_only_environment", "v2_1_sensitivity_corrected_focused_nominal_worm_only_1M"),
    ("diffuse", "worm_only_environment", "v2_1_sensitivity_corrected_diffuse_nominal_worm_only_1M"),
    ("focused", "water_material", "v2_1_sensitivity_corrected_focused_nominal_ngm_water_1M"),
    ("focused", "independent_seed", "v2_1_replicate_corrected_focused_nominal_ngm_seed2_1M"),
    ("diffuse", "independent_seed", "v2_1_replicate_corrected_diffuse_nominal_m9_seed2_1M"),
]


def summarize(irradiation: str, variation: str, result: Path) -> dict:
    score = result / "anatomy_edep_v2_1"
    dose = pd.read_csv(score / "neural_muscle_dose_by_roi.csv")
    exact = dose[dose.roi == "neural_exact_member_union_with_0.25um_mass_density_1.04"].iloc[0]
    muscle = dose[dose.roi == "physical_body_wall_muscle"].iloc[0]
    shells = pd.read_csv(score / "nervous_surface_edep_shells.csv")
    near = shells[shells.shell_upper_um <= 5.0]
    metadata = json.loads((score / "edep_scoring_metadata.json").read_text())
    warnings = json.loads((result / "navigation_warning_summary.json").read_text())
    return {
        "irradiation": irradiation, "variation": variation, "run_name": result.name,
        "events": int(exact.events), "whole_worm_edep_keV": metadata["event_edep_keV"],
        "neural_dose_ratio": exact.dose_ratio_roi_to_whole_worm,
        "neural_dose_ratio_se": exact.dose_ratio_stochastic_se,
        "neural_contributing_events": int(exact.contributing_events),
        "muscle_dose_ratio": muscle.dose_ratio_roi_to_whole_worm,
        "muscle_dose_ratio_se": muscle.dose_ratio_stochastic_se,
        "muscle_contributing_events": int(muscle.contributing_events),
        "perineural_0_5um_edep_fraction": near.whole_worm_edep_fraction.sum(),
        "perineural_0_5um_fraction_se_approx": math.sqrt((near.whole_worm_edep_fraction_se ** 2).sum()),
        "perineural_contributing_events_nonunique_sum": int(near.contributing_events.sum()),
        "navigation_warning_incidents": warnings["geomnav1002_incidents"],
        "invalid_steps": metadata["nonfinite_steps_excluded"],
        "outside_body_steps": metadata["scoring_position_outside_body_steps_excluded"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--production", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    production_dose = pd.read_csv(args.production / "production_neural_muscle_dose.csv")
    production_shells = pd.read_csv(args.production / "production_nervous_surface_edep_shells.csv")
    production_index = pd.read_csv(args.production / "production_run_index.csv")
    for irradiation in ("focused", "diffuse"):
        d = production_dose[production_dose.irradiation == irradiation]
        exact = d[d.roi == "neural_exact_member_union_with_0.25um_mass_density_1.04"].iloc[0]
        muscle = d[d.roi == "physical_body_wall_muscle"].iloc[0]
        near = production_shells[(production_shells.irradiation == irradiation) &
                                 (production_shells.shell_upper_um <= 5.0)]
        idx = production_index[production_index.irradiation == irradiation].iloc[0]
        rows.append({
            "irradiation": irradiation, "variation": "nominal_10M", "run_name": "tracked_production",
            "events": int(exact.events), "whole_worm_edep_keV": idx.positive_step_edep_keV,
            "neural_dose_ratio": exact.dose_ratio_roi_to_whole_worm,
            "neural_dose_ratio_se": exact.dose_ratio_stochastic_se,
            "neural_contributing_events": int(exact.contributing_events),
            "muscle_dose_ratio": muscle.dose_ratio_roi_to_whole_worm,
            "muscle_dose_ratio_se": muscle.dose_ratio_stochastic_se,
            "muscle_contributing_events": int(muscle.contributing_events),
            "perineural_0_5um_edep_fraction": near.whole_worm_edep_fraction.sum(),
            "perineural_0_5um_fraction_se_approx": math.sqrt((near.whole_worm_edep_fraction_se ** 2).sum()),
            "perineural_contributing_events_nonunique_sum": int(near.contributing_events.sum()),
            "navigation_warning_incidents": int(idx.navigation_warning_incidents),
            "invalid_steps": int(idx.invalid_steps), "outside_body_steps": int(idx.outside_body_steps),
        })
    for irradiation, variation, name in CASES:
        result = args.results / name
        rows.append(summarize(irradiation, variation, result))
        target = args.outdir / "runs" / name
        target.mkdir(parents=True, exist_ok=True)
        for source, filename in [
            (result / "anatomy_edep_v2_1/neural_muscle_dose_by_roi.csv", "neural_muscle_dose_by_roi.csv"),
            (result / "anatomy_edep_v2_1/nervous_surface_edep_shells.csv", "nervous_surface_edep_shells.csv"),
            (result / "anatomy_edep_v2_1/edep_scoring_metadata.json", "edep_scoring_metadata.json"),
            (result / "run_manifest.json", "run_manifest.json"),
            (result / "v2_1_run_manifest.json", "v2_1_run_manifest.json"),
            (result / "transport.mac", "transport.mac"),
            (result / "navigation_warning_summary.json", "navigation_warning_summary.json"),
        ]:
            shutil.copy2(source, target / filename)
    table = pd.DataFrame(rows)
    table.to_csv(args.outdir / "corrected_sensitivity_summary.csv", index=False)
    effects = []
    for row in table.itertuples():
        if row.variation == "nominal_10M":
            continue
        baseline = table[(table.irradiation == row.irradiation) &
                         (table.variation == "nominal_10M")].iloc[0]
        for metric, se_name in [
            ("neural_dose_ratio", "neural_dose_ratio_se"),
            ("muscle_dose_ratio", "muscle_dose_ratio_se"),
            ("perineural_0_5um_edep_fraction", "perineural_0_5um_fraction_se_approx"),
        ]:
            value = getattr(row, metric); reference = baseline[metric]
            combined_se = math.sqrt(getattr(row, se_name) ** 2 + baseline[se_name] ** 2)
            effects.append({
                "irradiation": row.irradiation, "variation": row.variation, "metric": metric,
                "value": value, "nominal_10M": reference,
                "percent_change": 100.0 * (value / reference - 1.0),
                "combined_standard_error": combined_se,
                "difference_over_combined_se": (value - reference) / combined_se if combined_se else float("nan"),
                "power_note": "1M neural ROI variants are underpowered when contributing events <30; perineural and muscle endpoints are more precise.",
            })
    pd.DataFrame(effects).to_csv(args.outdir / "corrected_sensitivity_effects.csv", index=False)


if __name__ == "__main__":
    main()
