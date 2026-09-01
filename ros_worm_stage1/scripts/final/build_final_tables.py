#!/usr/bin/env python3
"""Build the paper-facing, machine-readable final tables and spatial profiles."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--outdir", type=Path, required=True)
    a = p.parse_args(); repo = a.repo.resolve(); out = a.outdir.resolve(); out.mkdir(parents=True, exist_ok=True)
    vf = repo / "ros_worm_stage1/validation/final"
    stats = pd.read_csv(vf / "statistics/final_nominal_dose_statistics.csv")
    dose = pd.read_csv(vf / "production/production_neural_muscle_dose.csv")
    shells = pd.read_csv(vf / "production/production_nervous_surface_edep_shells.csv")
    chemistry = pd.read_csv(vf / "chemistry/cannon_condition_summary.csv")

    # One row per final nominal regional estimator.
    nominal = stats.copy()
    nominal["mc_relative_se_percent"] = 100 * nominal.delta_method_se / nominal.roi_to_whole_dose_ratio
    nominal["mc_ci_method"] = np.where(nominal.normal_interval_adequate, "event-level covariance delta method; bootstrap corroborated", "Poisson event bootstrap")
    nominal.to_csv(out / "final_nominal_regional_dose.csv", index=False)

    # Separate unlike uncertainty sources rather than collapsing them into one +/-.
    urows = []
    for irr in ("focused", "diffuse"):
        s = stats[(stats.irradiation == irr) & stats.roi.str.startswith("neural_")].iloc[0]
        vox = dose[(dose.irradiation == irr) & dose.roi.str.startswith("neural_voxel_")]
        reg = pd.read_csv(vf / f"registration/{irr}/neural_roi_registration_sensitivity.csv")
        for source, low, high, kind, note in [
            ("Monte Carlo statistics", s.delta_method_ci95_low, s.delta_method_ci95_high, "95% sampling interval", "event-level covariance propagation; Poisson bootstrap corroboration"),
            ("ROI pitch/reconstruction", vox.dose_ratio_roi_to_whole_worm.min(), vox.dose_ratio_roi_to_whole_worm.max(), "deterministic range", "0.25, 0.5, 1 and 2 um body-clipped union ROIs"),
            ("atlas registration", s.roi_to_whole_dose_ratio * reg.edep_ratio_to_baseline.min(), s.roi_to_whole_dose_ratio * reg.edep_ratio_to_baseline.max(), "deterministic bracket", "+/-2 um transverse, +/-5 um longitudinal, +/-3 degrees"),
            ("reported experimental dosimetry", 0.5 * s.roi_to_whole_dose_ratio, 2.0 * s.roi_to_whole_dose_ratio, "external multiplicative range", "Cannon et al. approximate factor-of-two uncertainty; applies to absolute Gy, not transport ratio"),
        ]:
            urows.append({"irradiation": irr, "endpoint": "neural/whole-worm dose ratio", "central": s.roi_to_whole_dose_ratio,
                          "uncertainty_source": source, "lower": low, "upper": high, "interval_type": kind, "note": note})
    effects = pd.read_csv(repo / "ros_worm_stage1/validation/v2_1/sensitivity/corrected_sensitivity_effects.csv")
    for _, r in effects[effects.metric == "perineural_0_5um_edep_fraction"].iterrows():
        urows.append({"irradiation": r.irradiation, "endpoint": "0-5 um nervous-surface edep fraction",
                      "central": r.nominal_10M, "uncertainty_source": r.variation, "lower": r.value, "upper": r.value,
                      "interval_type": "one-at-a-time 1M sensitivity estimate", "note": r.power_note})
    pd.DataFrame(urows).to_csv(out / "final_uncertainty_budget.csv", index=False)

    # Surface-based comparison on identical distance shells.
    muscle = pd.concat([pd.read_csv(vf / f"surfaces/{irr}/muscle_surface_edep_shells.csv").assign(irradiation=irr)
                        for irr in ("focused", "diffuse")], ignore_index=True)
    neural = shells.copy(); neural["surface"] = "nervous"; muscle["surface"] = "muscle"
    common = [c for c in neural.columns if c in muscle.columns]
    surface = pd.concat([neural[common], muscle[common]], ignore_index=True)
    surface.to_csv(out / "neural_muscle_surface_edep_shells.csv", index=False)
    within5 = surface[surface.shell_upper_um <= 5].groupby(["irradiation", "surface"], as_index=False).agg(
        edep_keV=("total_edep_keV", "sum"), edep_fraction=("whole_worm_edep_fraction", "sum"),
        edep_keV_per_whole_worm_Gy=("edep_keV_per_whole_worm_Gy", "sum"))
    within5.to_csv(out / "neural_muscle_surface_within5um.csv", index=False)

    # Final Cannon table. Perineural energy is fluence-linear and therefore reused.
    perigy = within5[within5.surface == "nervous"].set_index("irradiation").edep_keV_per_whole_worm_Gy
    crows = []
    for condition, group in chemistry.groupby("condition", sort=False):
        n = group[group.analysis_region == "neural"].iloc[0]; m = group[group.analysis_region == "muscle"].iloc[0]
        crows.append({
            "condition": condition, "source_type": n.irradiation, "phenotype": n.phenotype,
            "kV": 50 if n.irradiation == "focused" else 20, "reported_dose_rate_Gy_s": n.dose_rate_Gy_s,
            "exposure_s": n.exposure_s, "reported_whole_worm_dose_Gy": n.reported_total_dose_Gy,
            "neural_to_whole_ratio": n.dose_ratio_to_whole_worm, "neural_ratio_mc_se": n.dose_ratio_stochastic_se,
            "neural_ratio_reconstruction_low": n.dose_ratio_reconstruction_low, "neural_ratio_reconstruction_high": n.dose_ratio_reconstruction_high,
            "neural_Gy": n.modeled_local_dose_Gy, "muscle_to_whole_ratio": m.dose_ratio_to_whole_worm,
            "muscle_ratio_mc_se": m.dose_ratio_stochastic_se, "muscle_Gy": m.modeled_local_dose_Gy,
            "perineural_0_5um_edep_keV_per_whole_worm_Gy": perigy[n.irradiation],
            "neural_OH_equivalent_1us": n.OH_molecule_equivalent_1us, "neural_H2O2_equivalent_1us": n.H2O2_molecule_equivalent_1us,
            "Trp_interaction_opportunity_low": n.trp_interaction_opportunity_low, "Trp_interaction_opportunity_high": n.trp_interaction_opportunity_high,
            "thiol_interaction_opportunity_low": n.thiol_interaction_opportunity_low, "thiol_interaction_opportunity_high": n.thiol_interaction_opportunity_high,
            "experimental_dosimetry_multiplier_low": 0.5, "experimental_dosimetry_multiplier_high": 2.0,
            "mechanistic_level": n.receptor_metric_level})
    pd.DataFrame(crows).to_csv(out / "final_cannon_condition_table.csv", index=False)

    # Longitudinal all-body and surface-near deposition profiles from authoritative 100M step caches.
    profiles = []
    result_names = {"focused": "final_highstat_focused_nominal_ngm_100M", "diffuse": "final_highstat_diffuse_nominal_m9_100M"}
    edges = np.linspace(-460, 460, 47)
    for irr, result_name in result_names.items():
        base = repo / "ros_worm_stage1/results" / result_name / "anatomy_edep_v2_1"
        z = np.load(base / "edep_step_scoring_cache.npz"); ok = z["eligible"].astype(bool)
        y = z["scoreY_um"][ok]; e = z["edep_keV"][ok]; d_n = z["distance_to_nervous_surface_um"][ok]
        d_m = np.load(base / "muscle_surface_distance_cache.npz")["distance_to_muscle_surface_um"]
        if len(d_m) != len(e):
            raise SystemExit(f"{irr}: muscle-distance cache does not match eligible-step cache")
        total = e.sum()
        for label, mask in (("whole_worm", np.ones(len(e), bool)), ("within_5um_nervous_surface", d_n < 5), ("within_5um_muscle_surface", d_m < 5)):
            h, _ = np.histogram(y[mask], edges, weights=e[mask])
            for lo, hi, val in zip(edges[:-1], edges[1:], h):
                profiles.append({"irradiation": irr, "region": label, "y_low_um": lo, "y_high_um": hi,
                                 "y_center_um": (lo+hi)/2, "edep_keV": val, "whole_worm_edep_fraction": val/total})
    pd.DataFrame(profiles).to_csv(out / "longitudinal_edep_profiles.csv", index=False)

    # Operational warning and containment audit.
    qrows = []
    for irr in ("focused", "diffuse"):
        md = json.loads((vf / f"production/{irr}/edep_scoring_metadata.json").read_text())
        nw = json.loads((vf / f"production/{irr}/navigation_warning_summary.json").read_text())
        qrows.append({"irradiation": irr, "histories": md["events"], "positive_step_edep_keV": md["positive_step_edep_keV"],
                      "step_event_energy_difference_keV": md["step_minus_event_edep_keV"], "invalid_steps": md["nonfinite_steps_excluded"],
                      "outside_body_steps_excluded": md["scoring_position_outside_body_steps_excluded"],
                      "outside_body_edep_keV_excluded": md["scoring_position_outside_body_edep_keV_excluded"],
                      "outside_body_fraction_of_whole_edep": md["scoring_position_outside_body_edep_keV_excluded"] / md["positive_step_edep_keV"],
                      "navigation_warning_incidents": nw["geomnav1002_incidents"],
                      "navigation_warnings_per_history": nw["geomnav1002_incidents"] / md["events"]})
    pd.DataFrame(qrows).to_csv(out / "transport_qc_and_navigation.csv", index=False)

    meta = {"endpoint_policy": "actual Geant4 deposited energy is primary", "dose_ratio_statistics": "event-level covariance delta method and event bootstrap",
            "uncertainties_combined": False, "dosimetry_scaling": "fluence-linear nominal transport reused", "target_metric": "Level 1 chemical opportunity; not activation"}
    (out / "final_table_metadata.json").write_text(json.dumps(meta, indent=2) + "\n")


if __name__ == "__main__":
    main()
