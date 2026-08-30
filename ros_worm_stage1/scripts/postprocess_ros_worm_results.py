#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil

# Prefer Brave for Plotly/Kaleido static export.
# This avoids Kaleido falling back to Snap Chromium, which can fail headless.
_brave = shutil.which("brave-browser") or shutil.which("brave")
if _brave and not os.environ.get("BROWSER_PATH"):
    os.environ["BROWSER_PATH"] = _brave

import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px


EV_J = 1.602176634e-19
KEV_J = 1.602176634e-16

REGION_ORDER = ["body", "nervous", "bodywall", "digestive", "reproductive", "excretory"]
REGION_LABELS = {
    "body": "Residual body envelope",
    "nervous": "Nervous system",
    "bodywall": "Body wall muscle",
    "digestive": "Digestive system",
    "reproductive": "Reproductive system",
    "excretory": "Excretory system",
}
SPECIES_LABELS = {
    "H3O^1": "H₃O⁺",
    "°OH^0": "•OH",
    "OH^-1": "OH⁻",
    "e_aq^-1": "e⁻aq",
    "H^0": "H•",
    "H_2^0": "H₂",
    "H2O2^0": "H₂O₂",
    "°O^0": "O•",
}


def parse_run_metadata(run_name: str) -> dict:
    meta = {
        "run_name": run_name,
        "case": "Unknown",
        "source_geometry": "Unknown",
        "condition_label": run_name,
        "dose_rate_Gy_s": np.nan,
        "pulse_s": np.nan,
        "nominal_total_dose_Gy": np.nan,
    }

    if "focused" in run_name:
        meta["source_geometry"] = "Focused beam"
    elif "diffuse" in run_name:
        meta["source_geometry"] = "Diffuse field"

    if "caseB" in run_name:
        meta["case"] = "Focused X-ray response"
    elif "caseC" in run_name:
        meta["case"] = "Diffuse dose-response"
    elif "caseD" in run_name:
        meta["case"] = "Focused extended pulse"

    m = re.search(r"_(\d+)p(\d+)Gy_s_(\d+)s", run_name)
    if m:
        meta["dose_rate_Gy_s"] = float(f"{m.group(1)}.{m.group(2)}")
        meta["pulse_s"] = float(m.group(3))
        meta["nominal_total_dose_Gy"] = meta["dose_rate_Gy_s"] * meta["pulse_s"]
        meta["condition_label"] = f"{meta['source_geometry']}: {meta['dose_rate_Gy_s']:g} Gy/s × {meta['pulse_s']:g} s"
        return meta

    m = re.search(r"_(\d+)Gy_s_(\d+)s", run_name)
    if m:
        meta["dose_rate_Gy_s"] = float(m.group(1))
        meta["pulse_s"] = float(m.group(2))
        meta["nominal_total_dose_Gy"] = meta["dose_rate_Gy_s"] * meta["pulse_s"]
        meta["condition_label"] = f"{meta['source_geometry']}: {meta['dose_rate_Gy_s']:g} Gy/s × {meta['pulse_s']:g} s"

    return meta


def parse_region_masses_from_log(log_path: Path) -> pd.DataFrame:
    rows = []
    if not log_path.exists():
        return pd.DataFrame(columns=["region_key", "mass_kg"])

    pat = re.compile(r"\[ROS-WORM\]\[REGION\].*key=(\S+).*mass_kg=([0-9.eE+-]+)")
    for line in log_path.read_text(errors="ignore").splitlines():
        m = pat.search(line)
        if m:
            rows.append({"region_key": m.group(1), "mass_kg": float(m.group(2))})
    return pd.DataFrame(rows).drop_duplicates("region_key")


def read_run(run_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    run_name = run_dir.name
    meta = parse_run_metadata(run_name)

    summary_path = run_dir / "transport_summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    expected_total_dose = float(summary.get("expected_total_dose_Gy", meta["nominal_total_dose_Gy"]))

    comp = pd.read_csv(run_dir / "compartment_dose.csv")
    comp["run_name"] = run_name
    for k, v in meta.items():
        comp[k] = v
    comp["expected_total_dose_Gy"] = expected_total_dose
    comp["region_label"] = comp["region_key"].map(REGION_LABELS).fillna(comp["region_key"])

    masses = parse_region_masses_from_log(run_dir / "transport.log")
    comp = comp.merge(masses, on="region_key", how="left")

    # Scaled physical-energy estimate. Assumes expected_total_dose_Gy is a whole-sample reference dose
    # and distributes total deposited energy according to Monte Carlo scored energy fractions.
    total_mass_kg = comp["mass_kg"].dropna().sum()
    comp["total_model_mass_kg_for_scaling"] = total_mass_kg
    comp["scaled_region_energy_J"] = expected_total_dose * total_mass_kg * comp["relative_fraction_of_scored_edep"]
    comp["scaled_region_energy_eV"] = comp["scaled_region_energy_J"] / EV_J
    comp["scaled_region_dose_Gy_mass_normalized"] = comp["scaled_region_energy_J"] / comp["mass_kg"]
    comp["scaled_energy_fraction_equivalent_Gy"] = expected_total_dose * comp["relative_fraction_of_scored_edep"]

    sec_path = run_dir / "secondary_electrons.csv"
    if sec_path.exists() and sec_path.stat().st_size > 0:
        sec = pd.read_csv(sec_path)
        sec["run_name"] = run_name
        for k, v in meta.items():
            sec[k] = v
        sec["region_label"] = sec["region_key"].map(REGION_LABELS).fillna(sec["region_key"])
    else:
        sec = pd.DataFrame()

    chem_rows = []
    for f in sorted((run_dir / "regions").glob("region*/species_summary.csv")):
        region_dir = f.parent.name
        region_id = int(region_dir.split("_")[0].replace("region", ""))
        region_key = "_".join(region_dir.split("_")[1:])
        df = pd.read_csv(f)
        df["run_name"] = run_name
        df["region_id"] = region_id
        df["region_key"] = region_key
        df["region_label"] = df["region_key"].map(REGION_LABELS).fillna(df["region_key"])
        df["species_label"] = df["speciesName"].map(SPECIES_LABELS).fillna(df["speciesName"])
        for k, v in meta.items():
            df[k] = v
        chem_rows.append(df)

    chem = pd.concat(chem_rows, ignore_index=True) if chem_rows else pd.DataFrame()

    if not chem.empty:
        chem = chem.merge(
            comp[["run_name", "region_key", "scaled_region_energy_eV", "scaled_region_energy_J",
                  "scaled_energy_fraction_equivalent_Gy", "scaled_region_dose_Gy_mass_normalized",
                  "relative_fraction_of_scored_edep"]],
            on=["run_name", "region_key"],
            how="left",
        )
        chem["scaled_species_molecules"] = chem["meanG_molecules_per_100eV"] * (chem["scaled_region_energy_eV"] / 100.0)

    return comp, sec, chem


def write_plot(fig, out_base: Path, width=1250, height=760):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Arial", size=16),
        title=dict(x=0.02, xanchor="left", font=dict(size=22)),
        legend=dict(title=None, bgcolor="rgba(255,255,255,0.7)"),
        margin=dict(l=80, r=40, t=90, b=80),
    )
    fig.write_html(str(out_base.with_suffix(".html")), include_plotlyjs="cdn")
    try:
        fig.write_image(str(out_base.with_suffix(".png")), width=width, height=height, scale=2)
        fig.write_image(str(out_base.with_suffix(".svg")), width=width, height=height)
    except Exception as e:
        print(f"[WARN] Could not export static image for {out_base.name}: {e}")


def main():
    root = Path.cwd()
    results_dir = root / "results"
    outdir = root / "postprocessed_ros_worm"
    tables = outdir / "tables"
    plots = outdir / "plots"
    tables.mkdir(parents=True, exist_ok=True)
    plots.mkdir(parents=True, exist_ok=True)

    run_dirs = sorted([p for p in results_dir.glob("*_full") if (p / "compartment_dose.csv").exists()])
    if not run_dirs:
        raise SystemExit("No *_full result directories found with compartment_dose.csv")

    comp_all, sec_all, chem_all = [], [], []
    for rd in run_dirs:
        c, s, ch = read_run(rd)
        comp_all.append(c)
        if not s.empty:
            sec_all.append(s)
        if not ch.empty:
            chem_all.append(ch)

    comp = pd.concat(comp_all, ignore_index=True)
    sec = pd.concat(sec_all, ignore_index=True) if sec_all else pd.DataFrame()
    chem = pd.concat(chem_all, ignore_index=True) if chem_all else pd.DataFrame()

    comp["region_label"] = pd.Categorical(comp["region_label"], [REGION_LABELS[k] for k in REGION_ORDER], ordered=True)
    if not sec.empty:
        sec["region_label"] = pd.Categorical(sec["region_label"], [REGION_LABELS[k] for k in REGION_ORDER], ordered=True)
    if not chem.empty:
        chem["region_label"] = pd.Categorical(chem["region_label"], [REGION_LABELS[k] for k in REGION_ORDER], ordered=True)

    comp.to_csv(tables / "regional_transport_scaled_summary.csv", index=False)
    sec.to_csv(tables / "secondary_electrons_all_runs.csv", index=False)
    chem.to_csv(tables / "regional_chemistry_species_scaled_summary.csv", index=False)

    run_index = comp[["run_name", "case", "source_geometry", "condition_label", "dose_rate_Gy_s", "pulse_s", "expected_total_dose_Gy"]].drop_duplicates()
    run_index.to_csv(tables / "run_index.csv", index=False)

    sec_summary = pd.DataFrame()
    if not sec.empty:
        # observed=True avoids empty categorical groups, which otherwise produce
        # empty arrays and crash np.percentile().
        sec_summary = sec.dropna(subset=["ekin_keV"]).groupby(
            ["run_name", "condition_label", "source_geometry", "region_key", "region_label"],
            observed=True
        )["ekin_keV"].agg(
            n_secondaries="count",
            mean_keV="mean",
            median_keV="median",
            p05_keV=lambda x: np.percentile(x.to_numpy(dtype=float), 5) if len(x) else np.nan,
            p95_keV=lambda x: np.percentile(x.to_numpy(dtype=float), 95) if len(x) else np.nan,
            max_keV="max",
        ).reset_index()
        sec_summary.to_csv(tables / "secondary_electron_summary_by_region.csv", index=False)

    key_species = ["°OH^0", "e_aq^-1", "H2O2^0", "H^0", "H_2^0"]
    chem_key = chem[chem["speciesName"].isin(key_species)].copy() if not chem.empty else pd.DataFrame()
    if not chem_key.empty:
        chem_key.to_csv(tables / "key_species_scaled_summary.csv", index=False)

    # Plot 1: regional energy fraction.
    fig = px.bar(
        comp,
        x="region_label",
        y="relative_fraction_of_scored_edep",
        color="region_label",
        facet_col="source_geometry",
        barmode="group",
        labels={
            "region_label": "Anatomical compartment",
            "relative_fraction_of_scored_edep": "Fraction of scored deposited energy",
            "source_geometry": "Irradiation geometry",
        },
        title="Regional distribution of deposited energy in the C. elegans model",
        category_orders={"region_label": [REGION_LABELS[k] for k in REGION_ORDER]},
    )
    fig.update_yaxes(tickformat=".1%")
    fig.update_xaxes(tickangle=35)
    write_plot(fig, plots / "regional_deposited_energy_fraction")

    # Plot 2: scaled regional dose-equivalent by condition.
    fig = px.bar(
        comp,
        x="condition_label",
        y="scaled_energy_fraction_equivalent_Gy",
        color="region_label",
        barmode="stack",
        labels={
            "condition_label": "Irradiation condition",
            "scaled_energy_fraction_equivalent_Gy": "Energy-fraction scaled dose contribution (Gy)",
            "region_label": "Compartment",
        },
        title="Dose contributions by anatomical compartment after experimental normalization",
    )
    fig.update_yaxes(tickformat=".2e")
    fig.update_xaxes(tickangle=30)
    write_plot(fig, plots / "scaled_regional_dose_contributions")

    # Plot 3: secondary electron counts.
    if not sec_summary.empty:
        fig = px.bar(
            sec_summary,
            x="region_label",
            y="n_secondaries",
            color="region_label",
            facet_col="source_geometry",
            labels={
                "region_label": "Anatomical compartment",
                "n_secondaries": "Recorded secondary electrons",
                "source_geometry": "Irradiation geometry",
            },
            title="Secondary electron source-term statistics by compartment",
            category_orders={"region_label": [REGION_LABELS[k] for k in REGION_ORDER]},
        )
        fig.update_yaxes(tickformat=".2e")
        fig.update_xaxes(tickangle=35)
        write_plot(fig, plots / "secondary_electron_counts_by_region")

        fig = px.box(
            sec,
            x="region_label",
            y="ekin_keV",
            color="region_label",
            facet_col="source_geometry",
            points="outliers",
            labels={
                "region_label": "Anatomical compartment",
                "ekin_keV": "Secondary electron kinetic energy (keV)",
                "source_geometry": "Irradiation geometry",
            },
            title="Secondary electron energy distributions by compartment",
            category_orders={"region_label": [REGION_LABELS[k] for k in REGION_ORDER]},
        )
        fig.update_yaxes(tickformat=".2e")
        fig.update_xaxes(tickangle=35)
        write_plot(fig, plots / "secondary_electron_energy_distributions")

    # Plot 4: G-values for important radiolysis species.
    if not chem_key.empty:
        fig = px.bar(
            chem_key,
            x="region_label",
            y="meanG_molecules_per_100eV",
            color="species_label",
            facet_col="source_geometry",
            barmode="group",
            labels={
                "region_label": "Anatomical compartment",
                "meanG_molecules_per_100eV": "Mean G value (molecules / 100 eV)",
                "species_label": "Radiolysis species",
                "source_geometry": "Irradiation geometry",
            },
            title="Geant4-DNA water radiolysis yields driven by region-specific electron spectra",
            category_orders={"region_label": [REGION_LABELS[k] for k in REGION_ORDER]},
        )
        fig.update_yaxes(tickformat=".2f")
        fig.update_xaxes(tickangle=35)
        write_plot(fig, plots / "regional_radiolysis_g_values_key_species")

        fig = px.bar(
            chem_key[chem_key["speciesName"].isin(["°OH^0", "H2O2^0"])],
            x="condition_label",
            y="scaled_species_molecules",
            color="region_label",
            facet_row="species_label",
            barmode="stack",
            labels={
                "condition_label": "Irradiation condition",
                "scaled_species_molecules": "Scaled species yield (molecules)",
                "region_label": "Compartment",
                "species_label": "Species",
            },
            title="Scaled •OH and H₂O₂ yields by condition and compartment",
        )
        fig.update_yaxes(tickformat=".2e")
        fig.update_xaxes(tickangle=30)
        write_plot(fig, plots / "scaled_oh_h2o2_yields_by_condition")

        heat = chem_key[chem_key["speciesName"] == "°OH^0"].copy()
        fig = px.density_heatmap(
            heat,
            x="condition_label",
            y="region_label",
            z="scaled_species_molecules",
            histfunc="sum",
            color_continuous_scale="Viridis",
            labels={
                "condition_label": "Irradiation condition",
                "region_label": "Anatomical compartment",
                "scaled_species_molecules": "Scaled •OH yield (molecules)",
            },
            title="Scaled hydroxyl radical yield by irradiation condition",
        )
        fig.update_coloraxes(colorbar_tickformat=".2e")
        fig.update_xaxes(tickangle=30)
        write_plot(fig, plots / "scaled_hydroxyl_yield_heatmap")

    # Markdown summary.
    md = []
    md.append("# ROS-Worm post-processing summary\n")
    md.append(f"Processed `{len(run_dirs)}` full two-stage runs.\n")
    md.append("## Output tables\n")
    for f in sorted(tables.glob("*.csv")):
        md.append(f"- `{f.relative_to(outdir)}`")
    md.append("\n## Output plots\n")
    for f in sorted(plots.glob("*.html")):
        md.append(f"- `{f.relative_to(outdir)}`")
    md.append("\n## Notes\n")
    md.append("- Stage 1 uses heterogeneous tissue-equivalent transport materials.")
    md.append("- Stage 2 uses Geant4-DNA liquid-water chemistry driven by each region's secondary electron spectrum.")
    md.append("- `scaled_energy_fraction_equivalent_Gy` distributes the requested experimental dose by the Monte Carlo deposited-energy fraction.")
    md.append("- `scaled_region_dose_Gy_mass_normalized` additionally divides scaled deposited energy by compartment mass; interpret carefully because anatomical compartment masses and residual-body nesting remain model assumptions.")
    md.append("- Low-stat compartments, especially excretory and sometimes reproductive, should not be overinterpreted without higher-history runs.\n")
    (outdir / "POSTPROCESSING_SUMMARY.md").write_text("\n".join(md))

    print(f"[OK] Processed {len(run_dirs)} runs")
    print(f"[OK] Tables: {tables}")
    print(f"[OK] Plots:  {plots}")
    print(f"[OK] Summary: {outdir / 'POSTPROCESSING_SUMMARY.md'}")
    print()
    print("Key output files:")
    for f in sorted(tables.glob("*.csv")):
        print("  ", f)
    for f in sorted(plots.glob("*.html")):
        print("  ", f)


if __name__ == "__main__":
    main()
