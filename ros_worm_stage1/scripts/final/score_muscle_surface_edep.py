#!/usr/bin/env python3
"""Score actual deposited energy by distance to the physical muscle surface."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
# VTK must precede ROOT in this environment so ROOT's bundled libcurl does not
# pre-empt VTK's OpenSSL-linked dependency chain.
import vtk  # noqa: F401
import ROOT

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v2_1"))
from neural_roi import body_center_and_path, closest_surface_distances_file  # noqa: E402

SHELLS = [(0, 1), (1, 2), (2, 5), (5, 10), (10, 25), (25, 50), (50, np.inf)]


def event_stats(mask: np.ndarray, ids: np.ndarray, edep: np.ndarray, total: np.ndarray) -> dict:
    n = len(total)
    unique, inverse = np.unique(ids[mask], return_inverse=True)
    x = np.bincount(inverse, weights=edep[mask]).astype(float)
    sx, sy = float(x.sum()), float(total.sum())
    mx, my = sx / n, sy / n
    vx = (float(np.dot(x, x)) - sx * sx / n) / (n - 1)
    vy = (float(np.dot(total, total)) - sy * sy / n) / (n - 1)
    lookup = total[unique]
    cov = (float(np.dot(x, lookup)) - sx * sy / n) / (n - 1)
    fraction = mx / my
    se = math.sqrt(max(0, (vx + fraction * fraction * vy - 2 * fraction * cov) / (n * my * my)))
    return {"total_edep_keV": sx, "edep_per_history_keV": mx,
            "whole_worm_edep_fraction": fraction, "whole_worm_edep_fraction_se": se,
            "whole_worm_edep_fraction_ci95_low": fraction - 1.959963984540054 * se,
            "whole_worm_edep_fraction_ci95_high": fraction + 1.959963984540054 * se,
            "contributing_events": len(unique), "edep_steps": int(mask.sum())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--placement-manifest", type=Path, required=True)
    parser.add_argument("--muscle-stl", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    cache = np.load(args.result / "anatomy_edep_v2_1/edep_step_scoring_cache.npz")
    eligible = cache["eligible"].astype(bool)
    points = np.column_stack([cache["scoreX_um"], cache["scoreY_um"], cache["scoreZ_um"]])[eligible]
    edep = cache["edep_keV"].astype(float)[eligible]
    ids = cache["eventID"].astype(np.int64)[eligible]
    center, _ = body_center_and_path(args.placement_manifest.resolve(), Path(__file__).resolve().parents[3])
    distances = closest_surface_distances_file(points, args.muscle_stl.resolve(), center, 100.0, args.workers)
    # Large reproducible caches live with ignored ROOT results; only compact
    # tables and metadata belong in the tracked validation release.
    np.savez_compressed(args.result / "anatomy_edep_v2_1/muscle_surface_distance_cache.npz", eventID=ids,
                        edep_keV=edep, distance_to_muscle_surface_um=distances)
    raw = ROOT.RDataFrame("event", str(args.result / "output0.root")).AsNumpy(
        ["eventID", "Edep_total_worm_keV"])
    n = len(raw["eventID"])
    total = np.empty(n, dtype=float)
    total[np.asarray(raw["eventID"], dtype=np.int64)] = np.asarray(raw["Edep_total_worm_keV"], dtype=float)
    rows = []
    dose_per_history = total.sum() * 1.602176634e-16 / 7.252349e-9 / n
    for lo, hi in SHELLS:
        mask = distances >= lo
        if np.isfinite(hi): mask &= distances < hi
        row = {"shell_lower_um": lo, "shell_upper_um": hi,
               "shell_label": f"{lo:g}-{hi:g}" if np.isfinite(hi) else ">=50"}
        row.update(event_stats(mask, ids, edep, total))
        row["edep_keV_per_whole_worm_Gy"] = row["edep_per_history_keV"] / dose_per_history
        rows.append(row)
    pd.DataFrame(rows).to_csv(args.outdir / "muscle_surface_edep_shells.csv", index=False)
    metadata = {"endpoint": "body-wall-muscle-surface-referenced deposited energy",
                "muscle_surface": str(args.muscle_stl.resolve()), "events": n,
                "eligible_steps": len(edep), "distance_units": "um",
                "interpretation": "distance to closed physical muscle boundary; not membrane or intracellular dose"}
    (args.outdir / "muscle_surface_edep_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
