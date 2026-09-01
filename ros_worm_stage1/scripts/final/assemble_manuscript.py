#!/usr/bin/env python3
"""Assemble the journal-style manuscript from reviewed component files."""
from pathlib import Path

root = Path(__file__).resolve().parents[3]
man = root / "manuscript"
parts = ["TITLE_ABSTRACT.md", "INTRODUCTION.md", "METHODS.md", "RESULTS.md", "DISCUSSION.md", "FIGURE_CAPTIONS.md", "REFERENCES.md"]
text = "\n\n".join((man / p).read_text().rstrip() for p in parts) + "\n"
(man / "ROS_WORM_MANUSCRIPT.md").write_text(text)
