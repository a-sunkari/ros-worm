#!/usr/bin/env python3
"""Generate the ten authoritative static ROS-Worm v2.1 figures."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch
import numpy as np
import pandas as pd
import vtk
from vtk.util.numpy_support import vtk_to_numpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from neural_roi import SparseVoxelROI  # noqa: E402

COLORS = {"focused": "#1f77b4", "diffuse": "#d95f02", "neural": "#4c78a8",
          "muscle": "#e45756", "model": "#4c78a8", "exploratory": "#f2a541",
          "observed": "#3a7d44", "unsupported": "#b8b8b8"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save(fig: plt.Figure, outdir: Path, stem: str, title: str, records: list[dict]) -> None:
    fig.suptitle(title, x=0.02, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    paths = []
    for suffix in ("png", "pdf"):
        path = outdir / f"{stem}.{suffix}"
        fig.savefig(path, dpi=350 if suffix == "png" else None, bbox_inches="tight")
        paths.append(path)
    plt.close(fig)
    records.append({"figure": stem, "title": title,
                    **{p.suffix.lstrip(".") + "_sha256": sha256(p) for p in paths}})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    mpl.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.5, "axes.labelsize": 9,
        "axes.titlesize": 9.5, "legend.fontsize": 7.5, "xtick.labelsize": 8,
        "ytick.labelsize": 8, "axes.spines.top": False, "axes.spines.right": False,
        "savefig.facecolor": "white", "figure.facecolor": "white",
    })
    records: list[dict] = []
    prod = args.validation / "production"
    chem_dir = args.validation / "chemistry"
    convergence = pd.read_csv(args.validation / "neural_roi/neural_roi_resolution_convergence.csv")
    dose = pd.read_csv(prod / "production_neural_muscle_dose.csv")
    shells = pd.read_csv(prod / "production_nervous_surface_edep_shells.csv")

    # 1. Original surface vs accepted high-resolution analysis ROI.
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(args.repo / "openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl"))
    reader.Update()
    atlas = vtk_to_numpy(reader.GetOutput().GetPoints().GetData()).astype(float) * 100.0
    roi_path = args.validation / "neural_roi/neural_roi_union_members_pitch_0.25um.npz"
    roi_npz = np.load(roi_path)
    roi = SparseVoxelROI.load(roi_path)
    roi_points = roi.centers(roi_npz["boundary_flat_indices"])
    atlas = atlas[::max(1, len(atlas) // 65_000)]
    roi_points = roi_points[::max(1, len(roi_points) // 65_000)]
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 5.5), sharex=True)
    for ax, dim, label in [(axes[0], 0, "transverse X (µm)"), (axes[1], 2, "transverse Z (µm)")]:
        ax.scatter(atlas[:, 1], atlas[:, dim], s=0.18, c="#555555", alpha=0.22,
                   rasterized=True, label="original high-resolution surface")
        ax.scatter(roi_points[:, 1], roi_points[:, dim], s=0.18, c="#1f77b4", alpha=0.24,
                   rasterized=True, label="0.25 µm union-ROI boundary")
        ax.set_ylabel(label); ax.grid(alpha=0.15)
    axes[1].set_xlabel("longitudinal Y (µm)")
    axes[0].legend(loc="upper right", markerscale=12)
    save(fig, args.outdir, "fig01_surface_vs_implicit_roi",
         "Original nervous atlas and accepted analysis-only neural ROI", records)

    # 2. Volume and geometric convergence.
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))
    axes[0].plot(convergence.pitch_um, convergence.volume_um3, "o-", color=COLORS["neural"])
    axes[0].axhspan(convergence.volume_um3.min(), convergence.volume_um3.max(), color=COLORS["neural"], alpha=0.10)
    axes[0].set(xscale="log", xlabel="voxel pitch (µm)", ylabel="body-clipped neural volume (µm³)")
    axes[0].set_xticks(convergence.pitch_um, [f"{v:g}" for v in convergence.pitch_um]); axes[0].grid(alpha=0.2)
    axes[1].plot(convergence.pitch_um, convergence.surface_error_p50_um, "o-", label="p50")
    axes[1].plot(convergence.pitch_um, convergence.surface_error_p95_um, "o-", label="p95")
    axes[1].plot(convergence.pitch_um, convergence.surface_error_p99_um, "o-", label="p99")
    axes[1].set(xscale="log", yscale="log", xlabel="voxel pitch (µm)", ylabel="symmetric surface error (µm)")
    axes[1].set_xticks(convergence.pitch_um, [f"{v:g}" for v in convergence.pitch_um]); axes[1].legend(); axes[1].grid(alpha=0.2)
    save(fig, args.outdir, "fig02_neural_roi_convergence",
         "Neural-volume and surface-error convergence", records)

    # 3. Actual deposited energy vs atlas-surface distance.
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    labels = shells[shells.irradiation == "focused"].shell_label.tolist()
    x = np.arange(len(labels)); width = 0.36
    for offset, irradiation in [(-width / 2, "focused"), (width / 2, "diffuse")]:
        frame = shells[shells.irradiation == irradiation]
        ax.bar(x + offset, 100 * frame.whole_worm_edep_fraction, width,
               yerr=100 * frame.whole_worm_edep_fraction_se, capsize=2,
               color=COLORS[irradiation], label=irradiation.capitalize())
    ax.set(xticks=x, xticklabels=labels, xlabel="distance from original nervous surface (µm)",
           ylabel="whole-worm deposited energy (%)")
    ax.legend(); ax.grid(axis="y", alpha=0.2)
    save(fig, args.outdir, "fig03_edep_vs_neural_distance",
         "Nervous-surface-referenced deposited energy", records)

    # 4. Dose convergence by voxel pitch plus exact-member result.
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.3), sharey=True)
    for ax, irradiation in zip(axes, ("focused", "diffuse")):
        frame = dose[(dose.irradiation == irradiation) & dose.roi.str.match(r"neural_voxel_")].sort_values("pitch_um")
        ax.errorbar(frame.pitch_um, frame.dose_ratio_roi_to_whole_worm,
                    yerr=frame.dose_ratio_stochastic_se, fmt="o-", capsize=3, color=COLORS[irradiation], label="voxel ROI")
        exact = dose[(dose.irradiation == irradiation) &
                     (dose.roi == "neural_exact_member_union_with_0.25um_mass_density_1.04")].iloc[0]
        ax.axhline(exact.dose_ratio_roi_to_whole_worm, color="#333333", ls="--", label="exact member union")
        ax.fill_between([0.2, 2.3], exact.dose_ratio_roi_to_whole_worm - exact.dose_ratio_stochastic_se,
                        exact.dose_ratio_roi_to_whole_worm + exact.dose_ratio_stochastic_se,
                        color="#555555", alpha=0.10)
        ax.axhline(1, color="#888888", lw=0.8, ls=":")
        ax.set(xscale="log", xlim=(0.2, 2.3), xlabel="voxel pitch (µm)", title=irradiation.capitalize())
        ax.set_xticks(frame.pitch_um, [f"{v:g}" for v in frame.pitch_um]); ax.grid(alpha=0.2)
    axes[0].set_ylabel("neural dose / whole-worm mean dose")
    axes[0].legend(loc="best")
    save(fig, args.outdir, "fig04_neural_dose_convergence",
         "Neural dose convergence across analysis-only ROI definitions", records)

    # 5. Neural vs muscle on the same dose basis.
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    rows = []
    for irradiation in ("focused", "diffuse"):
        for region, roi_name in [("neural", "neural_exact_member_union_with_0.25um_mass_density_1.04"),
                                 ("muscle", "physical_body_wall_muscle")]:
            r = dose[(dose.irradiation == irradiation) & (dose.roi == roi_name)].iloc[0]
            rows.append((irradiation, region, r.dose_ratio_roi_to_whole_worm, r.dose_ratio_stochastic_se))
    x = np.arange(2); width = 0.34
    for j, region in enumerate(("neural", "muscle")):
        vals = [r for r in rows if r[1] == region]
        ax.bar(x + (j - .5) * width, [r[2] for r in vals], width,
               yerr=[r[3] for r in vals], capsize=3, color=COLORS[region], label=region.capitalize())
    ax.axhline(1, color="#555555", ls="--", lw=0.9)
    ax.set(xticks=x, xticklabels=["Focused", "Diffuse"], ylabel="regional dose / whole-worm mean dose")
    ax.legend(); ax.grid(axis="y", alpha=0.2)
    save(fig, args.outdir, "fig05_neural_vs_muscle_dose",
         "Neural and body-wall-muscle absorbed dose", records)

    # 6. Cannon exposure condition to regional dose.
    condition = pd.read_csv(chem_dir / "cannon_condition_summary.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.5), sharey=True)
    for ax, irradiation in zip(axes, ("focused", "diffuse")):
        frame = condition[condition.irradiation == irradiation]
        for region in ("neural", "muscle"):
            part = frame[frame.analysis_region == region].sort_values("reported_total_dose_Gy")
            ax.plot(part.reported_total_dose_Gy, part.modeled_local_dose_Gy, "o-",
                    color=COLORS[region], label=region.capitalize())
        maximum = frame.reported_total_dose_Gy.max()
        ax.plot([0, maximum], [0, maximum], color="#777777", ls="--", lw=0.8, label="whole-worm mean")
        ax.set(xlabel="reported total dose (Gy)", title=irradiation.capitalize()); ax.grid(alpha=0.2)
    axes[0].set_ylabel("modeled regional dose (Gy)"); axes[0].legend()
    save(fig, args.outdir, "fig06_cannon_condition_neural_dose",
         "Cannon exposure conditions mapped to regional dose", records)

    # 7. Local edep to water-radiolysis species over spur time.
    radiolysis = pd.read_csv(chem_dir / "cannon_condition_edep_radiolysis.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.5), sharey=True)
    for ax, irradiation in zip(axes, ("focused", "diffuse")):
        first_condition = radiolysis[radiolysis.irradiation == irradiation].condition.iloc[0]
        subset = radiolysis[(radiolysis.condition == first_condition) &
                            radiolysis.species.isin(["°OH^0", "H2O2^0"])]
        for region, ls in [("neural", "-"), ("muscle", "--")]:
            for species, color in [("°OH^0", "#7b3294"), ("H2O2^0", "#008837")]:
                part = subset[(subset.analysis_region == region) & (subset.species == species)].sort_values("time_ns")
                y = part.homogeneous_water_molecule_equivalent / part.reported_total_dose_Gy
                label = f"{region}, {'OH radical' if species == '°OH^0' else 'H₂O₂'}"
                ax.plot(part.time_ns, y, marker="o", ms=2.5, ls=ls, color=color, label=label)
        ax.set(xscale="log", yscale="log", xlabel="time after an energy-deposition spur (ns)", title=irradiation.capitalize())
        ax.grid(alpha=0.2, which="both")
    axes[0].set_ylabel("homogeneous-water molecule equivalents\nper reported whole-worm Gy")
    axes[0].legend(ncol=2, fontsize=6.8)
    save(fig, args.outdir, "fig07_edep_radiolysis_timeseries",
         "Deposited-energy-normalized water radiolysis", records)

    # 8. Level-1 target interaction sweep.
    interactions = pd.read_csv(chem_dir / "lite1_target_interaction_sweep.csv")
    subset = interactions[(interactions.condition == "focused_avoidance_0p2") &
                          (interactions.analysis_region == "neural")]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), sharey=True)
    for ax, target, label in zip(axes, ("tryptophan_like", "cysteine_thiol_like"),
                                 ("Trp-like", "thiol-like")):
        frame = subset[subset.target_class == target].copy()
        frame["per_Gy"] = frame.target_interaction_opportunity / 2.0
        pivot = frame.pivot(index="effective_target_concentration_M",
                            columns="background_scavenging_s-1", values="per_Gy")
        image = ax.imshow(np.log10(pivot.to_numpy()), aspect="auto", origin="lower", cmap="viridis")
        ax.set_xticks(range(len(pivot.columns)), [f"10$^{{{int(np.log10(v))}}}$" for v in pivot.columns])
        ax.set_yticks(range(len(pivot.index)), [f"{1e6*v:g}" for v in pivot.index])
        ax.set(xlabel="background scavenging (s⁻¹)", title=label)
        fig.colorbar(image, ax=ax, label="log₁₀ interaction opportunity / Gy")
    axes[0].set_ylabel("effective target concentration (µM)")
    save(fig, args.outdir, "fig08_lite1_target_opportunity",
         "Literature-rate target-interaction opportunities (Level 1)", records)

    # 9. Sensitivity effects and major neural-dose assumption intervals.
    effects = pd.read_csv(args.validation / "sensitivity/corrected_sensitivity_effects.csv")
    effects = effects[effects.metric == "perineural_0_5um_edep_fraction"].copy()
    effects["label"] = effects.irradiation.str[0].str.upper() + ": " + effects.variation.str.replace("_", " ")
    effects = effects.sort_values("percent_change")
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 4.3))
    axes[0].barh(effects.label, effects.percent_change,
                 color=[COLORS[v] for v in effects.irradiation])
    axes[0].axvline(0, color="#333333", lw=0.8)
    axes[0].set_xlabel("change in 0–5 µm edep fraction (%)"); axes[0].grid(axis="x", alpha=0.2)
    focused_exact = dose[(dose.irradiation == "focused") &
                         (dose.roi == "neural_exact_member_union_with_0.25um_mass_density_1.04")].iloc[0]
    base = focused_exact.dose_ratio_roi_to_whole_worm
    voxel = dose[(dose.irradiation == "focused") & dose.roi.str.startswith("neural_")]
    registration = pd.read_csv(prod / "focused/controls_full_registration/neural_roi_registration_sensitivity.csv")
    position = pd.read_csv(prod / "focused/edep_position_assignment_sensitivity.csv")
    intervals = [
        ("experimental dosimetry", -50.0, 100.0),
        ("atlas registration", 100 * (registration.edep_ratio_to_baseline.min() - 1),
         100 * (registration.edep_ratio_to_baseline.max() - 1)),
        ("event statistics (95%)", -100 * 1.96 * focused_exact.dose_ratio_stochastic_se / base,
         100 * 1.96 * focused_exact.dose_ratio_stochastic_se / base),
        ("ROI/density definitions", 100 * (voxel.dose_ratio_roi_to_whole_worm.min() / base - 1),
         100 * (voxel.dose_ratio_roi_to_whole_worm.max() / base - 1)),
        ("step position assignment", 100 * (position.edep_ratio_to_v2_1_hybrid.min() - 1),
         100 * (position.edep_ratio_to_v2_1_hybrid.max() - 1)),
    ]
    for i, (label, low, high) in enumerate(intervals):
        axes[1].plot([low, high], [i, i], lw=5, solid_capstyle="round", color=COLORS["model"])
        axes[1].plot(0, i, "|", color="white", ms=10, mew=1.5)
    axes[1].set_yticks(range(len(intervals)), [x[0] for x in intervals])
    axes[1].axvline(0, color="#333333", lw=0.8)
    axes[1].set_xlabel("focused neural-dose relative interval (%)"); axes[1].grid(axis="x", alpha=0.2)
    axes[1].invert_yaxis()
    save(fig, args.outdir, "fig09_sensitivity_uncertainty",
         "Sensitivity tests and dominant assumption intervals", records)

    # 10. Mechanistic ladder with evidence status encoded.
    fig, ax = plt.subplots(figsize=(10.0, 2.8)); ax.set_axis_off()
    nodes = [
        ("Cannon X-ray\nexposure", "observed"),
        ("secondary-electron\ntransport", "model"),
        ("local energy\ndeposition", "model"),
        ("water\nradiolysis", "model"),
        ("Trp/redox interaction\nopportunity", "exploratory"),
        ("LITE-1 channel\ngating", "unsupported"),
        ("behavioral\nphenotype", "observed"),
    ]
    xs = np.linspace(0.06, 0.94, len(nodes)); y = 0.52
    for i, ((text, status), x) in enumerate(zip(nodes, xs)):
        box = FancyBboxPatch((x - 0.062, y - 0.16), 0.124, 0.32,
                             boxstyle="round,pad=0.012,rounding_size=0.02",
                             transform=ax.transAxes, facecolor=COLORS[status], edgecolor="none",
                             alpha=0.92 if status != "unsupported" else 0.75)
        ax.add_patch(box); ax.text(x, y, text, transform=ax.transAxes, ha="center", va="center",
                                  color="white" if status != "unsupported" else "#333333", fontsize=7.6,
                                  fontweight="bold")
        if i < len(nodes) - 1:
            next_status = nodes[i + 1][1]
            hypothetical = status in ("exploratory", "unsupported") or next_status == "unsupported"
            ax.annotate("", xy=(xs[i + 1] - 0.068, y), xytext=(x + 0.068, y), xycoords=ax.transAxes,
                        arrowprops=dict(arrowstyle="->", lw=1.5,
                                        linestyle="--" if hypothetical else "-",
                                        color=COLORS["exploratory"] if hypothetical else COLORS["model"]))
    ax.legend(handles=[Patch(color=COLORS["observed"], label="experimentally observed"),
                       Patch(color=COLORS["model"], label="model-supported"),
                       Patch(color=COLORS["exploratory"], label="exploratory chemical opportunity"),
                       Patch(color=COLORS["unsupported"], label="not quantitatively modeled")],
              loc="lower center", bbox_to_anchor=(0.5, 0.04), ncol=4, frameon=False)
    save(fig, args.outdir, "fig10_mechanistic_ladder",
         "Mechanistic ladder and evidentiary boundary", records)

    source_files = [
        args.validation / "neural_roi/neural_roi_resolution_convergence.csv",
        prod / "production_neural_muscle_dose.csv",
        prod / "production_nervous_surface_edep_shells.csv",
        chem_dir / "cannon_condition_summary.csv",
        chem_dir / "cannon_condition_edep_radiolysis.csv",
        chem_dir / "lite1_target_interaction_sweep.csv",
        args.validation / "sensitivity/corrected_sensitivity_effects.csv",
    ]
    manifest = {"schema_version": 1, "figures": records,
                "source_hashes": {str(path): sha256(path) for path in source_files}}
    (args.outdir / "figure_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
