#!/usr/bin/env python3
import argparse, csv, json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--results',required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    res=Path(args.results); out=Path(args.out)
    summary={}
    if (res/'transport_summary.json').exists():
        summary=json.loads((res/'transport_summary.json').read_text())
    dose=[]
    if (res/'compartment_dose.csv').exists():
        with open(res/'compartment_dose.csv') as f: dose=list(csv.DictReader(f))
    lines=[]
    lines.append('# ROS-Worm two-stage simulation technical note\n')
    lines.append('## Pipeline\n')
    lines.append('Stage 1: Geant4 photon/electron transport through remeshed multi-compartment C. elegans geometry.\n')
    lines.append('Stage 2: Geant4-DNA water radiolysis, driven by region-specific secondary electron spectra from Stage 1.\n')
    lines.append('## Transport summary\n')
    if summary:
        lines.append(f"- Events: {summary.get('events')}\n")
        lines.append(f"- Total scored edep: {summary.get('total_scored_edep_keV'):.6g} keV\n")
        lines.append(f"- Target dose-rate setting: {summary.get('target_dose_rate_Gy_s')} Gy/s\n")
        lines.append(f"- Pulse setting: {summary.get('pulse_s')} s\n")
    if dose:
        lines.append('\n## Compartment edep table\n\n')
        lines.append('| Region | Edep keV | Edep/event keV | Fraction |\n|---|---:|---:|---:|\n')
        for r in dose:
            lines.append(f"| {r['region_key']} | {float(r['edep_keV']):.6g} | {float(r['edep_per_event_keV']):.6g} | {float(r['relative_fraction_of_scored_edep']):.4f} |\n")
    lines.append('\n## Interpretation boundary\n')
    lines.append('This package simulates physical energy deposition and local pure-water radiolysis source terms. It does not by itself model full tissue biochemistry, oxygen/scavenger chemistry, LITE-1 channel activation, or behavioral response.\n')
    out.write_text(''.join(lines))
    print(out)
if __name__=='__main__': main()
