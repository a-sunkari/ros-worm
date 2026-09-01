#!/usr/bin/env python3
"""Export every Geant4-DNA species time point with sampling uncertainty."""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import ROOT


def decode(value) -> str:
    try:
        raw = bytes(value)
        return raw.split(b"\0", 1)[0].decode(errors="replace")
    except Exception:
        return str(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    handle = ROOT.TFile.Open(str(args.root))
    tree = handle.Get("species")
    if not tree:
        raise SystemExit(f"No species tree in {args.root}")
    rows = []
    for row in tree:
        n = int(row.nEvent)
        total, total2 = float(row.sumG), float(row.sumG2)
        mean = total / n if n else 0.0
        variance = max(0.0, (total2 - total * total / n) / (n - 1)) if n > 1 else 0.0
        rows.append({
            "time_ns": float(row.time), "species_id": int(row.speciesID),
            "species": decode(row.speciesName), "n_events": n,
            "mean_G_molecules_per_100eV": mean,
            "standard_error_G": math.sqrt(variance / n) if n else 0.0,
            "molecule_count_sum": int(row.number),
        })
    rows.sort(key=lambda item: (item["time_ns"], item["species_id"]))
    with args.out.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    print(f"[OK] {args.out}: {len(rows)} rows, {len(set(r['time_ns'] for r in rows))} times")


if __name__ == "__main__":
    main()
