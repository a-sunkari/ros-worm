#!/usr/bin/env python3
"""Fail-loud audit for the authoritative publication figure release."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image


EXPECTED = {
    "main": [
        "Figure1_framework", "Figure2_neural_ROI", "Figure3_dose_and_surface",
        "Figure4_Cannon_exposures", "Figure5_radiolysis", "Figure6_target_chemistry",
    ],
    "supplementary": ["FigureS1_longitudinal", "FigureS2_uncertainty"],
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--figure-root", type=Path, required=True)
    args = parser.parse_args()
    repo, root = args.repo.resolve(), args.figure_root.resolve()
    failures: list[str] = []
    manifest_path = root / "publication_figure_manifest.json"
    require(manifest_path.is_file(), f"missing {manifest_path}", failures)
    if failures:
        raise SystemExit("\n".join(f"FAIL: {item}" for item in failures))
    manifest = json.loads(manifest_path.read_text())
    records = {record["stem"]: record for record in manifest["figures"]}

    require(manifest["design"]["main_figures"] == 6, "manifest must declare six main figures", failures)
    require(manifest["design"]["supplementary_figures"] == 2,
            "manifest must declare two supplementary figures", failures)
    for group, stems in EXPECTED.items():
        for stem in stems:
            require(stem in records, f"manifest missing {stem}", failures)
            if stem not in records:
                continue
            record = records[stem]
            require(record["class"] == group, f"wrong class for {stem}", failures)
            for ext in ("pdf", "svg", "png"):
                path = root / group / f"{stem}.{ext}"
                require(path.is_file() and path.stat().st_size > 1000, f"missing/empty {path}", failures)
                if path.is_file():
                    require(digest(path) == record[f"{ext}_sha256"], f"hash mismatch: {path}", failures)
            png = root / group / f"{stem}.png"
            if png.is_file():
                with Image.open(png) as image:
                    expected_width = round(record["width_in"] * record["png_dpi"])
                    expected_height = round(record["height_in"] * record["png_dpi"])
                    require(image.width == expected_width and image.height == expected_height,
                            f"wrong final-size raster dimensions: {png}", failures)
                    require(image.width >= 4000, f"PNG is below intended line-art resolution: {png}", failures)
            svg = root / group / f"{stem}.svg"
            if svg.is_file():
                svg_text = svg.read_text(errors="replace")
                require("<text" in svg_text, f"SVG text was converted to paths: {svg}", failures)

    for name, key in [("contact_sheet_color.png", "color_sha256"),
                      ("contact_sheet_grayscale.png", "grayscale_sha256")]:
        path = root / "previews" / name
        require(path.is_file(), f"missing preview {path}", failures)
        if path.is_file():
            require(digest(path) == manifest["contact_sheets"][key], f"preview hash mismatch: {path}", failures)

    for relative, expected in manifest["source_hashes"].items():
        path = repo / relative
        require(path.is_file(), f"missing source input: {relative}", failures)
        if path.is_file():
            require(digest(path) == expected, f"source input changed after rendering: {relative}", failures)

    pdffonts = shutil.which("pdffonts")
    if pdffonts:
        for group, stems in EXPECTED.items():
            for stem in stems:
                path = root / group / f"{stem}.pdf"
                result = subprocess.run([pdffonts, str(path)], text=True, capture_output=True, check=False)
                require(result.returncode == 0, f"pdffonts could not inspect {path}", failures)
                font_rows = [line for line in result.stdout.splitlines()[2:] if line.strip()]
                require(bool(font_rows), f"PDF contains no inspectable fonts: {path}", failures)
                require(all(" yes " in f" {row} " for row in font_rows),
                        f"PDF has a non-embedded font: {path}", failures)

    if failures:
        raise SystemExit("\n".join(f"FAIL: {item}" for item in failures))
    print("PASS: 6 main and 2 supplementary figures are complete, source-traced, and release-consistent.")


if __name__ == "__main__":
    main()
