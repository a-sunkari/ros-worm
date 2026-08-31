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
import vtk
from vtk.util.numpy_support import vtk_to_numpy


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def save_figure(fig, base: Path) -> None:
    """Write deterministic raster and vector versions of one figure."""
    fig.savefig(base.with_suffix(".png"), dpi=300, metadata={"Software": "ROS-Worm v2"})
    fig.savefig(base.with_suffix(".pdf"), metadata={
        "Creator": "ROS-Worm v2", "Producer": "Matplotlib",
        "CreationDate": None, "ModDate": None,
    })
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    stage = Path(__file__).resolve().parents[2]
    parser.add_argument("--results", type=Path, default=stage / "results")
    parser.add_argument("--outdir", type=Path, default=stage / "validation/v2")
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    figures = args.outdir / "figures"; figures.mkdir(exist_ok=True)
    compact = args.outdir / "runs"; compact.mkdir(exist_ok=True)
    rows, shell_frames, tissue_frames, sector_frames, null_frames, regional_frames = [], [], [], [], [], []
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
        regional = pd.DataFrame(summary["regions"])
        regional.insert(0, "case", manifest["case_name"])
        regional.insert(0, "run_name", run_dir.name)
        regional_frames.append(regional)
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
        for source in [manifest_path, summary_path, run_dir / "transport.mac", nav_path,
                       scoring / "anatomy_scoring_metadata.json",
                       scoring / "neural_distance_shells.csv", scoring / "neural_muscle_comparison.csv",
                       scoring / "neural_longitudinal_sectors.csv", scoring / "neural_matched_atlas_null.csv"]:
            if source.exists(): shutil.copy2(source, destination / source.name)
    runs = pd.DataFrame(rows).sort_values(["events", "case", "run_name"])
    runs.to_csv(args.outdir / "transport_run_index.csv", index=False)
    shells = pd.concat(shell_frames, ignore_index=True); shells.to_csv(args.outdir / "all_neural_distance_shells.csv", index=False)
    tissues = pd.concat(tissue_frames, ignore_index=True); tissues.to_csv(args.outdir / "all_neural_muscle_metrics.csv", index=False)
    sectors = pd.concat(sector_frames, ignore_index=True); sectors.to_csv(args.outdir / "all_longitudinal_sectors.csv", index=False)
    nulls = pd.concat(null_frames, ignore_index=True); nulls.to_csv(args.outdir / "all_neural_nulls.csv", index=False)
    regional = pd.concat(regional_frames, ignore_index=True)
    regional.to_csv(args.outdir / "all_regional_transport.csv", index=False)

    # Preserve compact evidence that the additive v2 changes did not break the
    # authoritative v1 execution path.
    v1_source = args.results / "v1_regression_after_v2_1k"
    if v1_source.exists():
        v1_compact = args.outdir / "v1_regression"; v1_compact.mkdir(exist_ok=True)
        for filename in ["run_manifest.json", "transport.mac", "transport_summary.json",
                         "navigation_warning_summary.json"]:
            source = v1_source / filename
            if source.exists(): shutil.copy2(source, v1_compact / filename)

    # Independent nominal replicates are deliberately selected by the
    # authoritative validation naming contract. Filtering only on event count
    # and spectrum would also admit the paired nominal sensitivity cases.
    one_m = runs[
        (runs.events == 1_000_000)
        & runs.run_name.str.match(r"^v2_validation_(focused|diffuse)_nominal_.*_1M_seed[123]$")
    ]
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
    fig.tight_layout(); save_figure(fig, figures / "fig00_geometry_schematic")
    # Figure 1: source spectra.
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=False)
    for ax, source, title in zip(axes, ["focused_imoxs_w_50kv", "diffuse_minix_ag_20kv"], ["Focused W, 50 kV", "Diffuse Ag, 20 kV"]):
        for variant in ["soft", "nominal", "hard"]:
            path = stage / f"config/v2/spectra/{source}_{variant}.csv"
            spectrum = pd.read_csv(path, comment="#", names=["energy", "weight"])
            ax.plot(spectrum.energy, spectrum.weight, label=variant)
        ax.set(title=title, xlabel="Photon energy (keV)", ylabel="Probability per 0.25-keV bin"); ax.legend(frameon=False)
    fig.suptitle("Physics-bracketed source ensembles (not instrument measurements)")
    fig.tight_layout(); save_figure(fig, figures / "fig01_source_spectrum_ensemble")

    # Figure 2: distance shells, production preferred.
    fig, ax = plt.subplots(figsize=(7, 4.5))
    labels = ["0–1", "1–2", "2–5", "5–10", "10–25", "25–50", ">50"]
    for case, label, color in [("focused_avoidance", "Focused", "#3366cc"), ("diffuse_paralysis", "Diffuse", "#cc6633")]:
        preferred = runs[(runs.events == runs.events.max()) & (runs.case == case)]
        if preferred.empty: preferred = one_m[one_m.case == case].head(1)
        values = shells[shells.run_name == preferred.iloc[0].run_name].fraction_of_eligible_births
        ax.plot(labels, values * 100, marker="o", label=label, color=color)
    ax.set(xlabel="Distance to nervous-system surface (µm)", ylabel="Eligible electron births (%)")
    ax.legend(frameon=False); fig.tight_layout(); save_figure(fig, figures / "fig02_neural_distance_shells")

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
    ax.legend(frameon=False); fig.tight_layout(); save_figure(fig, figures / "fig03_neural_matched_null")

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
    ax.legend(frameon=False, fontsize=8); fig.tight_layout(); save_figure(fig, figures / "fig04_neural_muscle_comparison")

    # Figure 5: modeled driver across experimental doses.
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for case, frame in dose.groupby("case"):
        ax.errorbar(frame.total_dose_Gy, frame.near5_births_conditional, yerr=frame.near5_births_MC_sd,
                    marker="o", label=case.replace("_", " "))
    ax.set(xlabel="Reported total dose (Gy)", ylabel="Modeled near-neural births (conditional)",
           title="Fluence-linear physical driver across Cannon exposure conditions")
    ax.legend(frameon=False, fontsize=8); fig.tight_layout(); save_figure(fig, figures / "fig05_experimental_dose_scaling")

    # Figure 6: navigation-warning rates.
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for i, (case, frame) in enumerate(one_m.groupby("case")):
        ax.scatter(np.full(len(frame), i), frame.navigation_warnings_per_million, label=case)
        ax.hlines(frame.navigation_warnings_per_million.mean(), i-.2, i+.2, color="black")
    ax.set_xticks(range(len(one_m.case.unique())), [name.replace("_", " ") for name in one_m.case.unique()])
    ax.set(ylabel="GeomNav1002 incidents per million histories", title="Residual non-neural boundary warnings")
    fig.tight_layout(); save_figure(fig, figures / "fig06_navigation_warnings")

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
        # Energy-budget equivalent chemistry across the experimental exposure
        # series. This assumes the summed near-neural birth kinetic energy
        # thermalizes locally in homogeneous water; it is not a concentration
        # or an intracellular molecule count.
        radiolysis_rows = []
        for _, exposure in dose.iterrows():
            condition = "Focused" if exposure["case"].startswith("focused") else "Diffuse"
            for _, chem in selected[selected.condition == condition].iterrows():
                molecule_equivalent = (exposure["near5_birth_energy_keV_conditional"]
                                       * 10.0 * chem["mean_G_molecules_per_100eV"])
                molecule_sem = (exposure["near5_birth_energy_keV_conditional"]
                                 * 10.0 * chem["standard_error_G"])
                radiolysis_rows.append({
                    "case": exposure["case"], "dose_rate_Gy_s": exposure["dose_rate_Gy_s"],
                    "exposure_s": exposure["exposure_s"], "total_dose_Gy": exposure["total_dose_Gy"],
                    "condition_spectrum": condition.lower(), "species": chem["species"],
                    "time_ns": chem["requested_time_ns"],
                    "G_molecules_per_100eV": chem["mean_G_molecules_per_100eV"],
                    "conditional_homogeneous_water_molecule_equivalent": molecule_equivalent,
                    "chemistry_SEM_molecule_equivalent": molecule_sem,
                    "assumption": "Full near-neural birth kinetic-energy budget thermalizes locally in homogeneous water; not intracellular concentration.",
                })
        pd.DataFrame(radiolysis_rows).to_csv(
            args.outdir / "experimental_condition_radiolysis_scaling.csv", index=False)
        fig,axes=plt.subplots(1,2,figsize=(10,4.5),sharey=True)
        for ax,condition in zip(axes,["Focused","Diffuse"]):
            part=selected[selected.condition==condition]
            # ASCII/mathtext-safe labels avoid missing glyphs in headless
            # publication rendering while retaining unambiguous chemistry.
            display = {"°OH^0": r"$\mathregular{OH\bullet}$", "H2O2^0": r"$\mathregular{H_2O_2}$",
                       "e_aq^-1": r"$\mathregular{e^-_{aq}}$", "H^0": r"$\mathregular{H\bullet}$"}
            for species in ["°OH^0","H2O2^0","e_aq^-1","H^0"]:
                frame=part[part.species==species]
                ax.errorbar(frame.requested_time_ns,frame.mean_G_molecules_per_100eV,yerr=frame.standard_error_G,
                            marker="o",ms=3,label=display[species])
            ax.set_xscale("log"); ax.set(title=condition,xlabel="Time (ns)",ylabel="G (molecules / 100 eV)"); ax.legend(frameon=False,fontsize=8)
        fig.suptitle("Geant4-DNA water-radiolysis time response")
        fig.tight_layout(); save_figure(fig, figures / "fig07_radiolysis_timeseries")

    # Figure 8: spatial near-neural maps and longitudinal coordinate sectors.
    fig=plt.figure(figsize=(11,8))
    grid=fig.add_gridspec(2,2,height_ratios=[1.4,1.0])
    atlas_path=stage.parent/"openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl"
    placement=pd.read_csv(stage/"config/transport_geometry_v1.csv")
    body_rel=placement[placement.safe_name=="WholeBodyEnvelope"].iloc[0].stl_path
    body_path=(stage/"config"/body_rel).resolve()
    body_reader=vtk.vtkSTLReader(); body_reader.SetFileName(str(body_path)); body_reader.Update()
    body_center=np.asarray(body_reader.GetOutput().GetBounds()).reshape(3,2).mean(axis=1)
    atlas_reader=vtk.vtkSTLReader(); atlas_reader.SetFileName(str(atlas_path)); atlas_reader.Update()
    atlas=(vtk_to_numpy(atlas_reader.GetOutput().GetPoints().GetData()).astype(float)-body_center)*0.1
    atlas=atlas[::max(1,len(atlas)//4000)]
    for j,(case,label,run_name) in enumerate([
        ("focused_avoidance","Focused","v2_production_focused_nominal_ngm_10M"),
        ("diffuse_paralysis","Diffuse","v2_production_diffuse_nominal_m9_10M")]):
        ax3=fig.add_subplot(grid[0,j],projection="3d")
        ax3.scatter(atlas[:,0],atlas[:,1],atlas[:,2],s=.3,c="#777777",alpha=.12,rasterized=True)
        scored_path=args.results/run_name/"anatomy_scoring_v2/eligible_electrons_anatomy_scored.csv"
        scored=pd.read_csv(scored_path)
        close=scored[scored.distance_to_nervous_surface_um<5]
        close=close.iloc[::max(1,len(close)//3000)]
        points=ax3.scatter(close.x_um/1000,close.y_um/1000,close.z_um/1000,c=close.ekin_keV,
                           s=3,cmap="viridis",alpha=.75,rasterized=True)
        ax3.set(xlabel="X (mm)",ylabel="Y (mm)",zlabel="Z (mm)",title=f"{label}: births <5 µm")
        ax3.set_box_aspect((1,4,1)); ax3.view_init(elev=18,azim=-58)
        fig.colorbar(points,ax=ax3,shrink=.65,pad=.08,label="Birth energy (keV)")
    ax=fig.add_subplot(grid[1,:])
    for case,label,color in [("focused_avoidance","Focused","#3366cc"),("diffuse_paralysis","Diffuse","#cc6633")]:
        preferred=runs[(runs.events==10_000_000)&(runs.case==case)]
        if preferred.empty: continue
        part=sectors[(sectors.run_name==preferred.iloc[0].run_name)&(sectors.threshold_um==5)]
        part=part.set_index("longitudinal_sector").reindex(["head_sector","anterior_sector","midbody_sector","posterior_sector","tail_sector"])
        ax.plot(["head","anterior","midbody","posterior","tail"],part.births_per_whole_worm_Gy_conditional,marker="o",label=label,color=color)
    ax.set(xlabel="Equal-length atlas Y sector",ylabel="Births within 5 µm per whole-worm Gy (conditional)",
           title="Longitudinal distribution of near-neural electron births")
    ax.legend(frameon=False); fig.suptitle("Near-neural spatial and longitudinal maps")
    # Retain the established basename so regenerated packages do not leave an
    # obsolete second Figure 8 alongside the enhanced spatial version.
    fig.tight_layout(); save_figure(fig, figures / "fig08_longitudinal_neural_sectors")

    # Figure 9: ranked exploratory sensitivity effects.
    part=sensitivity[sensitivity.metric=="near5_births_per_whole_worm_Gy_conditional"].sort_values("percent_change")
    if len(part):
        fig,ax=plt.subplots(figsize=(8,5.5)); colors=["#cc6633" if value<0 else "#3366cc" for value in part.percent_change]
        ax.barh(part.contrast,part.percent_change,color=colors); ax.axvline(0,color="black",lw=.8)
        ax.set(xlabel="Change in conditional near-neural births per Gy (%)",
               title="Paired one-at-a-time sensitivity (1M histories per case)")
        fig.tight_layout(); save_figure(fig, figures / "fig09_sensitivity_tornado")
    print(f"[OK] collected {len(runs)} runs into {args.outdir}")


if __name__ == "__main__":
    main()
