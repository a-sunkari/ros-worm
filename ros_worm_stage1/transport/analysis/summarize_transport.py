#!/usr/bin/env python3
"""Summarize ROS-Worm transport ROOT output using PyROOT."""
import argparse
from collections import Counter, defaultdict
import math
import ROOT


def mean_sd(vals):
    if not vals:
        return 0.0, 0.0
    m = sum(vals) / len(vals)
    if len(vals) < 2:
        return m, 0.0
    sd = math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))
    return m, sd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root_file")
    args = ap.parse_args()

    f = ROOT.TFile.Open(args.root_file)
    if not f or f.IsZombie():
        raise RuntimeError(f"Could not open {args.root_file}")

    event = f.Get("event")
    steps = f.Get("steps")
    if not event:
        raise RuntimeError("No event tree found")

    print("Transport event summary")
    print("-----------------------")
    print(f"file: {args.root_file}")
    print(f"events: {event.GetEntries()}")

    branches = [b.GetName() for b in event.GetListOfBranches()]
    dose_branches = [b for b in branches if b.startswith("Dose_") and b.endswith("_Gy_per_primary")]
    edep_branches = [b for b in branches if b.startswith("Edep_") and b.endswith("_keV")]

    print("\nEnergy deposition branches:")
    for b in sorted(edep_branches):
        vals = []
        nonzero = 0
        for i in range(event.GetEntries()):
            event.GetEntry(i)
            v = float(getattr(event, b))
            vals.append(v)
            if v > 0:
                nonzero += 1
        m, sd = mean_sd(vals)
        print(f"  {b:28s} mean={m:.6e} keV  sd={sd:.6e}  nonzero={nonzero}")

    print("\nDose branches:")
    for b in sorted(dose_branches):
        vals = []
        nonzero = 0
        for i in range(event.GetEntries()):
            event.GetEntry(i)
            v = float(getattr(event, b))
            vals.append(v)
            if v > 0:
                nonzero += 1
        m, sd = mean_sd(vals)
        print(f"  {b:34s} mean={m:.6e} Gy/primary  sd={sd:.6e}  nonzero={nonzero}")

    if steps:
        print("\nStep summary")
        print(f"steps: {steps.GetEntries()}")
        by_region = Counter()
        e_by_region = Counter()
        by_pdg = Counter()
        ekin_by_region = defaultdict(list)
        for i in range(steps.GetEntries()):
            steps.GetEntry(i)
            r = int(steps.regionID)
            pdg = int(steps.pdg)
            by_region[r] += 1
            by_pdg[pdg] += 1
            if abs(pdg) == 11:
                e_by_region[r] += 1
                ekin_by_region[r].append(float(steps.ekin_pre_keV))
        print("steps by regionID:", dict(sorted(by_region.items())))
        print("electron/positron steps by regionID:", dict(sorted(e_by_region.items())))
        print("steps by PDG:", dict(sorted(by_pdg.items())))
        for r, vals in sorted(ekin_by_region.items()):
            m, sd = mean_sd(vals)
            print(f"  region {r}: electron ekin mean={m:.4g} keV sd={sd:.4g} n={len(vals)}")

    f.Close()


if __name__ == "__main__":
    main()
