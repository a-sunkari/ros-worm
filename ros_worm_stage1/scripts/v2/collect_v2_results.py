#!/usr/bin/env python3
"""Collect compact v2 validation artifacts and make reproducible figures."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser()
    stage = Path(__file__).resolve().parents[2]
    parser.add_argument("--results", type=Path, default=stage / "results")
    parser.add_argument("--outdir", type=Path, default=stage / "validation/v2")
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    figures = args.outdir / "figures"; figures.mkdir(exist_ok=True)
    compact = args.outdir / "runs"; compact.mkdir(exist_ok=True)
    rows, shell_frames, tissue_frames, sector_frames, null_frames = [], [], [], [], []
    for run_dir in sorted(args.results.glob("v2_*")):
        manifest_path = run_dir / "run_manifest.json"
        summary_path = run_dir / "transport_summary.json"
        scoring = run_dir / "anatomy_scoring_v2"
        if not manifest_path.exists() or not summary_path.exists() or not (scoring / "anatomy_scoring_metadata.json").exists():
            continue
        manifest, summary = load_json(manifest_path), load_json(summary_path)
        anatomy = load_json(scoring / "anatomy_scoring_metadata.json")
        nav_path = run_dir / "navigation_warning_summary.json"
        if not nav_path.exists(): nav_path = run_dir / "navigation_warnings_summary.json"
        nav = load_json(nav_path) if nav_path.exists() else {"geomnav1002_incidents": np.nan}
        masses = [float(r["scoring_mass_kg"]) for r in summary["regions"] if r["scoring_mass_kg"] != ""]
        dose_per_history = summary["total_scored_edep_keV"] * 1.602176634e-16 / sum(masses) / summary["events"]
        tissue = pd.read_csv(scoring / "neural_muscle_comparison.csv")
        near = tissue[tissue.tissue_metric == "within_5um_nervous_surface"].iloc[0]
        row = {
            "run_name": run_dir.name, "case": manifest["case_name"],
            "spectrum": manifest["spectrum_variant"], "environment": manifest["environment_name"],
            "material_model": manifest.get("material_model", "tissue"),
            "beam_y_mm": manifest.get("beam_y_mm", manifest["case"]["source_position_mm"][1]),
            "spot_fwhm_mm": manifest.get("spot_fwhm_mm", manifest["case"].get("spot_fwhm_mm")),
            "environment_above_mm": manifest["environment"]["above_mm"],
            "events": summary["events"], "seed_a": manifest["random_seeds"][0], "seed_b": manifest["random_seeds"][1],
            "edep_keV_per_primary": summary["total_scored_edep_keV"] / summary["events"],
            "whole_worm_dose_Gy_per_primary": dose_per_history,
            "eligible_electrons_per_primary": anatomy["n_eligible_electrons"] / summary["events"],
            "near5_fraction": anatomy["null_model"]["real_fraction_within_5um"],
            "near5_births_per_whole_worm_Gy_conditional": near["births_per_whole_worm_Gy_conditional"],
            "near5_birth_energy_keV_per_whole_worm_Gy_conditional": near["energy_per_primary_keV"] / dose_per_history,
            "near5_mean_energy_keV": near["mean_energy_keV"],
            "null_enrichment_ratio": anatomy["null_model"]["enrichment_ratio_real_over_null_mean"],
            "null_empirical_p": anatomy["null_model"]["empirical_upper_tail_p"],
            "navigation_warnings": nav.get("geomnav1002_incidents", np.nan),
            "navigation_warnings_per_million": nav.get("geomnav1002_incidents", np.nan) / summary["events"] * 1e6,
            "excluded_nonfinite": anatomy["exclusions"]["nonfinite"],
            "excluded_recorded_outside": anatomy["exclusions"]["recorded_outside_body"],
            "excluded_geometric_outside": anatomy["exclusions"]["geometrically_outside_body"],
        }
        rows.append(row)
        for name, collection in [("neural_distance_shells.csv", shell_frames),
                                 ("neural_muscle_comparison.csv", tissue_frames),
                                 ("neural_longitudinal_sectors.csv", sector_frames),
                                 ("neural_matched_atlas_null.csv", null_frames)]:
            try:
                frame = pd.read_csv(scoring / name)
            except pd.errors.EmptyDataError:
                continue
            frame.insert(0, "run_name", run_dir.name); collection.append(frame)
        destination = compact / run_dir.name; destination.mkdir(exist_ok=True)
        for source in [manifest_path, summary_path, nav_path, scoring / "anatomy_scoring_metadata.json",
                       scoring / "neural_distance_shells.csv", scoring / "neural_muscle_comparison.csv",
                       scoring / "neural_longitudinal_sectors.csv", scoring / "neural_matched_atlas_null.csv"]:
            if source.exists(): shutil.copy2(source, destination / source.name)
    runs = pd.DataFrame(rows).sort_values(["events", "case", "run_name"])
    runs.to_csv(args.outdir / "transport_run_index.csv", index=False)
    shells = pd.concat(shell_frames, ignore_index=True); shells.to_csv(args.outdir / "all_neural_distance_shells.csv", index=False)
    tissues = pd.concat(tissue_frames, ignore_index=True); tissues.to_csv(args.outdir / "all_neural_muscle_metrics.csv", index=False)
    sectors = pd.concat(sector_frames, ignore_index=True); sectors.to_csv(args.outdir / "all_longitudinal_sectors.csv", index=False)
    nulls = pd.concat(null_frames, ignore_index=True); nulls.to_csv(args.outdir / "all_neural_nulls.csv", index=False)

    one_m = runs[(runs.events == 1_000_000) & (runs.spectrum == "nominal")]
    metrics = ["edep_keV_per_primary", "eligible_electrons_per_primary", "near5_fraction",
               "near5_births_per_whole_worm_Gy_conditional", "near5_mean_energy_keV", "navigation_warnings_per_million"]
    replicate = one_m.groupby(["case", "environment"])[metrics].agg(["mean", "std", "count"])
    replicate.columns = ["_".join(col) for col in replicate.columns]
    replicate.reset_index().to_csv(args.outdir / "replicate_summary_1M.csv", index=False)

    # Fluence-linear scaling across measured exposure conditions. This reuses
    # transport because dose rate does not change single-photon physics here.
    cases = json.loads(json.dumps(__import__("yaml").safe_load((stage / "config/v2/study_cases.yaml").read_text())["cases"]))
    dose_rows = []
    for case_name, case in cases.items():
        source_case = "focused_avoidance" if case_name.startswith("focused") else "diffuse_paralysis"
        subset = one_m[one_m.case == source_case]
        if subset.empty: continue
        driver_mean = subset.near5_births_per_whole_worm_Gy_conditional.mean()
        driver_sd = subset.near5_births_per_whole_worm_Gy_conditional.std()
        energy_mean = subset.near5_birth_energy_keV_per_whole_worm_Gy_conditional.mean()
        for rate in case["dose_rates_Gy_s"]:
            dose = rate * case["exposure_s"]
            dose_rows.append({"case": case_name, "dose_rate_Gy_s": rate, "exposure_s": case["exposure_s"],
                              "total_dose_Gy": dose,
                              "near5_births_conditional": driver_mean * dose,
                              "near5_births_MC_sd": driver_sd * dose,
                              "near5_birth_energy_keV_conditional": energy_mean * dose,
                              "interpretation": "Linear fluence scaling conditional on reported Gy equaling model whole-worm mean dose."})
    dose = pd.DataFrame(dose_rows); dose.to_csv(args.outdir / "experimental_condition_model_scaling.csv", index=False)

    # Named one-at-a-time contrasts. The source/beam/material 100k contrasts
    # are exploratory; only environment contrasts use paired 1M seeds.
    nominal = {
        "focused_100k": "v2_smoke_focused_nominal_ngm_100k",
        "diffuse_100k": "v2_smoke_diffuse_nominal_m9_100k",
        "focused_1M": "v2_validation_focused_nominal_ngm_1M_seed1",
        "diffuse_1M": "v2_validation_diffuse_nominal_m9_1M_seed1",
    }
    contrasts = [
        ("Focused: remove agar/dish", "v2_sensitivity_focused_nominal_worm_only_1M", nominal["focused_1M"], "paired 1M"),
        ("Diffuse: remove M9/glass", "v2_sensitivity_diffuse_nominal_worm_only_1M", nominal["diffuse_1M"], "paired 1M"),
        ("Focused: soft spectrum", "v2_sensitivity_focused_soft_ngm_1M", nominal["focused_1M"], "paired 1M"),
        ("Focused: hard spectrum", "v2_sensitivity_focused_hard_ngm_1M", nominal["focused_1M"], "paired 1M"),
        ("Diffuse: soft spectrum", "v2_sensitivity_diffuse_soft_m9_1M", nominal["diffuse_1M"], "paired 1M"),
        ("Diffuse: hard spectrum", "v2_sensitivity_diffuse_hard_m9_1M", nominal["diffuse_1M"], "paired 1M"),
        ("Focused: beam y -0.2 mm", "v2_sensitivity_beam_y_minus020_1M", nominal["focused_1M"], "paired 1M"),
        ("Focused: beam y +0.2 mm", "v2_sensitivity_beam_y_plus020_1M", nominal["focused_1M"], "paired 1M"),
        ("Focused: FWHM 0.65 mm", "v2_sensitivity_fwhm_065_1M", nominal["focused_1M"], "paired 1M"),
        ("Focused: FWHM 1.05 mm", "v2_sensitivity_fwhm_105_1M", nominal["focused_1M"], "paired 1M"),
        ("Diffuse: shallower M9", "v2_sensitivity_m9_above_0155_1M", nominal["diffuse_1M"], "paired 1M"),
        ("Focused: water materials", "v2_sensitivity_focused_water_materials_1M", nominal["focused_1M"], "paired 1M"),
    ]
    sensitivity_rows=[]
    for label, altered_name, reference_name, quality in contrasts:
        altered = runs[runs.run_name == altered_name]
        reference = runs[runs.run_name == reference_name]
        if altered.empty or reference.empty: continue
        for metric in ["near5_births_per_whole_worm_Gy_conditional", "near5_fraction", "near5_mean_energy_keV"]:
            a, r = float(altered.iloc[0][metric]), float(reference.iloc[0][metric])
            sensitivity_rows.append({"contrast": label, "metric": metric, "altered": a, "reference": r,
                                     "percent_change": (a/r-1)*100 if r else np.nan, "evidence_level": quality})
    sensitivity = pd.DataFrame(sensitivity_rows)
    sensitivity.to_csv(args.outdir / "sensitivity_effects.csv", index=False)

    plt.style.use("seaborn-v0_8-whitegrid")
    # Figure 0: geometry/source schematic (not to scale).
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, title, medium, source_z, color in [(axes[0], "Focused: iMOXS W, 50 kV", "NGM/agar + polystyrene dish", 1.7, "#3366cc"),
                                               (axes[1], "Diffuse: Mini-X Ag, 20 kV", "M9 drop + glass slide", 1.4, "#cc6633")]:
        ax.add_patch(plt.Rectangle((-1.2, -.55), 2.4, .35, color="#d9c49c", label=medium))
        ax.add_patch(plt.Rectangle((-1.2, -.72), 2.4, .17, color="#b8c4cc"))
        ax.add_patch(plt.matplotlib.patches.Ellipse((0, -.1), 1.7, .25, facecolor="#88c999", edgecolor="black", lw=1.2))
        ax.annotate("worm (long axis Y)", (0, -.1), ha="center", va="center", fontsize=9)
        ax.annotate("X-ray source", (0, source_z), ha="center", va="center", bbox=dict(boxstyle="round", fc="white", ec=color))
        ax.annotate("", xy=(0, .05), xytext=(0, source_z-.15), arrowprops=dict(arrowstyle="-|>", lw=3, color=color))
        ax.text(0.05, .75, "beam along −Z", color=color, fontsize=9)
        ax.text(0, -.47, medium, ha="center", fontsize=8)
        ax.set(xlim=(-1.3,1.3), ylim=(-.8,2.0), title=title); ax.axis("off")
    fig.suptitle("v2 experimental-environment model schematic (not to scale)")
    fig.tight_layout(); fig.savefig(figures / "fig00_geometry_schematic.png", dpi=300); fig.savefig(figures / "fig00_geometry_schematic.pdf"); plt.close(fig)
    # Figure 1: source spectra.
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=False)
    for ax, source, title in zip(axes, ["focused_imoxs_w_50kv", "diffuse_minix_ag_20kv"], ["Focused W, 50 kV", "Diffuse Ag, 20 kV"]):
        for variant in ["soft", "nominal", "hard"]:
            path = stage / f"config/v2/spectra/{source}_{variant}.csv"
            spectrum = pd.read_csv(path, comment="#", names=["energy", "weight"])
            ax.plot(spectrum.energy, spectrum.weight, label=variant)
        ax.set(title=title, xlabel="Photon energy (keV)", ylabel="Probability per 0.25-keV bin"); ax.legend(frameon=False)
    fig.suptitle("Physics-bracketed source ensembles (not instrument measurements)")
    fig.tight_layout(); fig.savefig(figures / "fig01_source_spectrum_ensemble.png", dpi=300); fig.savefig(figures / "fig01_source_spectrum_ensemble.pdf"); plt.close(fig)

    # Figure 2: distance shells, production preferred.
    fig, ax = plt.subplots(figsize=(7, 4.5))
    labels = ["0–1", "1–2", "2–5", "5–10", "10–25", "25–50", ">50"]
    for case, label, color in [("focused_avoidance", "Focused", "#3366cc"), ("diffuse_paralysis", "Diffuse", "#cc6633")]:
        preferred = runs[(runs.events == runs.events.max()) & (runs.case == case)]
        if preferred.empty: preferred = one_m[one_m.case == case].head(1)
        values = shells[shells.run_name == preferred.iloc[0].run_name].fraction_of_eligible_births
        ax.plot(labels, values * 100, marker="o", label=label, color=color)
    ax.set(xlabel="Distance to nervous-system surface (µm)", ylabel="Eligible electron births (%)")
    ax.legend(frameon=False); fig.tight_layout(); fig.savefig(figures / "fig02_neural_distance_shells.png", dpi=300); fig.savefig(figures / "fig02_neural_distance_shells.pdf"); plt.close(fig)

    # Figure 3: real atlas vs matched perturbations.
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    groups = []
    for case, short in [("focused_avoidance", "Focused"), ("diffuse_paralysis", "Diffuse")]:
        for _, row in one_m[one_m.case == case].iterrows():
            vals = nulls[nulls.run_name == row.run_name].fraction_within_5um.to_numpy() * 100
            groups.append((short, row.near5_fraction * 100, vals))
    x = np.arange(len(groups))
    ax.scatter(x, [g[1] for g in groups], color="black", label="Real atlas", zorder=3)
    for i, (_, _, vals) in enumerate(groups): ax.scatter(np.full(len(vals), i), vals, color="#999999", alpha=.6, s=18)
    ax.set_xticks(x, [f"{g[0]}\nseed {i%3+1}" for i, g in enumerate(groups)])
    ax.set(ylabel="Births within 5 µm (%)", title="Real neural atlas vs anatomy-preserving rigid nulls")
    ax.legend(frameon=False); fig.tight_layout(); fig.savefig(figures / "fig03_neural_matched_null.png", dpi=300); fig.savefig(figures / "fig03_neural_matched_null.pdf"); plt.close(fig)

    # Figure 4: tissue comparison normalized per Gy.
    fig, ax = plt.subplots(figsize=(7, 4.5))
    metrics_map = [("within_5um_nervous_surface", "Within 5 µm neural"),
                   ("within_5um_bodywall_surface", "Within 5 µm muscle"),
                   ("inside_bodywall_physical_compartment", "Inside muscle compartment")]
    width = .25
    for j, (metric, label) in enumerate(metrics_map):
        vals=[]; errs=[]
        for case in ["focused_avoidance", "diffuse_paralysis"]:
            run_names = one_m[one_m.case == case].run_name
            sample = tissues[(tissues.run_name.isin(run_names)) & (tissues.tissue_metric == metric)].births_per_whole_worm_Gy_conditional
            vals.append(sample.mean()); errs.append(sample.std())
        ax.bar(np.arange(2)+(j-1)*width, vals, width, yerr=errs, label=label, capsize=3)
    ax.set_xticks([0,1], ["Focused", "Diffuse"]); ax.set_ylabel("Electron births per whole-worm Gy (conditional)")
    ax.legend(frameon=False, fontsize=8); fig.tight_layout(); fig.savefig(figures / "fig04_neural_muscle_comparison.png", dpi=300); fig.savefig(figures / "fig04_neural_muscle_comparison.pdf"); plt.close(fig)

    # Figure 5: modeled driver across experimental doses.
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for case, frame in dose.groupby("case"):
        ax.errorbar(frame.total_dose_Gy, frame.near5_births_conditional, yerr=frame.near5_births_MC_sd,
                    marker="o", label=case.replace("_", " "))
    ax.set(xlabel="Reported total dose (Gy)", ylabel="Modeled near-neural births (conditional)",
           title="Fluence-linear physical driver across Cannon exposure conditions")
    ax.legend(frameon=False, fontsize=8); fig.tight_layout(); fig.savefig(figures / "fig05_experimental_dose_scaling.png", dpi=300); fig.savefig(figures / "fig05_experimental_dose_scaling.pdf"); plt.close(fig)

    # Figure 6: navigation-warning rates.
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for i, (case, frame) in enumerate(one_m.groupby("case")):
        ax.scatter(np.full(len(frame), i), frame.navigation_warnings_per_million, label=case)
        ax.hlines(frame.navigation_warnings_per_million.mean(), i-.2, i+.2, color="black")
    ax.set_xticks(range(len(one_m.case.unique())), [name.replace("_", " ") for name in one_m.case.unique()])
    ax.set(ylabel="GeomNav1002 incidents per million histories", title="Residual non-neural boundary warnings")
    fig.tight_layout(); fig.savefig(figures / "fig06_navigation_warnings.png", dpi=300); fig.savefig(figures / "fig06_navigation_warnings.pdf"); plt.close(fig)

    # Figure 7: time-resolved water radiolysis.
    chemistry_frames=[]; chemistry_out=args.outdir / "chemistry"; chemistry_out.mkdir(exist_ok=True)
    for label, dirname in [("Focused", "v2_chemistry_focused_neural_10k"), ("Diffuse", "v2_chemistry_diffuse_neural_10k")]:
        source=args.results / dirname / "species_timeseries.csv"
        if source.exists():
            frame=pd.read_csv(source); frame.insert(0,"condition",label); chemistry_frames.append(frame)
            for filename in ["species_timeseries.csv","species_summary.csv","run_manifest.json"]:
                path=args.results/dirname/filename
                if path.exists(): shutil.copy2(path, chemistry_out/f"{label.lower()}_{filename}")
    if chemistry_frames:
        chemistry=pd.concat(chemistry_frames,ignore_index=True); chemistry.to_csv(args.outdir/"chemistry_timeseries_all.csv",index=False)
        targets=np.array([.001,.01,.1,1,10,100,999.999])
        selected=[]
        for (condition,species), frame in chemistry.groupby(["condition","species"]):
            times=frame.time_ns.to_numpy(float)
            for target in targets:
                row=frame.iloc[np.argmin(np.abs(times-target))].copy(); row["requested_time_ns"]=target; selected.append(row)
        selected=pd.DataFrame(selected); selected.to_csv(args.outdir/"chemistry_reporting_times.csv",index=False)
        fig,axes=plt.subplots(1,2,figsize=(10,4.5),sharey=True)
        for ax,condition in zip(axes,["Focused","Diffuse"]):
            part=selected[selected.condition==condition]
            for species in ["°OH^0","H2O2^0","e_aq^-1","H^0"]:
                frame=part[part.species==species]
                ax.errorbar(frame.requested_time_ns,frame.mean_G_molecules_per_100eV,yerr=frame.standard_error_G,
                            marker="o",ms=3,label=species)
            ax.set_xscale("log"); ax.set(title=condition,xlabel="Time (ns)",ylabel="G (molecules / 100 eV)"); ax.legend(frameon=False,fontsize=8)
        fig.suptitle("Geant4-DNA water-radiolysis time response")
        fig.tight_layout(); fig.savefig(figures/"fig07_radiolysis_timeseries.png",dpi=300); fig.savefig(figures/"fig07_radiolysis_timeseries.pdf"); plt.close(fig)

    # Figure 8: longitudinal coordinate sectors at 5 um.
    fig,ax=plt.subplots(figsize=(7.5,4.5))
    for case,label,color in [("focused_avoidance","Focused","#3366cc"),("diffuse_paralysis","Diffuse","#cc6633")]:
        preferred=runs[(runs.events==10_000_000)&(runs.case==case)]
        if preferred.empty: continue
        part=sectors[(sectors.run_name==preferred.iloc[0].run_name)&(sectors.threshold_um==5)]
        part=part.set_index("longitudinal_sector").reindex(["head_sector","anterior_sector","midbody_sector","posterior_sector","tail_sector"])
        ax.plot(["head","anterior","midbody","posterior","tail"],part.births_per_whole_worm_Gy_conditional,marker="o",label=label,color=color)
    ax.set(xlabel="Equal-length atlas Y sector",ylabel="Births within 5 µm per whole-worm Gy (conditional)",
           title="Longitudinal distribution of near-neural electron births")
    ax.legend(frameon=False); fig.tight_layout(); fig.savefig(figures/"fig08_longitudinal_neural_sectors.png",dpi=300); fig.savefig(figures/"fig08_longitudinal_neural_sectors.pdf"); plt.close(fig)

    # Figure 9: ranked exploratory sensitivity effects.
    part=sensitivity[sensitivity.metric=="near5_births_per_whole_worm_Gy_conditional"].sort_values("percent_change")
    if len(part):
        fig,ax=plt.subplots(figsize=(8,5.5)); colors=["#cc6633" if value<0 else "#3366cc" for value in part.percent_change]
        ax.barh(part.contrast,part.percent_change,color=colors); ax.axvline(0,color="black",lw=.8)
        ax.set(xlabel="Change in conditional near-neural births per Gy (%)",
               title="One-at-a-time sensitivity (100k exploratory unless marked paired 1M)")
        fig.tight_layout(); fig.savefig(figures/"fig09_sensitivity_tornado.png",dpi=300); fig.savefig(figures/"fig09_sensitivity_tornado.pdf"); plt.close(fig)
    print(f"[OK] collected {len(runs)} runs into {args.outdir}")


if __name__ == "__main__":
    main()
