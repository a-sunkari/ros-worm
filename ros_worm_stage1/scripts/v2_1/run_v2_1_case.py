#!/usr/bin/env python3
"""Authoritative end-to-end v2.1 transport plus deposited-energy scorer."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run(command: list[str], cwd: Path) -> None:
    print("+", " ".join(map(str, command)), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=["focused_avoidance", "focused_egg_ejection", "diffuse_paralysis"], required=True)
    parser.add_argument("--spectrum", choices=["soft", "nominal", "hard"], default="nominal")
    parser.add_argument("--environment", choices=["worm_only", "ngm_agar_dish", "m9_drop_glass"])
    parser.add_argument("--material-model", choices=["tissue", "water"], default="tissue")
    parser.add_argument("--events", type=int, default=100_000)
    parser.add_argument("--threads", type=int, default=min(16, os.cpu_count() or 1))
    parser.add_argument("--seed-a", type=int, default=1357911)
    parser.add_argument("--seed-b", type=int, default=2468022)
    parser.add_argument("--run-name")
    parser.add_argument("--beam-y-mm", type=float)
    parser.add_argument("--spot-fwhm-mm", type=float)
    parser.add_argument("--environment-above-mm", type=float)
    parser.add_argument("--environment-below-mm", type=float)
    parser.add_argument("--max-step-um", type=float, default=2.0)
    parser.add_argument("--analysis-python", default=os.environ.get(
        "ROSWORM_ANALYSIS_PYTHON", str(Path.home() / "miniconda3/envs/ros/bin/python")))
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-birth-scoring", action="store_true")
    parser.add_argument("--fast-dose-only", action="store_true")
    parser.add_argument("--null-count", type=int, default=12)
    args = parser.parse_args()

    stage = Path(__file__).resolve().parents[2]
    repo = stage.parent
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_name = args.run_name or f"v2_1_{args.case}_{args.spectrum}_{args.events}_{timestamp}"
    base = [args.analysis_python, str(stage / "scripts/v2/run_v2_case.py"),
            "--case", args.case, "--spectrum", args.spectrum,
            "--material-model", args.material_model, "--events", str(args.events),
            "--threads", str(args.threads), "--seed-a", str(args.seed_a),
            "--seed-b", str(args.seed_b), "--run-name", run_name,
            "--max-step-um", str(args.max_step_um), "--save-steps",
            "--null-count", str(args.null_count), "--analysis-python", args.analysis_python]
    for flag, value in [("--environment", args.environment), ("--beam-y-mm", args.beam_y_mm),
                        ("--spot-fwhm-mm", args.spot_fwhm_mm),
                        ("--environment-above-mm", args.environment_above_mm),
                        ("--environment-below-mm", args.environment_below_mm)]:
        if value is not None:
            base += [flag, str(value)]
    if args.skip_build:
        base.append("--skip-build")
    if args.skip_birth_scoring:
        base.append("--skip-scoring")
    run(base, repo)

    result = stage / "results" / run_name
    scorer_out = result / "anatomy_edep_v2_1"
    roi_dir = stage / "validation/v2_1/neural_roi"
    score = [args.analysis_python, str(stage / "scripts/v2_1/score_edep_v2_1.py"),
             "--root", str(result / "output0.root"),
             "--transport-summary", str(result / "transport_summary.json"),
             "--placement-manifest", str(stage / "config/transport_geometry_v1.csv"),
             "--nervous-stl", str(repo / "openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl"),
             "--source-member-manifest", str(repo / "openworm_geometry/compartment_pipeline/aggregate_testE_nervous_no_cube/testE_aggregate_with_nervous_no_cube.csv"),
             "--outdir", str(scorer_out)]
    for pitch in [0.25, 0.5, 1, 2]:
        score += ["--neural-roi", str(roi_dir / f"neural_roi_union_members_pitch_{pitch:g}um.npz")]
    if args.fast_dose_only:
        score.append("--skip-surface-distance")
    run(score, repo)

    metadata = {
        "schema_version": 1, "case": args.case, "spectrum": args.spectrum,
        "environment": args.environment, "material_model": args.material_model,
        "events": args.events, "random_seeds": [args.seed_a, args.seed_b],
        "maximum_biological_step_um": args.max_step_um,
        "surface_distance_scoring": not args.fast_dose_only,
        "transport_run_manifest": str((result / "run_manifest.json").resolve()),
        "edep_scoring_metadata": str((scorer_out / "edep_scoring_metadata.json").resolve()),
    }
    (result / "v2_1_run_manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"[OK] authoritative v2.1 result: {result}")


if __name__ == "__main__":
    main()
