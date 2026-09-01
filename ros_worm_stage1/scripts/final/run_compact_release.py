#!/usr/bin/env python3
"""Regenerate compact paper tables, figures, manuscript, and run the audit."""
from __future__ import annotations
import os, subprocess, sys
from pathlib import Path

repo=Path(__file__).resolve().parents[3]; py=Path(sys.executable); env=dict(os.environ); env.setdefault("MPLCONFIGDIR","/tmp/ros-worm-final-mpl")
commands=[
 [py,repo/"ros_worm_stage1/scripts/final/build_final_tables.py","--repo",repo,"--outdir",repo/"ros_worm_stage1/validation/final/tables"],
 [py,repo/"ros_worm_stage1/scripts/final/make_paper_figures.py","--repo",repo,"--outdir",repo/"ros_worm_stage1/validation/final/figures"],
 [py,repo/"ros_worm_stage1/scripts/final/assemble_manuscript.py"],
 [py,repo/"ros_worm_stage1/scripts/final/audit_paper_release.py","--repo",repo,"--out",repo/"ros_worm_stage1/validation/final/release_audit.json"],
]
for cmd in commands: subprocess.run([str(x) for x in cmd],check=True,env=env,cwd=repo)
