#!/usr/bin/env python3
"""Build Geant4-DNA source spectra weighted by locally deposited electron energy."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROI_MAP = {
    "analysis_neural_exact_member_union": "neural",
    "physical_body_wall_muscle": "muscle",
    "within_5um_nervous_surface": "perineural_5um",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    records = []
    for irradiation in ("focused", "diffuse"):
        source = args.production / irradiation / "local_edep_weighted_electron_spectra.csv"
        frame = pd.read_csv(source)
        for roi, tissue in ROI_MAP.items():
            subset = frame[(frame.roi == roi) & (frame.electron_edep_keV > 0)].copy()
            if subset.empty:
                raise SystemExit(f"Missing positive spectrum rows for {irradiation}/{roi}")
            # Log-bin geometric centres avoid a systematic high-energy bias.
            subset["energy_keV"] = np.sqrt(subset.energy_low_keV * subset.energy_high_keV)
            destination = args.outdir / f"{irradiation}_{tissue}_edep_weighted.csv"
            with destination.open("w") as handle:
                handle.write("# energy_keV,weight\n")
                for row in subset.itertuples():
                    handle.write(f"{row.energy_keV:.12g},{row.electron_edep_keV:.12g}\n")
            records.append({
                "irradiation": irradiation,
                "analysis_region": tissue,
                "source_roi": roi,
                "source_file": str(source),
                "source_sha256": sha256(source),
                "output_file": str(destination),
                "output_sha256": sha256(destination),
                "bins": len(subset),
                "electron_edep_keV_represented": float(subset.electron_edep_keV.sum()),
                "spectrum_weight_definition": "electron deposited energy in each pre-step kinetic-energy bin",
            })
    pd.DataFrame(records).to_csv(args.outdir / "edep_weighted_spectrum_manifest.csv", index=False)
    (args.outdir / "README.json").write_text(json.dumps({
        "schema_version": 1,
        "purpose": "Geant4-DNA comparison spectra weighted by local electron edep, not electron-birth counts.",
        "interpretation": "Used to estimate energy-normalized homogeneous-water G values. Absolute molecule equivalents are normalized separately to the full local deposited-energy budget.",
        "limitation": "The condensed-history transport output cannot replay nanometre-resolved tracks; this is a spectrum-conditioned comparison, not direct chemistry continuation.",
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
