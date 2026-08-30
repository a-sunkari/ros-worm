#!/usr/bin/env python3
from pathlib import Path
import argparse
import json
import os, shutil

import numpy as np
import pandas as pd
import trimesh
from scipy.spatial import cKDTree
import plotly.express as px
import plotly.graph_objects as go

_brave = shutil.which("brave-browser") or shutil.which("brave")
if _brave and not os.environ.get("BROWSER_PATH"):
    os.environ["BROWSER_PATH"] = _brave


REGION_LABELS = {
    "body": "Residual body tissue",
    "bodywall": "Body wall muscle",
    "digestive": "Digestive system",
    "reproductive": "Reproductive system",
    "excretory": "Excretory system",
    "nervous": "Voxel nervous system",
}

REGION_COLORS = {
    "body": "#B8B8B8",
    "bodywall": "#C44E52",
    "digestive": "#55A868",
    "reproductive": "#8172B2",
    "excretory": "#CCB974",
    "near_neural": "#D62728",
    "far": "#BDBDBD",
}


def write_fig(fig, outbase: Path, width=1400, height=850):
    outbase.parent.mkdir(parents=True, exist_ok=True)
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Arial", size=18),
        title=dict(x=0.02, xanchor="left", font=dict(size=25)),
        margin=dict(l=80, r=40, t=90, b=80),
    )
    fig.write_html(outbase.with_suffix(".html"), include_plotlyjs="cdn")
    fig.write_image(outbase.with_suffix(".png"), width=width, height=height, scale=2)
    fig.write_image(outbase.with_suffix(".svg"), width=width, height=height)


def load_transport_summary(run: Path):
    f = run / "compartment_dose.csv"
    if not f.exists():
        return None
    df = pd.read_csv(f)
    if "region_key" in df.columns:
        df["region_label"] = df["region_key"].map(REGION_LABELS).fillna(df["region_key"])
    return df


def plot_transport_dose(run: Path, outdir: Path):
    df = load_transport_summary(run)
    if df is None:
        print("[WARN] no compartment_dose.csv found")
        return

    # Remove nervous if empty/stale from config, but keep all real physical regions.
    if "edep_keV" in df.columns:
        df = df[~((df["region_key"] == "nervous") & (df["edep_keV"] == 0))].copy()

    df = df.sort_values("relative_fraction_of_scored_edep", ascending=False)

    fig = px.bar(
        df,
        x="region_label",
        y="relative_fraction_of_scored_edep",
        text=df["relative_fraction_of_scored_edep"].map(lambda x: f"{100*x:.2f}%"),
        labels={
            "region_label": "Compartment",
            "relative_fraction_of_scored_edep": "Fraction of scored deposited energy",
        },
        title="Stage 1 transport: deposited energy fraction by compartment",
        color="region_key",
        color_discrete_map=REGION_COLORS,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_yaxes(tickformat=".1%", rangemode="tozero")
    fig.update_xaxes(tickangle=25)
    write_fig(fig, outdir / "transport_deposited_energy_fraction")

    if "edep_keV_scaled" in df.columns:
        y = "edep_keV_scaled"
    elif "scaled_edep_keV" in df.columns:
        y = "scaled_edep_keV"
    else:
        y = "edep_keV"

    fig = px.bar(
        df,
        x="region_label",
        y=y,
        labels={
            "region_label": "Compartment",
            y: "Deposited energy (keV)",
        },
        title="Stage 1 transport: compartment deposited energy",
        color="region_key",
        color_discrete_map=REGION_COLORS,
    )
    fig.update_yaxes(exponentformat="power", separatethousands=True)
    fig.update_xaxes(tickangle=25)
    write_fig(fig, outdir / "transport_deposited_energy_by_compartment")


def plot_secondary_counts(run: Path, outdir: Path):
    f = run / "secondary_electrons.csv"
    if not f.exists():
        print("[WARN] no secondary_electrons.csv found")
        return
    sec = pd.read_csv(f)
    sec["region_label"] = sec["region_key"].map(REGION_LABELS).fillna(sec["region_key"])

    counts = sec.groupby(["region_key", "region_label"], as_index=False).size()
    counts = counts.sort_values("size", ascending=False)

    fig = px.bar(
        counts,
        x="region_label",
        y="size",
        text="size",
        labels={"region_label": "Compartment", "size": "Secondary electrons scored"},
        title="Stage 1 transport: secondary electron counts by compartment",
        color="region_key",
        color_discrete_map=REGION_COLORS,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_yaxes(type="log", title="Secondary electrons scored (log scale)")
    fig.update_xaxes(tickangle=25)
    write_fig(fig, outdir / "secondary_electron_counts_by_compartment")

    fig = px.histogram(
        sec,
        x="ekin_keV",
        color="region_label",
        nbins=80,
        labels={"ekin_keV": "Secondary electron kinetic energy (keV)", "count": "Count", "region_label": "Compartment"},
        title="Stage 1 transport: secondary electron energy spectra by compartment",
    )
    fig.update_yaxes(type="log", title="Count (log scale)")
    fig.update_xaxes(exponentformat="power")
    write_fig(fig, outdir / "secondary_electron_energy_spectra_by_compartment")


def plot_exact_neuro(run: Path, outdir: Path):
    root = run / "highres_nervous_exact_surface_scoring"
    scan_f = root / "exact_nervous_surface_threshold_scan.csv"
    scored_f = root / "secondary_electrons_with_exact_nervous_surface_distance.csv"
    meta_f = root / "exact_nervous_surface_scoring_metadata.json"

    if not scan_f.exists() or not scored_f.exists():
        print("[WARN] exact nervous scoring files missing")
        return

    scan = pd.read_csv(scan_f)
    scored = pd.read_csv(scored_f)

    fig = px.bar(
        scan,
        x="threshold_um",
        y="fraction_near",
        text=scan["fraction_near"].map(lambda x: f"{100*x:.1f}%"),
        labels={
            "threshold_um": "Near-neural shell radius (µm)",
            "fraction_near": "Fraction of secondary electrons within shell",
        },
        title="High-resolution nervous anatomy: exact surface-distance threshold sensitivity",
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_yaxes(tickformat=".0%", rangemode="tozero")
    fig.update_xaxes(type="category")
    write_fig(fig, outdir / "exact_neuro_threshold_fraction_near")

    fig = px.line(
        scan,
        x="threshold_um",
        y="n_secondaries_near",
        markers=True,
        labels={
            "threshold_um": "Near-neural shell radius (µm)",
            "n_secondaries_near": "Secondary electrons within shell",
        },
        title="High-resolution nervous anatomy: cumulative secondary electrons by shell radius",
    )
    fig.update_xaxes(type="log", tickvals=[0.5, 1, 2, 5, 10, 25, 50])
    fig.update_yaxes(separatethousands=True)
    write_fig(fig, outdir / "exact_neuro_cumulative_near_counts")

    dist_col = "distance_to_highres_nervous_surface_um"
    fig = px.histogram(
        scored,
        x=dist_col,
        nbins=90,
        labels={dist_col: "Exact distance to high-resolution nervous surface (µm)", "count": "Secondary electrons"},
        title="Exact secondary-electron distance distribution to high-resolution nervous anatomy",
    )
    fig.add_vline(x=5, line_dash="dash", line_width=3, line_color="red")
    fig.add_annotation(x=5, y=1, yref="paper", text="5 µm primary shell", showarrow=False, xanchor="left")
    fig.update_yaxes(type="log", title="Count (log scale)")
    write_fig(fig, outdir / "exact_neuro_distance_distribution")

    scored["near_5um"] = np.where(scored[dist_col] <= 5, "≤5 µm near-neural shell", ">5 µm")
    fig = px.histogram(
        scored,
        x="ekin_keV",
        color="near_5um",
        nbins=80,
        labels={"ekin_keV": "Secondary electron kinetic energy (keV)", "count": "Count", "near_5um": "Classification"},
        title="Secondary electron energy spectra: 5 µm near-neural shell vs remaining transport points",
        color_discrete_map={"≤5 µm near-neural shell": "#D62728", ">5 µm": "#BDBDBD"},
    )
    fig.update_yaxes(type="log", title="Count (log scale)")
    write_fig(fig, outdir / "exact_neuro_near_vs_far_energy_spectrum")

    if meta_f.exists():
        meta = json.loads(meta_f.read_text())
        summary = [
            "# Exact high-resolution nervous scoring summary",
            "",
            f"- Input secondaries: {meta.get('n_input_secondaries')}",
            f"- Primary shell radius: {meta.get('threshold_um_primary')} µm",
            f"- Near-neural secondaries: {meta.get('n_near_primary')}",
            f"- Near-neural fraction: {100*meta.get('fraction_near_primary', 0):.2f}%",
            f"- Median exact distance: {meta.get('distance_um_median'):.2f} µm",
            f"- 5th–95th percentile exact distance: {meta.get('distance_um_p05'):.2f}–{meta.get('distance_um_p95'):.2f} µm",
            "",
            "Interpretation: this is an exact closest-surface proximity shell around the high-resolution nervous STL, not an inside-volume test.",
        ]
        (outdir / "exact_neuro_summary.md").write_text("\n".join(summary))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    run = Path(args.run)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    plot_transport_dose(run, outdir)
    plot_secondary_counts(run, outdir)
    plot_exact_neuro(run, outdir)

    print("[OK] wrote publication figures to", outdir)


if __name__ == "__main__":
    main()
