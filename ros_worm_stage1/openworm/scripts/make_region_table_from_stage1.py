#!/usr/bin/env python3
"""Create a starting anatomy region table using the current Stage-1 proxy regions.

This is not the final OpenWorm anatomy importer. It gives us a versioned CSV
interface that the Geant4 transport geometry can later consume.
"""
import argparse
import csv
from pathlib import Path

DEFAULT_ROWS = [
    [1, "whole_worm", "world", "water", "capsule", 0, 0, 0, 40, 40, 500, 1000,
     "Stage-1 body placeholder; replace with OpenWorm-informed body axis/shape"],
    [2, "head_proxy", "whole_worm", "water", "sphere", 430, 0, 0, 35, 35, 35, "",
     "Stage-1 placeholder; replace with head neuron/cell coordinate cluster"],
    [3, "ventral_nerve_cord_proxy", "whole_worm", "water", "cylinder", 0, -22, -15, 3, 3, 430, 860,
     "Stage-1 placeholder; replace with OpenWorm VNC/cell positions"],
    [4, "body_wall_muscle_proxy", "whole_worm", "water", "shell", 0, 0, 0, 40, 40, 500, 900,
     "Stage-1 placeholder; replace with muscle quadrants"],
    [5, "intestine_proxy", "whole_worm", "water", "cylinder", 0, 0, 5, 12, 12, 400, 800,
     "Stage-1 placeholder; replace with intestine tract geometry"],
]

HEADER = [
    "region_id", "region_name", "parent", "material", "shape",
    "center_x_um", "center_y_um", "center_z_um",
    "radius_x_um", "radius_y_um", "radius_z_um", "length_um", "notes"
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="openworm/anatomy/stage1_region_table.csv")
    args = ap.parse_args()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(DEFAULT_ROWS)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
