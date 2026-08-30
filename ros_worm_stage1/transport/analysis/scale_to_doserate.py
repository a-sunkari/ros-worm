#!/usr/bin/env python3
"""Scale ros_worm transport event dose output to an experimental target dose rate using PyROOT."""
import argparse
import math
import ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root_file")
    ap.add_argument("--target-dose-rate", type=float, required=True, help="Gy/s")
    ap.add_argument("--dose-column", default="Dose_worm_Gy_per_primary")
    args = ap.parse_args()

    f = ROOT.TFile.Open(args.root_file)
    if not f or f.IsZombie():
        raise RuntimeError(f"Could not open {args.root_file}")
    t = f.Get("event")
    if not t:
        raise RuntimeError("No 'event' tree found.")
    if not t.GetBranch(args.dose_column):
        branches = [b.GetName() for b in t.GetListOfBranches()]
        raise RuntimeError(f"Branch {args.dose_column!r} not found. Available: {branches}")

    vals = []
    for i in range(t.GetEntries()):
        t.GetEntry(i)
        vals.append(float(getattr(t, args.dose_column)))
    mean = sum(vals) / len(vals)
    if mean <= 0:
        raise RuntimeError("Mean dose per primary is zero; check source/geometry/statistics.")
    sd = math.sqrt(sum((x - mean) ** 2 for x in vals) / (len(vals) - 1)) if len(vals) > 1 else 0.0
    rate = args.target_dose_rate / mean

    print("Transport scaling")
    print("-----------------")
    print(f"file:                 {args.root_file}")
    print(f"column:               {args.dose_column}")
    print(f"events:               {len(vals)}")
    print(f"mean dose/primary:    {mean:.6e} Gy")
    print(f"std dose/primary:     {sd:.6e} Gy")
    print(f"target dose rate:     {args.target_dose_rate:.6e} Gy/s")
    print(f"required primaries/s: {rate:.6e}")


if __name__ == "__main__":
    main()
