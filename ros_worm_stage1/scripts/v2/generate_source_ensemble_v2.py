#!/usr/bin/env python3
"""Generate auditable, physics-bracketed v2 tube spectra.

The files are discrete photon-probability spectra for Geant4 sampling. They
must not be described as measurements of the exact Cannon instruments.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
import yaml

# NIST XCOM mass attenuation coefficient samples (cm2/g). Values are linearly
# interpolated in log(E)-log(mu/rho). The reduced grid is adequate for source
# filtration bracketing; it is not a replacement for Geant4 photon transport.
ENERGY_MEV = np.array([0.001, 0.0015, 0.002, 0.003, 0.004, 0.005, 0.006,
                       0.008, 0.010, 0.015, 0.020, 0.030, 0.040, 0.050])
MU_BE = np.array([604.1, 179.7, 74.69, 21.27, 9.178, 4.369, 2.527,
                  1.124, 0.6466, 0.3071, 0.2251, 0.1792, 0.1640, 0.1554])
MU_AL = np.array([1185., 402.2, 226.3, 78.80, 36.05, 19.34, 11.53,
                  5.033, 2.807, 0.8070, 0.4419, 0.2778, 0.2283, 0.2078])
DENSITY_G_CM3 = {"be": 1.848, "al": 2.699}


def attenuation(energy_kev: np.ndarray, be_mm: float, al_mm: float) -> np.ndarray:
    e_mev = energy_kev / 1000.0
    mu_be = np.exp(np.interp(np.log(e_mev), np.log(ENERGY_MEV), np.log(MU_BE)))
    mu_al = np.exp(np.interp(np.log(e_mev), np.log(ENERGY_MEV), np.log(MU_AL)))
    return np.exp(-mu_be * DENSITY_G_CM3["be"] * be_mm / 10.0
                  -mu_al * DENSITY_G_CM3["al"] * al_mm / 10.0)


def build_spectrum(endpoint: float, step: float, minimum: float, pars: dict,
                   line_e: list[float], line_w: list[float]) -> tuple[np.ndarray, np.ndarray]:
    energy = np.arange(minimum, endpoint + step / 2, step)
    continuum = np.maximum(endpoint - energy, 0.0) / energy
    continuum /= continuum.sum()
    lines = np.zeros_like(energy)
    for e, w in zip(line_e, line_w):
        lines[np.argmin(np.abs(energy - e))] += w
    lines /= lines.sum()
    line_fraction = float(pars["characteristic_fraction_pre_filter"])
    weights = ((1.0 - line_fraction) * continuum + line_fraction * lines)
    weights *= attenuation(energy, float(pars["be_mm"]), float(pars["al_mm"]))
    weights /= weights.sum()
    return energy, weights


def quantile(energy: np.ndarray, weights: np.ndarray, q: float) -> float:
    return float(energy[np.searchsorted(np.cumsum(weights), q)])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[2] / "config/v2/source_models.yaml")
    parser.add_argument("--outdir", type=Path, default=Path(__file__).resolve().parents[2] / "config/v2/spectra")
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    args.outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    definitions = {
        "focused_imoxs_w_50kv": 50.0,
        "diffuse_minix_ag_20kv": 20.0,
    }
    for source_name, endpoint in definitions.items():
        source = cfg["sources"][source_name]
        assumed = source["assumed_parameters"]
        for variant, pars in source["ensemble"].items():
            energy, weights = build_spectrum(
                endpoint, float(cfg["common"]["energy_grid_keV"]["step"]),
                float(cfg["common"]["energy_grid_keV"]["min"]), pars,
                assumed["line_energies_keV"], assumed["line_relative_weights"])
            output = args.outdir / f"{source_name}_{variant}.csv"
            with output.open("w", newline="") as handle:
                handle.write("# modelled photon spectrum; not an instrument measurement\n")
                handle.write("# energy_keV,probability\n")
                writer = csv.writer(handle)
                for e, w in zip(energy, weights):
                    if w > 0: writer.writerow([f"{e:.6f}", f"{w:.12g}"])
            rows.append({
                "source": source_name, "variant": variant, "endpoint_keV": endpoint,
                "be_mm": pars["be_mm"], "al_mm": pars["al_mm"],
                "characteristic_fraction_pre_filter": pars["characteristic_fraction_pre_filter"],
                "mean_energy_keV": float(np.sum(energy * weights)),
                "median_energy_keV": quantile(energy, weights, 0.5),
                "p10_energy_keV": quantile(energy, weights, 0.1),
                "p90_energy_keV": quantile(energy, weights, 0.9),
                "photon_fraction_below_5keV": float(weights[energy < 5].sum()),
                "spectrum_file": str(output.relative_to(args.config.parents[2])),
            })
    with (args.outdir / "source_ensemble_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    (args.outdir / "source_ensemble_summary.json").write_text(json.dumps({
        "schema_version": 2,
        "interpretation": "physics-informed uncertainty ensemble, not measured instrument spectra",
        "config": str(args.config.resolve()), "spectra": rows,
    }, indent=2) + "\n")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
