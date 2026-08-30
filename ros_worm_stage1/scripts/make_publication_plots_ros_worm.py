#!/usr/bin/env python3
from pathlib import Path
import os, shutil
import numpy as np
import pandas as pd
import plotly.express as px

# Prefer Brave over Snap Chromium for Kaleido.
_brave = shutil.which("brave-browser") or shutil.which("brave")
if _brave and not os.environ.get("BROWSER_PATH"):
    os.environ["BROWSER_PATH"] = _brave

BASE = Path("postprocessed_ros_worm/tables")
OUT = Path("postprocessed_ros_worm/publication_plots")
OUT.mkdir(parents=True, exist_ok=True)

REGION_ORDER = [
    "Residual body envelope",
    "Nervous system",
    "Body wall muscle",
    "Digestive system",
    "Reproductive system",
    "Excretory system",
]
TARGET_ORDER = [
    "Nervous system",
    "Body wall muscle",
    "Digestive system",
    "Reproductive system",
    "Excretory system",
]
SOURCE_ORDER = ["Focused beam", "Diffuse field"]
SPECIES_ORDER = ["•OH", "e⁻aq", "H•", "H₂", "H₂O₂"]

def write(fig, name, w=1500, h=900):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Arial", size=18),
        title=dict(x=0.02, xanchor="left", font=dict(size=25)),
        legend=dict(title=None, orientation="v", bgcolor="rgba(255,255,255,0.85)"),
        margin=dict(l=90, r=40, t=90, b=130),
    )
    fig.update_xaxes(showline=True, linewidth=1, linecolor="black", tickangle=30)
    fig.update_yaxes(showline=True, linewidth=1, linecolor="black", gridcolor="rgba(0,0,0,0.10)")
    fig.write_html(str(OUT / f"{name}.html"), include_plotlyjs="cdn")
    fig.write_image(str(OUT / f"{name}.png"), width=w, height=h, scale=2)
    fig.write_image(str(OUT / f"{name}.svg"), width=w, height=h)

transport = pd.read_csv(BASE / "regional_transport_scaled_summary.csv")
chem = pd.read_csv(BASE / "key_species_scaled_summary.csv")
sec_summary = pd.read_csv(BASE / "secondary_electron_summary_by_region.csv")
sec = pd.read_csv(BASE / "secondary_electrons_all_runs.csv")

# -------------------------------------------------------------------
# 1. Correct deposited-energy fraction by source geometry.
# Use mean across dose-rate variants, not sum.
# -------------------------------------------------------------------
dep = (
    transport.groupby(["source_geometry", "region_label"], as_index=False)
    .agg(
        fraction_of_deposited_energy=("relative_fraction_of_scored_edep", "mean"),
        sd_fraction=("relative_fraction_of_scored_edep", "std"),
    )
)
dep["percent_of_deposited_energy"] = 100 * dep["fraction_of_deposited_energy"]

fig = px.bar(
    dep,
    x="region_label",
    y="percent_of_deposited_energy",
    color="source_geometry",
    barmode="group",
    category_orders={"region_label": REGION_ORDER, "source_geometry": SOURCE_ORDER},
    labels={
        "region_label": "Anatomical compartment",
        "percent_of_deposited_energy": "Deposited energy fraction (%)",
        "source_geometry": "Irradiation geometry",
    },
    title="Regional distribution of deposited energy",
)
fig.update_yaxes(tickformat=".1f")
write(fig, "fig1_all_compartments_deposited_energy_fraction")

targets = dep[dep["region_label"].isin(TARGET_ORDER)].copy()
fig = px.bar(
    targets,
    x="region_label",
    y="percent_of_deposited_energy",
    color="source_geometry",
    barmode="group",
    text=targets["percent_of_deposited_energy"].map(lambda x: f"{x:.2f}%"),
    category_orders={"region_label": TARGET_ORDER, "source_geometry": SOURCE_ORDER},
    labels={
        "region_label": "Anatomical compartment",
        "percent_of_deposited_energy": "Deposited energy fraction (%)",
        "source_geometry": "Irradiation geometry",
    },
    title="Deposited energy in target anatomical compartments",
)
fig.update_traces(textposition="outside", cliponaxis=False)
fig.update_yaxes(tickformat=".2f")
write(fig, "fig1b_target_compartments_deposited_energy_fraction")

# -------------------------------------------------------------------
# 2. Scaled dose contribution by condition, target-only.
# -------------------------------------------------------------------
dose_targets = transport[transport["region_label"].isin(TARGET_ORDER)].copy()
fig = px.bar(
    dose_targets,
    x="condition_label",
    y="scaled_energy_fraction_equivalent_Gy",
    color="region_label",
    barmode="stack",
    category_orders={"region_label": TARGET_ORDER},
    labels={
        "condition_label": "Irradiation condition",
        "scaled_energy_fraction_equivalent_Gy": "Energy-fraction scaled dose (Gy)",
        "region_label": "Compartment",
    },
    title="Scaled dose contribution in target compartments",
)
fig.update_yaxes(tickformat=".2e")
write(fig, "fig2_target_compartments_scaled_dose_by_condition", w=1650, h=900)

# -------------------------------------------------------------------
# 3. Secondary electron source statistics, source-geometry aggregated.
# -------------------------------------------------------------------
sec_counts = (
    sec_summary.groupby(["source_geometry", "region_label"], as_index=False)
    .agg(
        n_secondaries=("n_secondaries", "mean"),
        mean_keV=("mean_keV", "mean"),
        median_keV=("median_keV", "mean"),
    )
)
sec_counts_targets = sec_counts[sec_counts["region_label"].isin(TARGET_ORDER)].copy()

fig = px.bar(
    sec_counts_targets,
    x="region_label",
    y="n_secondaries",
    color="source_geometry",
    barmode="group",
    text=sec_counts_targets["n_secondaries"].map(lambda x: f"{x:.0f}"),
    category_orders={"region_label": TARGET_ORDER, "source_geometry": SOURCE_ORDER},
    labels={
        "region_label": "Anatomical compartment",
        "n_secondaries": "Recorded secondary electrons per 100k photons",
        "source_geometry": "Irradiation geometry",
    },
    title="Secondary electron source terms in target compartments",
)
fig.update_traces(textposition="outside", cliponaxis=False)
fig.update_yaxes(tickformat=".0f")
write(fig, "fig3_target_compartments_secondary_electron_counts")

fig = px.bar(
    sec_counts_targets,
    x="region_label",
    y="median_keV",
    color="source_geometry",
    barmode="group",
    text=sec_counts_targets["median_keV"].map(lambda x: f"{x:.2f}"),
    category_orders={"region_label": TARGET_ORDER, "source_geometry": SOURCE_ORDER},
    labels={
        "region_label": "Anatomical compartment",
        "median_keV": "Median secondary electron energy (keV)",
        "source_geometry": "Irradiation geometry",
    },
    title="Median secondary electron energy in target compartments",
)
fig.update_traces(textposition="outside", cliponaxis=False)
fig.update_yaxes(tickformat=".2f")
write(fig, "fig4_target_compartments_secondary_electron_median_energy")

# -------------------------------------------------------------------
# 4. Electron energy distributions without duplicate dose-rate repeats.
# Pick one representative focused and one representative diffuse run.
# -------------------------------------------------------------------
rep_runs = []
for src in SOURCE_ORDER:
    candidates = sec.loc[sec["source_geometry"] == src, "run_name"].drop_duplicates().tolist()
    if candidates:
        rep_runs.append(candidates[0])
sec_rep = sec[sec["run_name"].isin(rep_runs) & sec["region_label"].isin(TARGET_ORDER)].copy()

fig = px.strip(
    sec_rep,
    x="region_label",
    y="ekin_keV",
    color="source_geometry",
    facet_col="source_geometry",
    category_orders={"region_label": TARGET_ORDER, "source_geometry": SOURCE_ORDER},
    labels={
        "region_label": "Anatomical compartment",
        "ekin_keV": "Secondary electron kinetic energy (keV)",
        "source_geometry": "Irradiation geometry",
    },
    title="Recorded secondary electron energies in target compartments",
)
fig.update_traces(jitter=0.35, marker=dict(size=7, opacity=0.75))
fig.update_yaxes(tickformat=".2f")
write(fig, "fig5_target_compartments_secondary_electron_energy_points", w=1600, h=850)

# -------------------------------------------------------------------
# 5. Correct G-value plot: mean across repeated dose conditions, not sum.
# -------------------------------------------------------------------
gvals = (
    chem.groupby(["source_geometry", "region_label", "species_label"], as_index=False)
    .agg(mean_G=("meanG_molecules_per_100eV", "mean"))
)
gvals_targets = gvals[gvals["region_label"].isin(TARGET_ORDER)].copy()

fig = px.bar(
    gvals_targets,
    x="region_label",
    y="mean_G",
    color="species_label",
    facet_col="source_geometry",
    barmode="group",
    category_orders={
        "region_label": TARGET_ORDER,
        "source_geometry": SOURCE_ORDER,
        "species_label": SPECIES_ORDER,
    },
    labels={
        "region_label": "Anatomical compartment",
        "mean_G": "Mean G value (molecules / 100 eV)",
        "species_label": "Radiolysis species",
        "source_geometry": "Irradiation geometry",
    },
    title="Geant4-DNA water radiolysis yields from region-specific electron spectra",
)
fig.update_yaxes(tickformat=".2f")
write(fig, "fig6_target_compartments_g_values")

# -------------------------------------------------------------------
# 6. Scaled ROS products by condition, target-only and all-compartment supplement.
# -------------------------------------------------------------------
ros = chem[chem["species_label"].isin(["•OH", "H₂O₂"])].copy()
ros_targets = ros[ros["region_label"].isin(TARGET_ORDER)].copy()

fig = px.bar(
    ros_targets,
    x="condition_label",
    y="scaled_species_molecules",
    color="region_label",
    facet_row="species_label",
    barmode="stack",
    category_orders={"region_label": TARGET_ORDER},
    labels={
        "condition_label": "Irradiation condition",
        "scaled_species_molecules": "Scaled species yield (molecules)",
        "region_label": "Compartment",
        "species_label": "Species",
    },
    title="Scaled •OH and H₂O₂ yields in target compartments",
)
fig.update_yaxes(tickformat=".2e")
write(fig, "fig7_target_compartments_scaled_oh_h2o2_by_condition", w=1700, h=950)

# Heatmap target-only.
oh_targets = ros_targets[ros_targets["species_label"] == "•OH"].copy()
fig = px.density_heatmap(
    oh_targets,
    x="condition_label",
    y="region_label",
    z="scaled_species_molecules",
    histfunc="sum",
    color_continuous_scale="Viridis",
    category_orders={"region_label": TARGET_ORDER},
    labels={
        "condition_label": "Irradiation condition",
        "region_label": "Anatomical compartment",
        "scaled_species_molecules": "Scaled •OH yield (molecules)",
    },
    title="Scaled hydroxyl radical yield in target compartments",
)
fig.update_coloraxes(colorbar_title="•OH molecules", colorbar_tickformat=".2e")
write(fig, "fig8_target_compartments_scaled_hydroxyl_heatmap", w=1550, h=850)

# Save cleaned summary tables used by figures.
dep.to_csv(OUT / "plot_table_deposited_energy_fraction_by_source.csv", index=False)
targets.to_csv(OUT / "plot_table_target_deposited_energy_fraction_by_source.csv", index=False)
sec_counts.to_csv(OUT / "plot_table_secondary_electrons_by_source.csv", index=False)
gvals.to_csv(OUT / "plot_table_g_values_by_source.csv", index=False)
ros_targets.to_csv(OUT / "plot_table_target_scaled_ros_by_condition.csv", index=False)

print(f"[OK] wrote publication figures to {OUT}")
for f in sorted(OUT.glob("*.png")):
    print(f)

# -------------------------------------------------------------------
# Extra all-compartment publication plots: body retained, but readable.
# -------------------------------------------------------------------
try:
    EXTRA = OUT / "all_compartment_readable"
    EXTRA.mkdir(parents=True, exist_ok=True)

    # All-compartment energy fraction on log y-axis.
    dep_all = dep.copy()
    dep_all["percent_of_deposited_energy"] = dep_all["percent_of_deposited_energy"].clip(lower=1e-4)

    fig = px.bar(
        dep_all,
        x="region_label",
        y="percent_of_deposited_energy",
        color="source_geometry",
        barmode="group",
        category_orders={"region_label": REGION_ORDER, "source_geometry": SOURCE_ORDER},
        labels={
            "region_label": "Anatomical compartment",
            "percent_of_deposited_energy": "Deposited energy fraction (%)",
            "source_geometry": "Irradiation geometry",
        },
        title="Regional distribution of deposited energy, including residual body envelope",
        log_y=True,
    )
    fig.update_yaxes(tickformat=".2e")
    write(fig, "all_compartments_deposited_energy_fraction_log", w=1550, h=900)

    # All-compartment scaled dose, log y-axis.
    dose_all = transport.copy()
    dose_all["scaled_energy_fraction_equivalent_Gy"] = dose_all["scaled_energy_fraction_equivalent_Gy"].clip(lower=1e-8)
    fig = px.bar(
        dose_all,
        x="condition_label",
        y="scaled_energy_fraction_equivalent_Gy",
        color="region_label",
        barmode="stack",
        category_orders={"region_label": REGION_ORDER},
        labels={
            "condition_label": "Irradiation condition",
            "scaled_energy_fraction_equivalent_Gy": "Energy-fraction scaled dose (Gy)",
            "region_label": "Compartment",
        },
        title="Scaled dose contribution by anatomical compartment, including residual body envelope",
        log_y=True,
    )
    fig.update_yaxes(tickformat=".2e")
    write(fig, "all_compartments_scaled_dose_by_condition_log", w=1700, h=900)

    # All-compartment •OH and H2O2 scaled yields, log y-axis.
    ros_all = ros.copy()
    ros_all["scaled_species_molecules"] = ros_all["scaled_species_molecules"].clip(lower=1.0)
    fig = px.bar(
        ros_all,
        x="condition_label",
        y="scaled_species_molecules",
        color="region_label",
        facet_row="species_label",
        barmode="stack",
        category_orders={"region_label": REGION_ORDER},
        labels={
            "condition_label": "Irradiation condition",
            "scaled_species_molecules": "Scaled species yield (molecules)",
            "region_label": "Compartment",
            "species_label": "Species",
        },
        title="Scaled •OH and H₂O₂ yields by compartment, including residual body envelope",
        log_y=True,
    )
    fig.update_yaxes(tickformat=".2e")
    write(fig, "all_compartments_scaled_oh_h2o2_by_condition_log", w=1700, h=950)

    print("[OK] wrote extra all-compartment readable plots")
except Exception as e:
    print("[WARN] extra all-compartment readable plots failed:", repr(e))
