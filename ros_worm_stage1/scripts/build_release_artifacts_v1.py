#!/usr/bin/env python3
"""Consolidate verified production outputs into tracked tables and figures."""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def read_csv(path: Path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    stage = Path(__file__).resolve().parents[1]
    results = stage / "results"
    out = stage / "validation/v1"
    figures = stage / "docs/figures"
    out.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    runs = {
        "focused_50kV": results / "production_focused_10M_v1",
        "diffuse_20kV": results / "production_diffuse_10M_v1",
    }
    transport_rows = []
    region_rows = []
    normalized_rows = []
    warning_rows = []
    threshold = {}
    for case, folder in runs.items():
        summary = json.loads((folder / "transport_summary.json").read_text())
        neural = json.loads((folder / "nervous_surface_scoring/nervous_surface_scoring_metadata.json").read_text())
        warning = json.loads((folder / "navigation_warning_summary.json").read_text())
        transport_rows.append({
            "case": case, "events": summary["events"],
            "total_edep_keV": summary["total_scored_edep_keV"],
            "all_secondaries": summary["n_all_secondaries"],
            "eligible_electrons": neural["n_eligible_electrons"],
            "outside_body_excluded": neural["n_recorded_outside_body"] + neural["n_geometrically_outside_body"],
            "within_5um": neural["n_near_primary"],
            "within_5um_fraction": neural["fraction_near_primary"],
            "median_surface_distance_um": neural["distance_um_median"],
            "p95_surface_distance_um": neural["distance_um_p95"],
            "geomnav1002_incidents": warning["geomnav1002_incidents"],
            "warnings_per_primary": warning["geomnav1002_incidents"] / summary["events"],
        })
        physical = [r for r in summary["regions"] if isinstance(r["scoring_mass_kg"], (int, float)) and r["scoring_mass_kg"] > 0]
        total_mass = sum(r["scoring_mass_kg"] for r in physical)
        for r in physical:
            fraction = r["relative_fraction_of_scored_edep"]
            transfer = fraction * total_mass / r["scoring_mass_kg"]
            region_rows.append({"case": case, "region": r["region_key"], "mass_kg": r["scoring_mass_kg"],
                                "edep_keV": r["edep_keV"], "edep_fraction": fraction,
                                "dose_per_history_Gy": r["absorbed_dose_per_incident_history_Gy"]})
            normalized_rows.append({"case": case, "region": r["region_key"],
                                    "region_Gy_per_assumed_1Gy_whole_worm_average": transfer})
        threshold[case] = read_csv(folder / "nervous_surface_scoring/nervous_surface_threshold_scan.csv")
        for pair, count in warning["pair_counts"].items():
            warning_rows.append({"case": case, "boundary_pair": pair, "incidents": count})

    write_csv(out / "transport_production_summary.csv", transport_rows, list(transport_rows[0]))
    write_csv(out / "regional_transport_results.csv", region_rows, list(region_rows[0]))
    write_csv(out / "reference_dose_normalized_regions.csv", normalized_rows, list(normalized_rows[0]))
    write_csv(out / "navigation_warning_pairs.csv", warning_rows, list(warning_rows[0]))

    qc = results / "geometry_qc_highstat_v1"
    for name in ["nervous_surface_fidelity.csv", "nervous_voxel_scoring_dependence.csv"]:
        if (qc / name).exists():
            shutil.copy2(qc / name, out / name)
    mesh_rows = read_csv(qc / "nervous_mesh_qc.csv")
    for row in mesh_rows:
        path = Path(row["path"])
        try:
            row["path"] = str(path.relative_to(stage.parent))
        except ValueError:
            pass
    write_csv(out / "nervous_mesh_qc.csv", mesh_rows, list(mesh_rows[0]))
    for ext in ["png", "svg"]:
        source = qc / f"nervous_morphology_qc.{ext}"
        if source.exists():
            shutil.copy2(source, figures / source.name)

    chemistry_rows = []
    chemistry = {
        "focused_50kV_near_neural_5um": results / "chemistry_focused_near_neural_10k_v1/species_summary.csv",
        "diffuse_20kV_near_neural_5um": results / "chemistry_diffuse_near_neural_10k_v1/species_summary.csv",
    }
    for case, path in chemistry.items():
        for row in read_csv(path):
            chemistry_rows.append({"case": case, "time_ns": row["time_ns"],
                                   "species": row["speciesName"], "events": row["nEvent"],
                                   "mean_G_molecules_per_100eV": row["meanG_molecules_per_100eV"]})
    write_csv(out / "water_radiolysis_1us_summary.csv", chemistry_rows, list(chemistry_rows[0]))

    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), constrained_layout=True)
    regions = ["body", "bodywall", "digestive", "reproductive"]
    x = np.arange(len(regions)); width = 0.36
    for i, case in enumerate(runs):
        vals = [next(r for r in region_rows if r["case"] == case and r["region"] == reg)["edep_fraction"] for reg in regions]
        axes[0].bar(x + (i - .5) * width, vals, width, label=case.replace("_", " "))
    axes[0].set_xticks(x, ["Residual\nbody", "Body-wall\nmuscle", "Digestive", "Reproductive"])
    axes[0].set_ylabel("Fraction of scored energy deposition")
    axes[0].set_yscale("log"); axes[0].legend(frameon=False, fontsize=8)
    for case, rows in threshold.items():
        axes[1].plot([float(r["threshold_um"]) for r in rows],
                     [float(r["fraction_of_eligible_electrons"]) for r in rows], marker="o",
                     label=case.replace("_", " "))
    axes[1].set_xlabel("Distance to neural surface (µm)")
    axes[1].set_ylabel("Fraction of eligible electron births")
    axes[1].legend(frameon=False, fontsize=8)
    fig.savefig(figures / "transport_and_neural_scoring_v1.png", dpi=300)
    fig.savefig(figures / "transport_and_neural_scoring_v1.svg")
    plt.close(fig)

    species_order = ["°OH^0", "H2O2^0", "e_aq^-1", "H^0", "H_2^0"]
    fig, ax = plt.subplots(figsize=(6.2, 3.1), constrained_layout=True)
    x = np.arange(len(species_order)); width = .36
    for i, case in enumerate(chemistry):
        vals = [float(next(r for r in chemistry_rows if r["case"] == case and r["species"] == s)["mean_G_molecules_per_100eV"]) for s in species_order]
        ax.bar(x + (i - .5) * width, vals, width, label=case.replace("_", " "))
    ax.set_xticks(x, ["•OH", "H₂O₂", "e⁻aq", "H•", "H₂"])
    ax.set_ylabel("G value at 1 µs (molecules / 100 eV)")
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(figures / "water_radiolysis_near_neural_v1.png", dpi=300)
    fig.savefig(figures / "water_radiolysis_near_neural_v1.svg")
    plt.close(fig)
    print(f"[OK] release artifacts: {out}")


if __name__ == "__main__":
    main()
