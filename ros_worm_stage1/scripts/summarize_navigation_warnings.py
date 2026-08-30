#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, re
from collections import Counter
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args(); args.outdir.mkdir(parents=True, exist_ok=True)
    text = args.log.read_text(errors="ignore")
    blocks = re.split(r"(?=\*\*\* G4Exception : GeomNav1002)", text)[1:]
    pairs, positions = Counter(), []
    for block in blocks:
        block = block.split("G4Exception-END", 1)[0]
        previous = re.search(r"Previous phys volume:\s*'([^']+)'", block)
        current = re.search(r"Current\s+phys volume:\s*'([^']+)'", block)
        pair = f"{current.group(1) if current else 'unknown'} <- {previous.group(1) if previous else 'unknown'}"
        pairs[pair] += 1
        position = re.search(r"at position\s*:\s*\(([^)]+)\)", block)
        positions.append({"pair": pair, "position": position.group(1) if position else ""})
    with (args.outdir/"navigation_warning_pairs.csv").open("w", newline="") as handle:
        writer=csv.DictWriter(handle, fieldnames=["pair","incidents"]); writer.writeheader()
        for pair, count in pairs.most_common(): writer.writerow({"pair":pair,"incidents":count})
    with (args.outdir/"navigation_warning_incidents.csv").open("w", newline="") as handle:
        writer=csv.DictWriter(handle, fieldnames=["pair","position"]); writer.writeheader(); writer.writerows(positions)
    summary={"log":str(args.log.resolve()),"geomnav1002_incidents":len(blocks),"pair_counts":dict(pairs)}
    (args.outdir/"navigation_warning_summary.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__ == "__main__": main()
