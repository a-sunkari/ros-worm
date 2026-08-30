#!/usr/bin/env python3
"""
Create electron_spectrum.csv from ros_worm transport ROOT output using PyROOT.
CSV columns: energy_keV,weight. This is intended as input to chemistry/ros_spectrum.in.
"""
import argparse
import ROOT

REGION_NAMES = {1: "worm", 2: "head", 3: "vnc", 4: "bodywall", 5: "intestine"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root_file")
    ap.add_argument("--region", type=int, default=1)
    ap.add_argument("--bins", type=int, default=80)
    ap.add_argument("--emin", type=float, default=0.01, help="keV")
    ap.add_argument("--emax", type=float, default=50.0, help="keV")
    ap.add_argument("--output", default="electron_spectrum.csv")
    args = ap.parse_args()

    f = ROOT.TFile.Open(args.root_file)
    if not f or f.IsZombie():
        raise RuntimeError(f"Could not open {args.root_file}")
    t = f.Get("steps")
    if not t:
        raise RuntimeError("No 'steps' tree found. Make sure /worm/scoring/saveSteps true was used.")

    hist = ROOT.TH1D("electron_spectrum", "electron_spectrum", args.bins, args.emin, args.emax)
    n_selected = 0
    for i in range(t.GetEntries()):
        t.GetEntry(i)
        if abs(int(t.pdg)) != 11:
            continue
        if int(t.regionID) != args.region:
            continue
        e = float(t.ekin_pre_keV)
        if args.emin <= e <= args.emax:
            hist.Fill(e)
            n_selected += 1

    if n_selected == 0:
        raise RuntimeError(f"No electron steps selected for region {args.region} ({REGION_NAMES.get(args.region, 'unknown')}).")

    with open(args.output, "w") as out:
        out.write("# energy_keV,weight\n")
        for b in range(1, hist.GetNbinsX() + 1):
            w = hist.GetBinContent(b)
            if w > 0:
                out.write(f"{hist.GetBinCenter(b):.8e},{int(w)}\n")

    print("Chemistry source spectrum")
    print("-------------------------")
    print(f"input:       {args.root_file}")
    print(f"region:      {args.region} ({REGION_NAMES.get(args.region, 'unknown')})")
    print(f"steps total: {t.GetEntries()}")
    print(f"electrons:   {n_selected}")
    print(f"output:      {args.output}")


if __name__ == "__main__":
    main()
