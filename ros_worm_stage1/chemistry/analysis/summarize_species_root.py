#!/usr/bin/env python3
"""Summarize Geant4-DNA chem6/ROS-Worm Species*.root output using PyROOT.

This handles Geant4 11.3.x ROOT string columns, where PyROOT may expose
speciesName as a LowLevelView instead of a normal Python str.
"""
import argparse
import csv
import glob
import os
import re
from typing import Any, Iterable, List, Tuple

import ROOT


def natural_key(path: str):
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", os.path.basename(path))]


def decode_root_string(value: Any) -> str:
    """Convert ROOT string/char-array/LowLevelView values to normal Python text."""
    if isinstance(value, str):
        return value
    try:
        # std::string-like objects in PyROOT often work through str(), but
        # char buffers/LowLevelViews do not.
        s = str(value)
        if "LowLevelView object" not in s:
            return s
    except Exception:
        pass
    try:
        b = bytes(value)
        return b.split(b"\x00", 1)[0].decode("utf-8", errors="replace")
    except Exception:
        return str(value)


def read_rows(path: str) -> List[Tuple[float, int, str, int, int, float, float, float]]:
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        raise RuntimeError(f"Could not open {path}")
    t = f.Get("species")
    if not t:
        raise RuntimeError(f"No 'species' tree in {path}")

    rows = []
    for i in range(t.GetEntries()):
        t.GetEntry(i)
        time_ns = float(t.time)
        species_id = int(t.speciesID)
        name = decode_root_string(t.speciesName)
        number = int(t.number)
        n_event = int(t.nEvent)
        sum_g = float(t.sumG)
        sum_g2 = float(t.sumG2)
        mean_g = sum_g / n_event if n_event > 0 else 0.0
        rows.append((time_ns, species_id, name, number, n_event, sum_g, sum_g2, mean_g))
    f.Close()
    return rows


def summarize_file(path: str, final_time_ns=None, csv_writer=None):
    rows = read_rows(path)
    if final_time_ns is None and rows:
        final_time_ns = max(r[0] for r in rows)

    selected = [r for r in rows if abs(r[0] - final_time_ns) < 1e-9]
    print(f"\n{os.path.basename(path)}")
    print("time_ns speciesID speciesName number nEvent meanG_molecules_per_100eV")
    for r in selected:
        time_ns, species_id, name, number, n_event, sum_g, sum_g2, mean_g = r
        print(f"{time_ns:.6g} {species_id:9d} {name:>12s} {number:8d} {n_event:6d} {mean_g:.6g}")
        if csv_writer is not None:
            csv_writer.writerow({
                "file": os.path.basename(path),
                "time_ns": time_ns,
                "speciesID": species_id,
                "speciesName": name,
                "number": number,
                "nEvent": n_event,
                "sumG": sum_g,
                "sumG2": sum_g2,
                "meanG_molecules_per_100eV": mean_g,
            })


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", default=None,
                    help="Species ROOT files. Default: Species*.root in cwd")
    ap.add_argument("--time-ns", type=float, default=None,
                    help="Only print this time point. Default: final time in each file")
    ap.add_argument("--latest", action="store_true",
                    help="Analyze only the highest-numbered Species*.root file")
    ap.add_argument("--csv", default=None,
                    help="Optional CSV output path")
    args = ap.parse_args()

    files = args.files if args.files else glob.glob("Species*.root")
    files = sorted(files, key=natural_key)
    if args.latest and files:
        files = [files[-1]]
    if not files:
        raise RuntimeError("No Species*.root files found. Run ros_worm_chem first.")

    csv_file = None
    writer = None
    if args.csv:
        csv_file = open(args.csv, "w", newline="")
        writer = csv.DictWriter(csv_file, fieldnames=[
            "file", "time_ns", "speciesID", "speciesName", "number", "nEvent",
            "sumG", "sumG2", "meanG_molecules_per_100eV"
        ])
        writer.writeheader()

    try:
        for path in files:
            summarize_file(path, args.time_ns, writer)
    finally:
        if csv_file:
            csv_file.close()


if __name__ == "__main__":
    main()
