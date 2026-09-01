#!/usr/bin/env python3
"""Scale validated water G values to actual local edep and bracket target chemistry."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

EV_TO_J = 1.602176634e-19
J_PER_100_EV = 100.0 * EV_TO_J


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def choose_times(frame: pd.DataFrame) -> pd.DataFrame:
    requested = np.array([0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 999.999])
    selected = []
    for target in requested:
        actual = frame.iloc[np.abs(frame.time_ns - target).argmin()].time_ns
        selected.append(frame[frame.time_ns == actual])
    return pd.concat(selected, ignore_index=True).drop_duplicates(
        ["time_ns", "species_id"], keep="first")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--production", type=Path, required=True)
    parser.add_argument("--chemistry-results", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load(args.config.read_text())

    chemistry_frames = []
    chemistry_index = []
    regions = ("neural", "muscle", "perineural_5um")
    for irradiation in ("focused", "diffuse"):
        for region in regions:
            name = f"v2_1_chemistry_{irradiation}_{region}_edep_weighted_10k"
            source = args.chemistry_results / name
            if not source.is_dir():
                # The tracked release uses concise directory names, while the
                # ignored original result tree retains full run names.
                source = args.chemistry_results / f"{irradiation}_{region}"
            times = choose_times(pd.read_csv(source / "species_timeseries.csv"))
            times.insert(0, "analysis_region", region)
            times.insert(0, "irradiation", irradiation)
            chemistry_frames.append(times)
            manifest = json.loads((source / "run_manifest.json").read_text())
            compact = args.outdir / "runs" / f"{irradiation}_{region}"
            compact.mkdir(parents=True, exist_ok=True)
            for filename in ("species_timeseries.csv", "species_summary.csv", "run_manifest.json",
                             "electron_spectrum.csv", "chemistry.in"):
                if (source / filename).resolve() != (compact / filename).resolve():
                    shutil.copy2(source / filename, compact / filename)
            chemistry_index.append({
                "irradiation": irradiation, "analysis_region": region,
                "events": manifest["events"], "geant4_version": manifest["geant4_version"],
                "random_seeds": ":".join(map(str, manifest["random_seeds"])),
                "input_spectrum_sha256": manifest["input_spectrum_sha256"],
                "timeseries_sha256": sha256(source / "species_timeseries.csv"),
            })
    chemistry = pd.concat(chemistry_frames, ignore_index=True)
    chemistry.to_csv(args.outdir / "edep_weighted_chemistry_timeseries.csv", index=False)
    pd.DataFrame(chemistry_index).to_csv(args.outdir / "chemistry_run_index.csv", index=False)

    # Compare to the v2 birth-count spectra at the same seven reporting times.
    old = pd.read_csv(args.repo / "ros_worm_stage1/validation/v2/chemistry_reporting_times.csv")
    old = old.rename(columns={"condition": "irradiation", "tissue": "analysis_region",
                              "requested_time_ns": "report_time_ns",
                              "mean_G_molecules_per_100eV": "birth_spectrum_G",
                              "standard_error_G": "birth_spectrum_G_se"})
    old.irradiation = old.irradiation.str.lower()
    new = chemistry[chemistry.analysis_region.isin(["neural", "muscle"])].copy()
    # ROOT stores the nominal 999.999 ns point with a small binary floating
    # offset; round both sources before the paired spectrum comparison.
    new["report_time_ns"] = new.time_ns.round(6)
    old["report_time_ns"] = old.report_time_ns.round(6)
    compare = new.merge(old[["irradiation", "analysis_region", "species", "report_time_ns",
                             "birth_spectrum_G", "birth_spectrum_G_se"]],
                        on=["irradiation", "analysis_region", "species", "report_time_ns"], how="left")
    compare = compare.rename(columns={"mean_G_molecules_per_100eV": "edep_weighted_G",
                                      "standard_error_G": "edep_weighted_G_se"})
    compare["percent_change_edep_vs_birth"] = 100.0 * (
        compare.edep_weighted_G / compare.birth_spectrum_G - 1.0)
    compare.to_csv(args.outdir / "chemistry_spectrum_normalization_comparison.csv", index=False)

    dose = pd.read_csv(args.production / "production_neural_muscle_dose.csv")
    shells = pd.read_csv(args.production / "production_nervous_surface_edep_shells.csv")
    local_rows = []
    for irradiation in ("focused", "diffuse"):
        subset = dose[dose.irradiation == irradiation]
        neural = subset[subset.roi == "neural_exact_member_union_with_0.25um_mass_density_1.04"].iloc[0]
        muscle = subset[subset.roi == "physical_body_wall_muscle"].iloc[0]
        neural_candidates = subset[subset.roi.str.startswith("neural_")]
        near = shells[(shells.irradiation == irradiation) & (shells.shell_upper_um <= 5.0)]
        local_rows.extend([
            {"irradiation": irradiation, "analysis_region": "neural",
             "mass_kg": neural.mass_kg, "dose_ratio": neural.dose_ratio_roi_to_whole_worm,
             "dose_ratio_se": neural.dose_ratio_stochastic_se,
             "dose_ratio_reconstruction_low": neural_candidates.dose_ratio_roi_to_whole_worm.min(),
             "dose_ratio_reconstruction_high": neural_candidates.dose_ratio_roi_to_whole_worm.max(),
             "edep_J_per_whole_worm_Gy": neural.mass_kg * neural.dose_ratio_roi_to_whole_worm},
            {"irradiation": irradiation, "analysis_region": "muscle",
             "mass_kg": muscle.mass_kg, "dose_ratio": muscle.dose_ratio_roi_to_whole_worm,
             "dose_ratio_se": muscle.dose_ratio_stochastic_se,
             "dose_ratio_reconstruction_low": muscle.dose_ratio_roi_to_whole_worm,
             "dose_ratio_reconstruction_high": muscle.dose_ratio_roi_to_whole_worm,
             "edep_J_per_whole_worm_Gy": muscle.mass_kg * muscle.dose_ratio_roi_to_whole_worm},
            {"irradiation": irradiation, "analysis_region": "perineural_5um",
             "mass_kg": np.nan, "dose_ratio": np.nan, "dose_ratio_se": np.nan,
             "dose_ratio_reconstruction_low": np.nan, "dose_ratio_reconstruction_high": np.nan,
             "edep_J_per_whole_worm_Gy": near.edep_keV_per_whole_worm_Gy.sum() * 1.602176634e-16},
        ])
    local = pd.DataFrame(local_rows)
    local.to_csv(args.outdir / "local_edep_per_whole_worm_Gy.csv", index=False)

    exposure_rows = []
    molecule_rows = []
    for condition in config["cannon_conditions"]:
        whole_dose = condition["dose_rate_Gy_s"] * condition["exposure_s"]
        for region in regions:
            metric = local[(local.irradiation == condition["irradiation"]) &
                           (local.analysis_region == region)].iloc[0]
            local_edep = whole_dose * metric.edep_J_per_whole_worm_Gy
            local_dose = whole_dose * metric.dose_ratio if np.isfinite(metric.dose_ratio) else np.nan
            exposure_rows.append({**condition, "reported_total_dose_Gy": whole_dose,
                                  "analysis_region": region, "local_dose_Gy": local_dose,
                                  "dose_ratio_to_whole_worm": metric.dose_ratio,
                                  "dose_ratio_stochastic_se": metric.dose_ratio_se,
                                  "dose_ratio_reconstruction_low": metric.dose_ratio_reconstruction_low,
                                  "dose_ratio_reconstruction_high": metric.dose_ratio_reconstruction_high,
                                  "local_edep_J": local_edep,
                                  "dosimetry_low_local_edep_J": local_edep * config["experimental_dosimetry_uncertainty"]["multiplicative_low"],
                                  "dosimetry_high_local_edep_J": local_edep * config["experimental_dosimetry_uncertainty"]["multiplicative_high"]})
            chem = chemistry[(chemistry.irradiation == condition["irradiation"]) &
                             (chemistry.analysis_region == region)]
            for row in chem.itertuples():
                molecules = local_edep / J_PER_100_EV * row.mean_G_molecules_per_100eV
                molecule_rows.append({
                    **condition, "reported_total_dose_Gy": whole_dose,
                    "analysis_region": region, "local_edep_J": local_edep,
                    "time_ns": row.time_ns, "species": row.species,
                    "G_molecules_per_100eV": row.mean_G_molecules_per_100eV,
                    "G_standard_error": row.standard_error_G,
                    "homogeneous_water_molecule_equivalent": molecules,
                    "chemistry_only_standard_error_molecules": local_edep / J_PER_100_EV * row.standard_error_G,
                    "interpretation": "Molecule-equivalent production from actual local edep and homogeneous-water G value; not measured tissue concentration.",
                })
    exposure = pd.DataFrame(exposure_rows)
    molecules = pd.DataFrame(molecule_rows)
    exposure.to_csv(args.outdir / "cannon_condition_local_dose_edep.csv", index=False)
    molecules.to_csv(args.outdir / "cannon_condition_edep_radiolysis.csv", index=False)

    # Level-1 radical capture opportunity. This is deliberately a concentration
    # and background-scavenging sweep, not a receptor response model.
    opportunities = []
    initial = molecules[np.isclose(molecules.time_ns, 0.001)]
    for reaction in config["radical_target_reactions"]:
        species = initial[initial.species == reaction["radiolysis_species"]]
        k = float(reaction["rate_M-1_s-1"])
        for concentration in config["uncertain_effective_target_concentrations_M"]:
            concentration = float(concentration)
            for background in config["uncertain_background_radical_scavenging_s-1"]:
                background = float(background)
                fraction = k * concentration / (k * concentration + background)
                for row in species.itertuples():
                    opportunities.append({
                        "condition": row.condition, "irradiation": row.irradiation,
                        "analysis_region": row.analysis_region,
                        "target_class": reaction["target_class"], "reaction_key": reaction["key"],
                        "rate_M-1_s-1": k, "effective_target_concentration_M": concentration,
                        "background_scavenging_s-1": background, "capture_fraction": fraction,
                        "initial_radical_molecule_equivalent": row.homogeneous_water_molecule_equivalent,
                        "target_interaction_opportunity": row.homogeneous_water_molecule_equivalent * fraction,
                        "interpretation": "Chemical-opportunity estimate; not site-specific modification, receptor activation, or channel gating.",
                    })
    opportunities = pd.DataFrame(opportunities)
    opportunities.to_csv(args.outdir / "lite1_target_interaction_sweep.csv", index=False)

    # H2O2 molecule-time integral from 1 ps to 1 us, followed by a PRDX-like
    # encounter-capacity sweep. No biological clearance or replenishment is present.
    h2o2 = molecules[molecules.species == config["h2o2_relay"]["species"]].sort_values(
        ["condition", "analysis_region", "time_ns"])
    auc_rows = []
    for (condition, region), frame in h2o2.groupby(["condition", "analysis_region"]):
        time_s = frame.time_ns.to_numpy() * 1e-9
        values = frame.homogeneous_water_molecule_equivalent.to_numpy()
        auc = float(np.trapezoid(values, time_s))
        base = frame.iloc[-1]
        for k in config["h2o2_relay"]["rate_M-1_s-1_range"] + [config["h2o2_relay"]["representative_rate_M-1_s-1"]]:
            k = float(k)
            for concentration in config["uncertain_effective_target_concentrations_M"]:
                concentration = float(concentration)
                auc_rows.append({
                    "condition": condition, "irradiation": base.irradiation,
                    "analysis_region": region, "h2o2_molecule_second_integral_1ps_to_1us": auc,
                    "prdx_like_rate_M-1_s-1": k, "effective_target_concentration_M": concentration,
                    "prdx_like_encounter_opportunity": auc * k * concentration,
                    "interpretation": "No-sink H2O2 encounter capacity over spur time; not a direct LITE-1 reaction or biological exposure integral.",
                })
    pd.DataFrame(auc_rows).drop_duplicates().to_csv(args.outdir / "h2o2_prdx_opportunity_sweep.csv", index=False)

    # Compact Cannon table with explicit ranges over unknown target/scavenger inputs.
    final_rows = []
    at_1us = molecules[np.isclose(molecules.time_ns, 999.999)]
    for condition in exposure.condition.unique():
        for region in ("neural", "muscle"):
            d = exposure[(exposure.condition == condition) & (exposure.analysis_region == region)].iloc[0]
            c = at_1us[(at_1us.condition == condition) & (at_1us.analysis_region == region)]
            o = opportunities[(opportunities.condition == condition) &
                              (opportunities.analysis_region == region)]
            get_species = lambda name: float(c[c.species == name].homogeneous_water_molecule_equivalent.iloc[0])
            final_rows.append({
                "condition": condition, "irradiation": d.irradiation, "phenotype": d.phenotype,
                "dose_rate_Gy_s": d.dose_rate_Gy_s, "exposure_s": d.exposure_s,
                "reported_total_dose_Gy": d.reported_total_dose_Gy,
                "analysis_region": region, "modeled_local_dose_Gy": d.local_dose_Gy,
                "dose_ratio_to_whole_worm": d.dose_ratio_to_whole_worm,
                "dose_ratio_stochastic_se": d.dose_ratio_stochastic_se,
                "dose_ratio_reconstruction_low": d.dose_ratio_reconstruction_low,
                "dose_ratio_reconstruction_high": d.dose_ratio_reconstruction_high,
                "OH_molecule_equivalent_1us": get_species("°OH^0"),
                "H2O2_molecule_equivalent_1us": get_species("H2O2^0"),
                "trp_interaction_opportunity_low": o[o.target_class == "tryptophan_like"].target_interaction_opportunity.min(),
                "trp_interaction_opportunity_high": o[o.target_class == "tryptophan_like"].target_interaction_opportunity.max(),
                "thiol_interaction_opportunity_low": o[o.target_class == "cysteine_thiol_like"].target_interaction_opportunity.min(),
                "thiol_interaction_opportunity_high": o[o.target_class == "cysteine_thiol_like"].target_interaction_opportunity.max(),
                "experimental_dose_interval_factor": "0.5x-2x",
                "receptor_metric_level": "Level 1 chemical opportunity only",
            })
    pd.DataFrame(final_rows).to_csv(args.outdir / "cannon_condition_summary.csv", index=False)

    (args.outdir / "analysis_metadata.json").write_text(json.dumps({
        "schema_version": 1,
        "config": str(args.config.resolve()), "config_sha256": sha256(args.config),
        "normalization": "actual local deposited energy multiplied by Geant4-DNA homogeneous-water G values",
        "primary_chemistry_spectrum": "local electron deposited-energy-weighted pre-step kinetic-energy spectrum",
        "comparison": "v2 electron-birth-count spectrum",
        "direct_track_chemistry_gate": "not attempted: condensed-history transport does not retain nanometre track states required for faithful continuation",
        "lite1_evidence_level": config["evidence_level"],
        "lite1_decision": config["decision"],
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
