#!/usr/bin/env python3
"""Event-level statistical audit for final 100M ROS-Worm dose estimators."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import ROOT
from scipy.stats import skew


def sparse_event_sum(event_ids: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ids, inverse = np.unique(event_ids.astype(np.int64), return_inverse=True)
    return ids, np.bincount(inverse, weights=values).astype(float)


def moments(ids: np.ndarray, x: np.ndarray, y_ids: np.ndarray, y: np.ndarray,
            n: int, mass_factor: float) -> dict[str, float]:
    selected_y = y[np.searchsorted(y_ids, ids)]
    sx, sy = float(x.sum()), float(y.sum())
    sx2, sy2 = float(np.dot(x, x)), float(np.dot(y, y))
    sxy = float(np.dot(x, selected_y))
    mx, my = sx / n, sy / n
    vx = (sx2 - sx * sx / n) / (n - 1)
    vy = (sy2 - sy * sy / n) / (n - 1)
    cov = (sxy - sx * sy / n) / (n - 1)
    fraction = mx / my
    variance_fraction = (vx + fraction * fraction * vy - 2 * fraction * cov) / (n * my * my)
    ratio = fraction * mass_factor
    se = math.sqrt(max(0.0, variance_fraction)) * mass_factor
    return {
        "histories": n, "total_roi_edep_keV": sx, "total_whole_edep_keV": sy,
        "roi_edep_per_history_keV": mx, "whole_edep_per_history_keV": my,
        "roi_to_whole_dose_ratio": ratio, "delta_method_se": se,
        "delta_method_ci95_low": ratio - 1.959963984540054 * se,
        "delta_method_ci95_high": ratio + 1.959963984540054 * se,
        "raw_contributing_events": int(len(ids)),
        "energy_weighted_effective_events": sx * sx / sx2,
        "largest_event_fraction_of_roi_edep": float(x.max() / sx),
        "nonzero_event_edep_skewness": float(skew(x, bias=False)),
        "numerator_denominator_covariance_keV2": cov,
        "se_if_covariance_ignored": math.sqrt(max(0.0, (vx + fraction * fraction * vy) /
                                                       (n * my * my))) * mass_factor,
    }


def poisson_bootstrap(x_by_y: np.ndarray, y: np.ndarray, mass_factor: float,
                      replicates: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    output = np.empty(replicates, dtype=float)
    batch = 20
    for first in range(0, replicates, batch):
        count = min(batch, replicates - first)
        weights = rng.poisson(1.0, size=(count, len(y))).astype(np.float32)
        output[first:first + count] = (weights @ x_by_y) / (weights @ y) * mass_factor
    return output


def prefix_moments(ids: np.ndarray, x: np.ndarray, y_ids: np.ndarray, y: np.ndarray,
                   prefix: int, mass_factor: float) -> dict[str, float]:
    ix = np.searchsorted(ids, prefix)
    iy = np.searchsorted(y_ids, prefix)
    return moments(ids[:ix], x[:ix], y_ids[:iy], y[:iy], prefix, mass_factor)


def analyze(label: str, result: Path, old_validation: Path, outdir: Path,
            bootstraps: int, seed: int) -> tuple[list[dict], list[dict], list[dict]]:
    score = result / "anatomy_edep_v2_1"
    dose = pd.read_csv(score / "neural_muscle_dose_by_roi.csv")
    events = int(dose.events.max())
    cache = np.load(score / "edep_step_scoring_cache.npz")
    member = np.load(score / "exact_member_union_step_membership.npz")["inside"].astype(bool)
    eligible = cache["eligible"].astype(bool)
    event_id = cache["eventID"].astype(np.int64)
    edep = cache["edep_keV"].astype(float)
    region = cache["regionID"].astype(int)

    rdf = ROOT.RDataFrame("event", str(result / "output0.root")).Filter("Edep_total_worm_keV > 0")
    raw = rdf.AsNumpy(["eventID", "Edep_total_worm_keV"])
    order = np.argsort(raw["eventID"])
    y_ids = np.asarray(raw["eventID"], dtype=np.int64)[order]
    y = np.asarray(raw["Edep_total_worm_keV"], dtype=float)[order]
    if len(np.unique(y_ids)) != len(y_ids) or y_ids[0] < 0 or y_ids[-1] >= events:
        raise SystemExit(f"{label}: event IDs are not independent unique histories")

    definitions = [
        ("neural_exact_member_union", eligible & member,
         float(dose.loc[dose.roi.str.startswith("neural_exact_member_union_with_0.25um_mass_density_1.04"), "mass_kg"].iloc[0])),
        ("physical_body_wall_muscle", eligible & (region == 3),
         float(dose.loc[dose.roi == "physical_body_wall_muscle", "mass_kg"].iloc[0])),
    ]
    whole_mass = json.loads((score / "edep_scoring_metadata.json").read_text())["whole_worm_mass_kg"]
    final_rows, convergence_rows, replicate_rows = [], [], []
    old = pd.read_csv(old_validation / label / "neural_muscle_dose_by_roi.csv")
    for j, (roi, mask, roi_mass) in enumerate(definitions):
        x_ids, x = sparse_event_sum(event_id[mask], edep[mask])
        mass_factor = whole_mass / roi_mass
        stats = moments(x_ids, x, y_ids, y, events, mass_factor)
        x_aligned = np.zeros(len(y), dtype=float)
        x_aligned[np.searchsorted(y_ids, x_ids)] = x
        bootstrap = poisson_bootstrap(x_aligned, y, mass_factor, bootstraps, seed + j)
        lo, hi = np.percentile(bootstrap, [2.5, 97.5])
        stats.update({"irradiation": label, "roi": roi, "bootstrap_method": "Poisson(1) event-weight nonparametric bootstrap",
                      "bootstrap_replicates": bootstraps, "bootstrap_seed": seed + j,
                      "bootstrap_se": float(bootstrap.std(ddof=1)), "bootstrap_ci95_low": float(lo),
                      "bootstrap_ci95_high": float(hi),
                      "normal_interval_adequate": bool(len(x_ids) >= 100 and
                          abs((hi - lo) - 2 * 1.959963984540054 * stats["delta_method_se"]) /
                          (hi - lo) < 0.1),
                      "event_independence_check": "unique Geant4 eventID; one primary history per ID; independent RNG histories"})
        final_rows.append(stats)
        for prefix in [1_000_000, 2_000_000, 5_000_000, 10_000_000, 20_000_000, 50_000_000, 100_000_000]:
            row = prefix_moments(x_ids, x, y_ids, y, prefix, mass_factor)
            row.update({"irradiation": label, "roi": roi, "prefix_histories": prefix})
            convergence_rows.append(row)

        old_name = ("neural_exact_member_union_with_0.25um_mass_density_1.04" if roi.startswith("neural")
                    else "physical_body_wall_muscle")
        old_row = old[old.roi == old_name].iloc[0]
        difference = stats["roi_to_whole_dose_ratio"] - old_row.dose_ratio_roi_to_whole_worm
        combined_se = math.hypot(stats["delta_method_se"], old_row.dose_ratio_stochastic_se)
        replicate_rows.append({"irradiation": label, "roi": roi,
                               "old_histories": int(old_row.events), "new_histories": events,
                               "old_ratio": old_row.dose_ratio_roi_to_whole_worm,
                               "old_se": old_row.dose_ratio_stochastic_se,
                               "new_ratio": stats["roi_to_whole_dose_ratio"],
                               "new_se": stats["delta_method_se"], "difference": difference,
                               "combined_se": combined_se, "replicate_z": difference / combined_se,
                               "consistent_with_independent_replicate": abs(difference / combined_se) < 1.96})
    return final_rows, convergence_rows, replicate_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--focused", type=Path, required=True)
    parser.add_argument("--diffuse", type=Path, required=True)
    parser.add_argument("--old-validation", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260901)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    final, convergence, replicate = [], [], []
    for label, path in (("focused", args.focused), ("diffuse", args.diffuse)):
        a, b, c = analyze(label, path.resolve(), args.old_validation.resolve(), args.outdir,
                          args.bootstrap_replicates, args.seed + (0 if label == "focused" else 100))
        final += a; convergence += b; replicate += c
    pd.DataFrame(final).to_csv(args.outdir / "final_nominal_dose_statistics.csv", index=False)
    pd.DataFrame(convergence).to_csv(args.outdir / "history_convergence.csv", index=False)
    pd.DataFrame(replicate).to_csv(args.outdir / "independent_replicate_consistency.csv", index=False)
    metadata = {"schema_version": 1, "primary_interval": "event-level delta method with covariance",
                "bootstrap_role": "distributional adequacy audit; percentile interval",
                "bootstrap_replicates": args.bootstrap_replicates, "seed": args.seed,
                "normality_gate": "at least 100 contributing events and bootstrap-vs-normal interval widths agree within 10%",
                "uncertainty_scope": "Monte Carlo statistics only; reconstruction, registration, model, and experimental dosimetry are separate"}
    (args.outdir / "statistical_audit_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
