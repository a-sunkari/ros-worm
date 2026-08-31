#!/usr/bin/env python3
"""One authoritative entry point for the ROS-Worm v2 study.

Tiers are cumulative: production performs smoke, validation, and production.
Existing provenance-complete run directories are reused rather than overwritten.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", choices=["smoke", "validation", "production"], default="smoke")
    parser.add_argument("--threads", type=int, default=min(12, os.cpu_count() or 1))
    parser.add_argument("--analysis-python", default=str(Path.home() / "miniconda3/envs/ros/bin/python"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    stage = Path(__file__).resolve().parents[2]
    repo = stage.parent
    python = args.analysis_python

    commands: list[tuple[list[str], Path | None]] = [
        ([python, str(stage / "scripts/v2/generate_source_ensemble_v2.py")], None),
    ]
    # Final tuple member is a list of extra run_v2_case.py arguments. Keeping
    # the full design here makes the repository, rather than shell history,
    # authoritative for every tracked comparison.
    cases = [
        ("focused_avoidance", "nominal", "ngm_agar_dish", 100_000, 11001, 22002, "v2_smoke_focused_nominal_ngm_100k", 4, []),
        ("diffuse_paralysis", "nominal", "m9_drop_glass", 100_000, 11002, 22003, "v2_smoke_diffuse_nominal_m9_100k", 4, []),
    ]
    if args.tier in ["validation", "production"]:
        for i in range(3):
            cases += [
                ("focused_avoidance", "nominal", "ngm_agar_dish", 1_000_000, 71001+i, 81001+i, f"v2_validation_focused_nominal_ngm_1M_seed{i+1}", 8, []),
                ("diffuse_paralysis", "nominal", "m9_drop_glass", 1_000_000, 72001+i, 82001+i, f"v2_validation_diffuse_nominal_m9_1M_seed{i+1}", 8, []),
            ]
        for source_case, environment in [("focused_avoidance", "ngm_agar_dish"), ("diffuse_paralysis", "m9_drop_glass")]:
            for spectrum in ["soft", "hard"]:
                prefix = "focused" if source_case.startswith("focused") else "diffuse"
                env_short = "ngm" if prefix == "focused" else "m9"
                cases.append((source_case, spectrum, environment, 1_000_000,
                              71001 if prefix == "focused" else 72001,
                              81001 if prefix == "focused" else 82001,
                              f"v2_sensitivity_{prefix}_{spectrum}_{env_short}_1M", 0, []))
        # Paired one-at-a-time sensitivity tests use the seed-1 nominal seeds.
        # Parameters not listed in extra_args remain at the authoritative
        # nominal values in study_cases.yaml.
        cases += [
            ("focused_avoidance", "nominal", "worm_only", 1_000_000, 71001, 81001,
             "v2_sensitivity_focused_nominal_worm_only_1M", 0, []),
            ("diffuse_paralysis", "nominal", "worm_only", 1_000_000, 72001, 82001,
             "v2_sensitivity_diffuse_nominal_worm_only_1M", 0, []),
            ("focused_avoidance", "nominal", "ngm_agar_dish", 1_000_000, 71001, 81001,
             "v2_sensitivity_beam_y_minus020_1M", 0, ["--beam-y-mm", "-0.2"]),
            ("focused_avoidance", "nominal", "ngm_agar_dish", 1_000_000, 71001, 81001,
             "v2_sensitivity_beam_y_plus020_1M", 0, ["--beam-y-mm", "0.2"]),
            ("focused_avoidance", "nominal", "ngm_agar_dish", 1_000_000, 71001, 81001,
             "v2_sensitivity_fwhm_065_1M", 0, ["--spot-fwhm-mm", "0.65"]),
            ("focused_avoidance", "nominal", "ngm_agar_dish", 1_000_000, 71001, 81001,
             "v2_sensitivity_fwhm_105_1M", 0, ["--spot-fwhm-mm", "1.05"]),
            ("diffuse_paralysis", "nominal", "m9_drop_glass", 1_000_000, 72001, 82001,
             "v2_sensitivity_m9_above_0155_1M", 0, ["--environment-above-mm", "0.155"]),
            ("focused_avoidance", "nominal", "ngm_agar_dish", 1_000_000, 71001, 81001,
             "v2_sensitivity_focused_water_materials_1M", 0, ["--material-model", "water"]),
        ]
    if args.tier == "production":
        cases += [
            ("focused_avoidance", "nominal", "ngm_agar_dish", 10_000_000, 91001, 92001, "v2_production_focused_nominal_ngm_10M", 12, []),
            ("diffuse_paralysis", "nominal", "m9_drop_glass", 10_000_000, 91002, 92002, "v2_production_diffuse_nominal_m9_10M", 12, []),
        ]
    needs_build = True
    for case, spectrum, environment, events, seed_a, seed_b, name, null_count, extra_args in cases:
        existing = stage / "results" / name / "run_manifest.json"
        if existing.exists():
            print(f"[REUSE] {name}")
            continue
        command = [python, str(stage / "scripts/v2/run_v2_case.py"), "--case", case, "--spectrum", spectrum,
                   "--environment", environment, "--events", str(events), "--threads", str(args.threads),
                   "--seed-a", str(seed_a), "--seed-b", str(seed_b), "--run-name", name,
                   "--null-count", str(null_count), "--analysis-python", python]
        command.extend(extra_args)
        if not needs_build: command.append("--skip-build")
        commands.append((command, existing)); needs_build = False

    for command, _ in commands:
        print("+", " ".join(command), flush=True)
        if not args.dry_run: subprocess.run(command, cwd=repo, check=True)

    if args.tier == "production":
        chemistry = [
            ("focused", "neural", "v2_production_focused_nominal_ngm_10M"),
            ("diffuse", "neural", "v2_production_diffuse_nominal_m9_10M"),
            ("focused", "muscle", "v2_production_focused_nominal_ngm_10M"),
            ("diffuse", "muscle", "v2_production_diffuse_nominal_m9_10M"),
        ]
        for label, tissue, transport in chemistry:
            outdir = stage / "results" / f"v2_chemistry_{label}_{tissue}_10k"
            if (outdir / "run_manifest.json").exists():
                print(f"[REUSE] {outdir.name}"); continue
            spectrum = stage / "results" / transport / f"anatomy_scoring_v2/electron_spectrum_{tissue}_within_5um.csv"
            command = [python, str(stage / "scripts/run_chemistry_spectrum.py"), "--spectrum", str(spectrum),
                       "--outdir", str(outdir), "--events", "10000", "--threads", str(min(8,args.threads))]
            print("+", " ".join(command), flush=True)
            if not args.dry_run: subprocess.run(command, cwd=repo, check=True)
    collect = [python, str(stage / "scripts/v2/collect_v2_results.py")]
    print("+", " ".join(collect), flush=True)
    if not args.dry_run: subprocess.run(collect, cwd=repo, check=True)
    if args.tier == "production":
        audit = [python, str(stage / "scripts/v2/audit_v2_release.py")]
        print("+", " ".join(audit), flush=True)
        if not args.dry_run: subprocess.run(audit, cwd=repo, check=True)


if __name__ == "__main__":
    main()
