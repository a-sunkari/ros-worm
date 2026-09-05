#!/usr/bin/env python3
"""Regenerate the authoritative six main and two supplementary paper figures."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse, Polygon, Rectangle
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publication_style import (COLORS, DOUBLE_COLUMN_IN, apply_publication_style,
                               light_grid, panel_label, save_figure, sha256)

def read_spectrum(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, comment="#", names=["energy_keV", "probability"])


def sampled_vertices(path: Path, maximum: int) -> np.ndarray:
    mesh = trimesh.load_mesh(path, force="mesh", process=False)
    vertices = np.asarray(mesh.vertices, dtype=float)
    if len(vertices) > maximum:
        vertices = vertices[np.linspace(0, len(vertices) - 1, maximum, dtype=int)]
    return vertices


def sparse_boundary_centers(path: Path) -> np.ndarray:
    """Load precomputed ROI boundary centers without importing the VTK analysis stack."""
    data = np.load(path)
    flat = data["boundary_flat_indices"].astype(np.int64)
    dimensions = data["dimensions"].astype(np.int64)
    pitch_um = float(data["pitch_um"])
    origin_edge_um = data["origin_edge_um"].astype(float)
    nx, ny, _ = dimensions
    iz = flat // (nx * ny)
    remainder = flat - iz * nx * ny
    iy = remainder // nx
    ix = remainder - iy * nx
    return origin_edge_um + (np.column_stack([ix, iy, iz]) + 0.5) * pitch_um


def anatomy_data(repo: Path) -> dict[str, np.ndarray]:
    geometry = repo / "openworm_geometry/compartment_pipeline"
    body = sampled_vertices(
        geometry / "non_nervous_priority_bake/debug_simple_safe_body_envelope_ellipsoid.stl", 22_000
    ) * 100.0
    muscle = sampled_vertices(
        geometry / "non_nervous_priority_bake/voxel_remesh_wu_like/BodyWallMuscle_voxel_0.020.stl", 32_000
    ) * 100.0
    atlas = sampled_vertices(
        geometry / "baked_priority_meshes_test/NervousSystem_baked_union.stl", 75_000
    ) * 100.0
    roi_path = repo / "ros_worm_stage1/validation/v2_1/neural_roi/neural_roi_union_members_pitch_0.25um.npz"
    boundary = sparse_boundary_centers(roi_path)
    if len(boundary) > 75_000:
        boundary = boundary[np.linspace(0, len(boundary) - 1, 75_000, dtype=int)]
    return {"body": body, "muscle": muscle, "atlas": atlas, "roi": boundary}


def draw_setup(ax, kind: str) -> None:
    ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis("off")
    focused = kind == "focused"
    source_color = COLORS["focused"] if focused else COLORS["diffuse"]
    ax.add_patch(Rectangle((0.42, 0.80), 0.16, 0.07, facecolor="white",
                           edgecolor=COLORS["text"], linewidth=0.65))
    ax.text(0.50, 0.835, "W target, 50 kV" if focused else "Ag target, 20 kV",
            ha="center", va="center", fontsize=6.2)
    if focused:
        beam = Polygon([[0.47, 0.80], [0.53, 0.80], [0.66, 0.25], [0.34, 0.25]],
                       closed=True, facecolor=source_color, alpha=0.12,
                       edgecolor=source_color, linewidth=0.75)
        medium_y, medium_h = 0.15, 0.10
        ax.text(0.50, 0.29, "0.85 mm FWHM", ha="center", color=source_color, fontsize=6)
        ax.text(0.70, 0.55, "50 mm", ha="left", va="center", fontsize=6.2)
        ax.annotate("", xy=(0.68, 0.79), xytext=(0.68, 0.25),
                    arrowprops=dict(arrowstyle="|-|", lw=0.55, color=COLORS["text"]))
        medium_label, substrate_label = "3 mm NGM/agar", "1 mm polystyrene"
    else:
        beam = Polygon([[0.48, 0.80], [0.52, 0.80], [0.88, 0.25], [0.12, 0.25]],
                       closed=True, facecolor=source_color, alpha=0.10,
                       edgecolor=source_color, linewidth=0.75)
        medium_y, medium_h = 0.15, 0.10
        ax.text(0.50, 0.48, "120° cone", ha="center", color=source_color, fontsize=6)
        ax.text(0.70, 0.55, "10 mm", ha="left", va="center", fontsize=6.2)
        ax.annotate("", xy=(0.68, 0.79), xytext=(0.68, 0.25),
                    arrowprops=dict(arrowstyle="|-|", lw=0.55, color=COLORS["text"]))
        medium_label, substrate_label = "≤0.5 mm M9", "1 mm glass"
    ax.add_patch(beam)
    ax.add_patch(Rectangle((0.08, medium_y), 0.84, medium_h,
                           facecolor="#DCEAF2", edgecolor="#7C9DB0", linewidth=0.55))
    ax.add_patch(Rectangle((0.08, 0.10), 0.84, 0.05,
                           facecolor="#E5E5E5", edgecolor="#888888", linewidth=0.55))
    ax.add_patch(Ellipse((0.50, 0.25), 0.26, 0.035, facecolor="#6F6F6F",
                         edgecolor="none", zorder=5))
    ax.text(0.12, medium_y + medium_h / 2, medium_label, va="center", fontsize=5.9)
    ax.text(0.12, 0.125, substrate_label, va="center", fontsize=5.9)
    ax.text(0.50, 0.925, "Focused configuration" if focused else "Diffuse configuration",
            ha="center", va="center", fontsize=7, fontweight="semibold")


def figure1(repo: Path, anatomy: dict[str, np.ndarray], outdir: Path) -> dict:
    fig = plt.figure(figsize=(DOUBLE_COLUMN_IN, 5.15), layout="constrained")
    gs = fig.add_gridspec(2, 2, height_ratios=[0.92, 1.08], hspace=0.08, wspace=0.10)
    a = fig.add_subplot(gs[0, 0]); b = fig.add_subplot(gs[0, 1])
    c = fig.add_subplot(gs[1, 0])
    d = fig.add_subplot(gs[1, 1])
    draw_setup(a, "focused"); draw_setup(b, "diffuse")
    panel_label(a, "a", x=-0.05, y=1.00); panel_label(b, "b", x=-0.05, y=1.00)

    spectra = repo / "ros_worm_stage1/config/v2/spectra"
    for prefix, color, label in [
        ("focused_imoxs_w_50kv", COLORS["focused"], "Focused W, 50 kV"),
        ("diffuse_minix_ag_20kv", COLORS["diffuse"], "Diffuse Ag, 20 kV"),
    ]:
        variants = {v: read_spectrum(spectra / f"{prefix}_{v}.csv") for v in ("soft", "nominal", "hard")}
        x = variants["nominal"].energy_keV.to_numpy()
        values = np.vstack([variants[v].probability.to_numpy() for v in ("soft", "nominal", "hard")])
        c.fill_between(x, values.min(axis=0), values.max(axis=0), color=color, alpha=0.14,
                       linewidth=0,
                       label="Soft-hard spectral bracket" if prefix.startswith("focused") else None)
        c.plot(x, values[1], color=color, lw=1.05, label=label)
    c.set(xlabel="Photon energy (keV)", ylabel="Probability per 0.25 keV bin",
          yscale="log", xlim=(1, 50), ylim=(1e-5, 0.3))
    c.legend(loc="upper right")
    light_grid(c, "y"); panel_label(c, "c")

    body, muscle, atlas = anatomy["body"], anatomy["muscle"], anatomy["atlas"]
    d.scatter(body[:, 1], body[:, 0], s=0.08, color=COLORS["null"], alpha=0.40,
              linewidths=0, rasterized=True)
    d.scatter(muscle[:, 1], muscle[:, 0], s=0.12, color=COLORS["muscle"], alpha=0.38,
              linewidths=0, rasterized=True, label="body-wall muscle")
    d.scatter(atlas[:, 1], atlas[:, 0], s=0.12, color=COLORS["neural"], alpha=0.70,
              linewidths=0, rasterized=True, label="nervous atlas")
    d.set(xlabel="Longitudinal position (µm)", ylabel="Transverse position (µm)",
          xlim=(-455, 455), ylim=(-62, 62), aspect="equal")
    d.legend(loc="upper center", bbox_to_anchor=(0.5, 1.30), ncol=2, markerscale=6,
             handletextpad=0.35, columnspacing=1.1)
    fig.text(0.505, 0.535, "d", ha="left", va="top", fontsize=9,
             fontweight="bold", color=COLORS["text"])
    return save_figure(fig, outdir, "Figure1_framework")


def figure2(repo: Path, anatomy: dict[str, np.ndarray], outdir: Path) -> dict:
    vf = repo / "ros_worm_stage1/validation/final"
    conv = pd.read_csv(repo / "ros_worm_stage1/validation/v2_1/neural_roi/neural_roi_resolution_convergence.csv")
    dose = pd.read_csv(vf / "production/production_neural_muscle_dose.csv")
    stats = pd.read_csv(vf / "statistics/final_nominal_dose_statistics.csv")
    fig = plt.figure(figsize=(DOUBLE_COLUMN_IN, 4.55), layout="constrained")
    gs = fig.add_gridspec(2, 3, height_ratios=[0.62, 1.0], hspace=0.04, wspace=0.10)
    a = fig.add_subplot(gs[0, :2]); b = fig.add_subplot(gs[0, 2])
    c = fig.add_subplot(gs[1, 0]); d = fig.add_subplot(gs[1, 1]); e = fig.add_subplot(gs[1, 2])
    atlas, roi, body = anatomy["atlas"], anatomy["roi"], anatomy["body"]

    for ax, zoom in [(a, False), (b, True)]:
        ax.scatter(body[:, 1], body[:, 0], s=0.05, color=COLORS["null"], alpha=0.25,
                   linewidths=0, rasterized=True)
        ax.scatter(roi[:, 1], roi[:, 0], s=0.10 if not zoom else 0.20,
                   color=COLORS["neural"], alpha=0.30, linewidths=0,
                   rasterized=True, label="0.25 µm union ROI")
        ax.scatter(atlas[:, 1], atlas[:, 0], s=0.08 if not zoom else 0.18,
                   facecolors="none", edgecolors=COLORS["whole"], alpha=0.30,
                   linewidths=0.18, rasterized=True, label="original surface")
        ax.set_aspect("equal")
    a.set(xlabel="Longitudinal position (µm)", ylabel="Transverse position (µm)",
          xlim=(-455, 455), ylim=(-50, 50))
    a.legend(loc="upper center", bbox_to_anchor=(0.52, 1.18), ncol=2, markerscale=6,
             handletextpad=0.35, columnspacing=1.0)
    b.set(xlabel="Longitudinal (µm)", ylabel="Transverse (µm)",
          xlim=(205, 335), ylim=(-32, 32), title="Anterior detail")
    panel_label(a, "a", x=-0.07); panel_label(b, "b", x=-0.20)

    pitch_x = np.arange(len(conv))
    pitch_labels = [f"{v:g}" for v in conv.pitch_um]
    c.plot(pitch_x, conv.volume_um3, "o-", color=COLORS["neural"], ms=3,
           lw=0.55, alpha=0.80)
    c.axhline(conv.loc[conv.pitch_um == 0.25, "volume_um3"].iloc[0], color=COLORS["null_dark"],
              lw=0.65, ls=":")
    c.set(xlabel="Voxel pitch (µm)", ylabel="Body-clipped volume (µm³)",
          xticks=pitch_x, xticklabels=pitch_labels)
    light_grid(c, "y"); panel_label(c, "c")

    for column, label, marker in [("surface_error_p50_um", "p50", "o"),
                                  ("surface_error_p95_um", "p95", "s"),
                                  ("surface_error_p99_um", "p99", "^")]:
        d.plot(pitch_x, conv[column], marker=marker, color=COLORS["neural"],
               lw=0.85, ms=2.8, label=label)
    d.set(yscale="log", xlabel="Voxel pitch (µm)", ylabel="Symmetric surface error (µm)",
          xticks=pitch_x, xticklabels=pitch_labels)
    d.legend(loc="upper left", ncol=1)
    light_grid(d, "y"); panel_label(d, "d")

    for irradiation, color, marker in [("focused", COLORS["focused"], "o"),
                                       ("diffuse", COLORS["diffuse"], "s")]:
        q = dose[(dose.irradiation == irradiation) & dose.roi.str.startswith("neural_voxel_")].sort_values("pitch_um")
        q = q.set_index("pitch_um").reindex(conv.pitch_um).reset_index()
        e.plot(pitch_x, q.dose_ratio_roi_to_whole_worm, marker=marker, color=color,
               ms=3, label=irradiation.capitalize())
        exact = stats[(stats.irradiation == irradiation) & stats.roi.str.startswith("neural_")].iloc[0]
        e.axhline(exact.roi_to_whole_dose_ratio, color=color, lw=0.65, ls=":")
    e.axhline(1, color=COLORS["whole"], lw=0.65, ls="--", label="Whole-worm equality")
    e.set(xlabel="Voxel pitch (µm)", ylabel="Neural / whole-worm dose",
          xticks=pitch_x, xticklabels=pitch_labels, ylim=(0.78, 1.04))
    handles, labels = e.get_legend_handles_labels()
    handles.append(Line2D([0], [0], color=COLORS["null_dark"], lw=0.75, ls=":"))
    labels.append("Exact-union estimate")
    e.legend(handles, labels, loc="lower right", ncol=1)
    light_grid(e, "y"); panel_label(e, "e")
    return save_figure(fig, outdir, "Figure2_neural_ROI")


def cumulative_surface(shells: pd.DataFrame, irradiation: str, surface: str) -> pd.DataFrame:
    q = shells[(shells.irradiation == irradiation) & (shells.surface == surface)].copy()
    q = q[np.isfinite(q.shell_upper_um) & (q.shell_upper_um <= 50)].sort_values("shell_upper_um")
    q["cumulative_fraction"] = q.whole_worm_edep_fraction.cumsum()
    return q


def figure3(repo: Path, outdir: Path) -> dict:
    vf = repo / "ros_worm_stage1/validation/final"
    stats = pd.read_csv(vf / "statistics/final_nominal_dose_statistics.csv")
    dose = pd.read_csv(vf / "production/production_neural_muscle_dose.csv")
    shells = pd.read_csv(vf / "tables/neural_muscle_surface_edep_shells.csv")
    fig = plt.figure(figsize=(DOUBLE_COLUMN_IN, 5.25), layout="constrained")
    gs = fig.add_gridspec(2, 3, height_ratios=[0.92, 1.08], hspace=0.08, wspace=0.12)
    a = fig.add_subplot(gs[0, :]); b = fig.add_subplot(gs[1, 0]); c = fig.add_subplot(gs[1, 1], sharey=b); d = fig.add_subplot(gs[1, 2])

    order = [("focused", "neural", "neural_"), ("focused", "muscle", "physical_"),
             ("diffuse", "neural", "neural_"), ("diffuse", "muscle", "physical_")]
    y = np.arange(len(order))[::-1]
    for yy, (irr, tissue, prefix) in zip(y, order):
        row = stats[(stats.irradiation == irr) & stats.roi.str.startswith(prefix)].iloc[0]
        if tissue == "neural":
            v = dose[(dose.irradiation == irr) & dose.roi.str.startswith("neural_voxel_")].dose_ratio_roi_to_whole_worm
            a.hlines(yy, v.min(), v.max(), color=COLORS["neural"], lw=5.2, alpha=0.18, zorder=1)
        marker = "o" if irr == "focused" else "s"
        a.errorbar(row.roi_to_whole_dose_ratio, yy,
                   xerr=[[row.roi_to_whole_dose_ratio - row.delta_method_ci95_low],
                         [row.delta_method_ci95_high - row.roi_to_whole_dose_ratio]],
                   fmt=marker, mfc=COLORS[tissue], mec="white", mew=0.45,
                   ecolor=COLORS[tissue], elinewidth=1.0, capsize=2.1, ms=4.4, zorder=3)
    a.axvline(1, color=COLORS["whole"], lw=0.75, ls="--")
    a.set(yticks=y, yticklabels=["Focused — neural", "Focused — muscle",
                                 "Diffuse — neural", "Diffuse — muscle"],
          xlabel="Regional dose / whole-worm mean dose", xlim=(0.70, 1.16))
    light_grid(a, "x"); panel_label(a, "a", x=-0.07)

    for ax, irr, letter in [(b, "focused", "b"), (c, "diffuse", "c")]:
        for surface, color, marker in [("nervous", COLORS["neural"], "o"),
                                       ("muscle", COLORS["muscle"], "s")]:
            q = cumulative_surface(shells, irr, surface)
            ax.plot(q.shell_upper_um, 100 * q.cumulative_fraction, marker=marker,
                    color=color, ms=2.8, label=surface.capitalize())
        ax.axvline(5, color=COLORS["null_dark"], lw=0.55, ls=":")
        ax.set(xscale="log", xlabel="Distance from anatomical surface (µm)",
               xticks=[1, 2, 5, 10, 25, 50], title=irr.capitalize(), xlim=(0.85, 58))
        ax.set_xticklabels(["1", "2", "5", "10", "25", "50"])
        light_grid(ax, "y"); panel_label(ax, letter, x=-0.21)
    b.set_ylabel("Cumulative whole-worm energy (%)"); b.legend(loc="upper left")
    plt.setp(c.get_yticklabels(), visible=False)

    rng = np.random.default_rng(20260921)
    for xx, irr in enumerate(("focused", "diffuse")):
        null = pd.read_csv(vf / f"nulls/{irr}/nervous_surface_edep_matched_nulls.csv")
        meta = json.loads((vf / f"nulls/{irr}/edep_control_metadata.json").read_text())
        jitter = rng.uniform(-0.16, 0.16, len(null))
        d.scatter(xx + jitter, 100 * null.edep_fraction_within_5um, s=5.5,
                  color=COLORS["null"], alpha=0.70, linewidths=0, rasterized=True)
        actual = 100 * meta["real"]["edep_fraction_within_5um"]
        d.scatter(xx, actual, marker="D", s=24, color=COLORS["neural"],
                  edgecolor="white", linewidth=0.45, zorder=4)
        d.annotate(f"p = {meta['null_empirical_upper_tail_p_within_5um']:.2f}",
                   (xx, actual), xytext=(0, 9), textcoords="offset points",
                   ha="center", va="bottom", fontsize=5.8, color=COLORS["text"])
    d.set(xticks=[0, 1], xticklabels=["Focused", "Diffuse"],
          ylabel="Energy within 5 µm (%)", xlim=(-0.42, 1.42), title="Matched-atlas controls")
    light_grid(d, "y"); panel_label(d, "d", x=-0.22)
    return save_figure(fig, outdir, "Figure3_dose_and_surface")


def condition_label(row: pd.Series) -> str:
    return f"{row.reported_dose_rate_Gy_s:g} Gy s$^{{-1}}$ × {row.exposure_s:g} s"


def figure4(repo: Path, outdir: Path) -> dict:
    table = pd.read_csv(repo / "ros_worm_stage1/validation/final/tables/final_cannon_condition_table.csv")
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COLUMN_IN, 3.65), sharex=True,
                             layout="constrained", gridspec_kw={"wspace": 0.12})
    for ax, irr, letter, title in zip(
        axes, ("focused", "diffuse"), ("a", "b"),
        ("Focused W, 50 kV — NGM", "Diffuse Ag, 20 kV — M9"),
    ):
        q = table[table.source_type == irr].copy().sort_values(["exposure_s", "reported_dose_rate_Gy_s"])
        y = np.arange(len(q))[::-1]
        for index, (yy, (_, row)) in enumerate(zip(y, q.iterrows())):
            vals = np.array([row.reported_whole_worm_dose_Gy, row.neural_Gy, row.muscle_Gy])
            ax.hlines(yy, 0.5 * vals.min(), 2.0 * vals.max(), color=COLORS["null"],
                      lw=3.8, alpha=0.27,
                      label="0.5-2× dosimetry" if index == 0 else None)
        ax.scatter(q.reported_whole_worm_dose_Gy, y + 0.15, marker="o", s=27, facecolor="white",
                   edgecolor=COLORS["whole"], linewidth=1.0, label="Whole-worm mean", zorder=5)
        ax.scatter(q.neural_Gy, y, marker="D", s=19, color=COLORS["neural"],
                   edgecolor="white", linewidth=0.4, label="Neural", zorder=4)
        ax.scatter(q.muscle_Gy, y - 0.15, marker="s", s=19, color=COLORS["muscle"],
                   edgecolor="white", linewidth=0.4, label="Muscle", zorder=4)
        labels = [condition_label(row) for _, row in q.iterrows()]
        if irr == "focused":
            labels[-1] += "  (egg ejection)" if q.iloc[-1].exposure_s == 15 else ""
        ax.set(yticks=y, yticklabels=labels, xlabel="Nominal regional dose (Gy)",
               xlim=(0, 33), title=title)
        light_grid(ax, "x"); panel_label(ax, letter, x=-0.21)
    handles, labels = axes[0].get_legend_handles_labels()
    order = [labels.index(name) for name in
             ("Whole-worm mean", "Neural", "Muscle", "0.5-2× dosimetry")]
    axes[0].legend([handles[i] for i in order], [labels[i] for i in order],
                   loc="upper right", ncol=1)
    return save_figure(fig, outdir, "Figure4_Cannon_exposures")


def species_frame(chem: pd.DataFrame, irradiation: str, species: str) -> pd.DataFrame:
    return chem[(chem.irradiation == irradiation) & (chem.analysis_region == "neural") &
                (chem.species == species)].sort_values("time_ns")


def figure5(repo: Path, outdir: Path) -> dict:
    chem = pd.read_csv(repo / "ros_worm_stage1/validation/final/chemistry/edep_weighted_chemistry_timeseries.csv")
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE_COLUMN_IN, 3.45), sharex=True,
                             layout="constrained", gridspec_kw={"wspace": 0.11})
    groups = [
        [("°OH^0", "·OH", COLORS["oh"], 1.18), ("e_aq^-1", r"$e^-_{aq}$", COLORS["eaq"], 0.93),
         ("H^0", "H·", COLORS["h_radical"], 0.96)],
        [("H2O2^0", r"$H_2O_2$", COLORS["h2o2"], 1.02), ("H_2^0", r"$H_2$", COLORS["h2"], 0.92),
         ("H3O^1", r"$H_3O^+$", COLORS["h3o"], 1.08)],
    ]
    titles = ["Short-lived reducing/oxidizing species", "Molecular and ionic products"]
    for ax, group, title, letter in zip(axes, groups, titles, ("a", "b")):
        for species, label, color, offset in group:
            for irr, ls, alpha in [("focused", "-", 1.0), ("diffuse", (0, (3, 2)), 0.80)]:
                q = species_frame(chem, irr, species)
                ax.plot(q.time_ns, q.mean_G_molecules_per_100eV, color=color,
                        ls=ls, lw=1.05 if irr == "focused" else 0.85, alpha=alpha)
            qf = species_frame(chem, "focused", species)
            ax.text(1250, qf.mean_G_molecules_per_100eV.iloc[-1] * offset, label,
                    color=color, fontsize=6.4, ha="left", va="center", clip_on=False)
        ax.set(xscale="log", yscale="log", xlabel="Time after energy deposition (ns)",
               ylabel=r"G (molecules 100 eV$^{-1}$)", title=title, xlim=(7e-4, 2100))
        light_grid(ax, "both"); panel_label(ax, letter, x=-0.15)
    style_handles = [
        Line2D([0], [0], color=COLORS["whole"], lw=1.05, ls="-", label="Focused"),
        Line2D([0], [0], color=COLORS["whole"], lw=0.85, ls=(0, (3, 2)), label="Diffuse"),
    ]
    axes[0].legend(handles=style_handles, loc="lower left", ncol=2)
    return save_figure(fig, outdir, "Figure5_radiolysis")


def figure6(repo: Path, outdir: Path) -> dict:
    vf = repo / "ros_worm_stage1/validation/final"
    sweep = pd.read_csv(vf / "chemistry/lite1_target_interaction_sweep.csv")
    cannon = pd.read_csv(vf / "tables/final_cannon_condition_table.csv")
    subset = sweep[(sweep.condition == "focused_avoidance_0p2") &
                   (sweep.analysis_region == "neural")]
    matrices = []
    for target in ("tryptophan_like", "cysteine_thiol_like"):
        q = subset[subset.target_class == target]
        pivot = q.pivot(index="effective_target_concentration_M",
                        columns="background_scavenging_s-1",
                        values="target_interaction_opportunity").sort_index().sort_index(axis=1)
        matrices.append(pivot)
    all_logs = np.concatenate([np.log10(m.to_numpy()).ravel() for m in matrices])
    vmin, vmax = np.floor(all_logs.min()), np.ceil(all_logs.max())

    fig = plt.figure(figsize=(DOUBLE_COLUMN_IN, 5.15), layout="constrained")
    gs = fig.add_gridspec(2, 3, width_ratios=[1, 1, 0.06], height_ratios=[0.92, 1.08],
                          hspace=0.08, wspace=0.10)
    a = fig.add_subplot(gs[0, 0]); b = fig.add_subplot(gs[0, 1]); cb = fig.add_subplot(gs[0, 2])
    c = fig.add_subplot(gs[1, :2]); fig.add_subplot(gs[1, 2]).axis("off")
    for ax, matrix, title, letter in [(a, matrices[0], "Trp-like target", "a"),
                                      (b, matrices[1], "Thiol-like target", "b")]:
        z = np.log10(matrix.to_numpy())
        image = ax.imshow(z, origin="lower", aspect="auto", cmap="cividis", vmin=vmin, vmax=vmax)
        for iy in range(z.shape[0]):
            for ix in range(z.shape[1]):
                ax.text(ix, iy, f"{z[iy, ix]:.1f}", ha="center", va="center",
                        fontsize=5.7, color="white" if z[iy, ix] < (vmin + vmax) / 2 else "#111111")
        ax.set(xticks=range(len(matrix.columns)), xticklabels=[f"10$^{{{int(np.log10(v))}}}$" for v in matrix.columns],
               yticks=range(len(matrix.index)), yticklabels=[f"{1e6*v:g}" for v in matrix.index],
               xlabel=r"Competing scavenging (s$^{-1}$)", ylabel="Effective target (µM)", title=title)
        panel_label(ax, letter, x=-0.18)
    fig.colorbar(image, cax=cb, label="log₁₀ interaction opportunity")

    y = np.arange(len(cannon))[::-1]
    for target, low, high, color, offset, marker, linestyle in [
        ("Trp-like", "Trp_interaction_opportunity_low", "Trp_interaction_opportunity_high",
         COLORS["trp"], 0.13, "o", "-"),
        ("Thiol-like", "thiol_interaction_opportunity_low", "thiol_interaction_opportunity_high",
         COLORS["thiol"], -0.13, "s", (0, (3, 2))),
    ]:
        lo, hi = cannon[low].to_numpy(), cannon[high].to_numpy()
        c.hlines(y + offset, lo, hi, color=color, lw=1.25, alpha=0.88,
                 linestyles=linestyle)
        c.scatter(np.sqrt(lo * hi), y + offset, s=12, marker=marker, color=color,
                  edgecolor="white", linewidth=0.35, zorder=3)
    labels = [f"{'F' if r.source_type == 'focused' else 'D'}  {r.reported_dose_rate_Gy_s:g} Gy s$^{{-1}}$ × {r.exposure_s:g} s"
              for _, r in cannon.iterrows()]
    c.set(xscale="log", yticks=y, yticklabels=labels,
          xlabel="Neural target-interaction opportunity", title="Experimental exposure series")
    target_handles = [
        Line2D([0], [0], color=COLORS["trp"], lw=1.25, ls="-", marker="o",
               markersize=3.5, markeredgecolor="white", markeredgewidth=0.35, label="Trp-like"),
        Line2D([0], [0], color=COLORS["thiol"], lw=1.25, ls=(0, (3, 2)), marker="s",
               markersize=3.5, markeredgecolor="white", markeredgewidth=0.35, label="Thiol-like"),
    ]
    light_grid(c, "x")
    c.legend(handles=target_handles, loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=2)
    panel_label(c, "c", x=-0.09)
    return save_figure(fig, outdir, "Figure6_target_chemistry")


def supplementary1(repo: Path, outdir: Path) -> dict:
    prof = pd.read_csv(repo / "ros_worm_stage1/validation/final/tables/longitudinal_edep_profiles.csv")
    fig, axes = plt.subplots(2, 2, figsize=(DOUBLE_COLUMN_IN, 4.8), sharex=True,
                             layout="constrained", gridspec_kw={"hspace": 0.08, "wspace": 0.10})
    for col, irr in enumerate(("focused", "diffuse")):
        q = prof[prof.irradiation == irr]
        whole = q[q.region == "whole_worm"].set_index("y_center_um")
        axes[0, col].plot(whole.index, 100 * whole.whole_worm_edep_fraction,
                          color=COLORS[irr], lw=1.05)
        axes[0, col].fill_between(whole.index, 0, 100 * whole.whole_worm_edep_fraction,
                                  color=COLORS[irr], alpha=0.10, linewidth=0)
        axes[0, col].set(title=irr.capitalize(), ylabel="Whole-worm energy per 20 µm bin (%)")
        for region, color, label, ls in [
            ("within_5um_nervous_surface", COLORS["neural"], "Nervous surface", "-"),
            ("within_5um_muscle_surface", COLORS["muscle"], "Muscle surface", (0, (3, 2))),
        ]:
            local = q[q.region == region].set_index("y_center_um")
            ratio = np.divide(local.edep_keV, whole.edep_keV,
                              out=np.full(len(local), np.nan), where=whole.edep_keV.to_numpy() > 0)
            axes[1, col].plot(local.index, 100 * ratio, color=color, ls=ls, label=label)
        axes[1, col].set(xlabel="Longitudinal position (µm)",
                         ylabel="Local-bin energy within 5 µm (%)", ylim=(0, 32))
        light_grid(axes[0, col], "y"); light_grid(axes[1, col], "y")
    for ax, label in zip(axes.ravel(), ("a", "b", "c", "d")):
        panel_label(ax, label, x=-0.17)
    axes[1, 0].legend(loc="upper left")
    return save_figure(fig, outdir, "FigureS1_longitudinal")


def supplementary2(repo: Path, outdir: Path) -> dict:
    vf = repo / "ros_worm_stage1/validation/final"
    hist = pd.read_csv(vf / "statistics/history_convergence.csv")
    budget = pd.read_csv(vf / "tables/final_uncertainty_budget.csv")
    fig = plt.figure(figsize=(DOUBLE_COLUMN_IN, 5.0), layout="constrained")
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 0.88], hspace=0.09, wspace=0.10)
    a = fig.add_subplot(gs[0, 0]); b = fig.add_subplot(gs[0, 1], sharey=a); c = fig.add_subplot(gs[1, :])
    for ax, irr, letter in [(a, "focused", "a"), (b, "diffuse", "b")]:
        q = hist[(hist.irradiation == irr) & hist.roi.str.startswith("neural_")].sort_values("prefix_histories")
        x = q.prefix_histories / 1e6
        ax.errorbar(x, q.roi_to_whole_dose_ratio, yerr=1.96 * q.delta_method_se,
                    color=COLORS[irr], marker="o" if irr == "focused" else "s",
                    ms=2.8, lw=0.8, capsize=1.7)
        ax.axhline(1, color=COLORS["whole"], ls="--", lw=0.65)
        ax.axhline(q.roi_to_whole_dose_ratio.iloc[-1], color=COLORS[irr], ls=":", lw=0.75)
        ax.set(xscale="log", xlabel="Primary histories (million)",
               ylabel="Neural / whole-worm dose", title=irr.capitalize(),
               xticks=[1, 2, 5, 10, 20, 50, 100], ylim=(0, 2.35))
        ax.set_xticklabels(["1", "2", "5", "10", "20", "50", "100"])
        light_grid(ax, "y"); panel_label(ax, letter, x=-0.16)
    plt.setp(b.get_yticklabels(), visible=False)

    q = budget[budget.endpoint == "neural/whole-worm dose ratio"].copy()
    q = q[~q.uncertainty_source.str.contains("dosimetry")]
    categories = ["Monte Carlo statistics", "ROI pitch/reconstruction", "atlas registration"]
    ybase = np.arange(len(categories))[::-1]
    for irr, color, offset, marker in [("focused", COLORS["focused"], 0.12, "o"),
                                       ("diffuse", COLORS["diffuse"], -0.12, "s")]:
        for yy, category in zip(ybase, categories):
            row = q[(q.irradiation == irr) & (q.uncertainty_source == category)].iloc[0]
            low = 100 * (row.lower / row.central - 1); high = 100 * (row.upper / row.central - 1)
            c.hlines(yy + offset, low, high, color=color, lw=1.35)
            c.scatter(0, yy + offset, marker=marker, s=15, color=color, edgecolor="white",
                      linewidth=0.35, label=irr.capitalize() if category == categories[0] else None)
    c.axvline(0, color=COLORS["whole"], lw=0.65)
    c.set(yticks=ybase, yticklabels=categories, xlabel="Relative interval around nominal neural-dose ratio (%)")
    c.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2)
    light_grid(c, "x"); panel_label(c, "c", x=-0.08)
    return save_figure(fig, outdir, "FigureS2_uncertainty")


def make_contact_sheet(entries: list[dict], root: Path) -> dict[str, str]:
    preview = root / "previews"; preview.mkdir(parents=True, exist_ok=True)
    images = []
    target_width = 980
    font_path = "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
    font = ImageFont.truetype(font_path, 20) if Path(font_path).exists() else ImageFont.load_default()
    for entry in entries:
        folder = root / ("main" if entry["class"] == "main" else "supplementary")
        im = Image.open(folder / f"{entry['stem']}.png").convert("RGB")
        height = round(im.height * target_width / im.width)
        im = im.resize((target_width, height), Image.Resampling.LANCZOS)
        card = Image.new("RGB", (target_width, height + 38), "white")
        card.paste(im, (0, 38)); ImageDraw.Draw(card).text((8, 8), entry["stem"], fill="#202124", font=font)
        images.append(card)
    cols = 2; rows = int(np.ceil(len(images) / cols)); gap = 24
    row_heights = [max(images[i].height for i in range(r * cols, min((r + 1) * cols, len(images)))) for r in range(rows)]
    sheet = Image.new("RGB", (cols * target_width + (cols - 1) * gap,
                              sum(row_heights) + (rows - 1) * gap), "#E9EAEC")
    y = 0
    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            if idx < len(images): sheet.paste(images[idx], (col * (target_width + gap), y))
        y += row_heights[row] + gap
    color_path = preview / "contact_sheet_color.png"; gray_path = preview / "contact_sheet_grayscale.png"
    sheet.save(color_path, dpi=(150, 150), optimize=True)
    ImageOps.grayscale(sheet).convert("RGB").save(gray_path, dpi=(150, 150), optimize=True)
    return {"color_sha256": sha256(color_path), "grayscale_sha256": sha256(gray_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args(); repo = args.repo.resolve(); root = args.outdir.resolve()
    main_dir = root / "main"; supplement_dir = root / "supplementary"
    apply_publication_style(); anatomy = anatomy_data(repo)
    records = []
    for figure_function, classification in [
        (figure1, "main"), (figure2, "main"), (figure3, "main"),
        (figure4, "main"), (figure5, "main"), (figure6, "main"),
        (supplementary1, "supplementary"), (supplementary2, "supplementary"),
    ]:
        if figure_function in (figure1, figure2):
            record = figure_function(repo, anatomy, main_dir)
        else:
            record = figure_function(repo, main_dir if classification == "main" else supplement_dir)
        record["class"] = classification; records.append(record)
    contact = make_contact_sheet(records, root)
    geometry = repo / "openworm_geometry/compartment_pipeline"
    source_paths = [
        repo / "ros_worm_stage1/config/v2/study_cases.yaml",
        repo / "ros_worm_stage1/config/v2/source_models.yaml",
        *sorted((repo / "ros_worm_stage1/config/v2/spectra").glob("*.csv")),
        geometry / "non_nervous_priority_bake/debug_simple_safe_body_envelope_ellipsoid.stl",
        geometry / "non_nervous_priority_bake/voxel_remesh_wu_like/BodyWallMuscle_voxel_0.020.stl",
        geometry / "baked_priority_meshes_test/NervousSystem_baked_union.stl",
        repo / "ros_worm_stage1/validation/v2_1/neural_roi/neural_roi_union_members_pitch_0.25um.npz",
        repo / "ros_worm_stage1/validation/v2_1/neural_roi/neural_roi_resolution_convergence.csv",
        repo / "ros_worm_stage1/validation/final/production/production_neural_muscle_dose.csv",
        *sorted((repo / "ros_worm_stage1/validation/final/tables").glob("*.csv")),
        *sorted((repo / "ros_worm_stage1/validation/final/statistics").glob("*.csv")),
        *sorted((repo / "ros_worm_stage1/validation/final/neural_roi").glob("*.csv")),
        *sorted((repo / "ros_worm_stage1/validation/final/nulls").glob("*/*.csv")),
        *sorted((repo / "ros_worm_stage1/validation/final/nulls").glob("*/edep_control_metadata.json")),
        repo / "ros_worm_stage1/validation/final/chemistry/edep_weighted_chemistry_timeseries.csv",
        repo / "ros_worm_stage1/validation/final/chemistry/lite1_target_interaction_sweep.csv",
    ]
    manifest = {
        "schema_version": 1,
        "generator": str(Path(__file__).resolve().relative_to(repo)),
        "figures": records,
        "contact_sheets": contact,
        "source_hashes": {str(path.relative_to(repo)): sha256(path) for path in source_paths},
        "design": {"main_figures": 6, "supplementary_figures": 2,
                   "width_in": DOUBLE_COLUMN_IN, "png_dpi": 600,
                   "vector_text": "editable TrueType text in PDF/SVG"},
    }
    (root / "publication_figure_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
