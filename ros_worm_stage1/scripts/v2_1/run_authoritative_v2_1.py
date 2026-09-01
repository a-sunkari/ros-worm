#!/usr/bin/env python3
"""Authoritative, non-destructive entry point for the ROS-Worm v2.1 package."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run(command: list[str], env: dict[str, str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True, env=env)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("audit", "figures", "analysis"), default="audit",
                        help="audit tracked release; rebuild figures; or rebuild compact chemistry analysis and figures")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    repo = args.repo.resolve()
    validation = repo / "ros_worm_stage1/validation/v2_1"
    scripts = repo / "ros_worm_stage1/scripts/v2_1"
    env = os.environ.copy()
    env.setdefault("MPLCONFIGDIR", "/tmp/ros_worm_mpl")
    env.setdefault("XDG_CACHE_HOME", "/tmp/ros_worm_cache")
    python = sys.executable

    if args.stage == "analysis":
        run([python, str(scripts / "calculate_edep_radiochemistry_v2_1.py"),
             "--repo", str(repo), "--production", str(validation / "production"),
             "--chemistry-results", str(validation / "chemistry/runs"),
             "--config", str(repo / "ros_worm_stage1/config/v2_1/lite1_target_chemistry.yaml"),
             "--outdir", str(validation / "chemistry")], env)
    if args.stage in ("analysis", "figures"):
        run([python, str(scripts / "make_v2_1_figures.py"), "--repo", str(repo),
             "--validation", str(validation), "--outdir", str(validation / "figures")], env)
    run([python, str(scripts / "audit_v2_1_release.py"), "--repo", str(repo)], env)


if __name__ == "__main__":
    main()
