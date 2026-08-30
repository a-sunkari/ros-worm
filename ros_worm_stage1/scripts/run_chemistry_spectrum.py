#!/usr/bin/env python3
"""Run the validated chem6-derived water-radiolysis lifecycle for one spectrum."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spectrum", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--events", type=int, default=10000)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--seed-a", type=int, default=1357911)
    parser.add_argument("--seed-b", type=int, default=2468022)
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()

    stage = Path(__file__).resolve().parents[1]
    repo = stage.parent
    source_macro = stage / "chemistry/highstat_macros/ros_spectrum_10k.in"
    build = stage / "chemistry/build"
    binary = build / "ros_worm_chem"
    spectrum = args.spectrum.resolve()
    outdir = args.outdir.resolve()
    if outdir.exists() and any(outdir.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty directory: {outdir}")
    outdir.mkdir(parents=True, exist_ok=True)

    if not args.skip_build:
        subprocess.run(["cmake", "-S", str(stage / "chemistry"), "-B", str(build),
                        "-DCMAKE_BUILD_TYPE=Release"], cwd=repo, check=True)
        subprocess.run(["cmake", "--build", str(build), "-j", str(args.threads)],
                       cwd=repo, check=True)

    text = source_macro.read_text()
    text = text.replace("/run/numberOfThreads 8", f"/run/numberOfThreads {args.threads}")
    text = text.replace("/random/setSeeds 1357911 2468022",
                        f"/random/setSeeds {args.seed_a} {args.seed_b}")
    text = text.replace("/run/beamOn 10000", f"/run/beamOn {args.events}")
    macro = outdir / "chemistry.in"
    macro.write_text(text)
    shutil.copy2(spectrum, outdir / "electron_spectrum.csv")

    with (outdir / "chemistry.log").open("w") as log:
        subprocess.run([str(binary), str(macro)], cwd=outdir, stdout=log,
                       stderr=subprocess.STDOUT, check=True)
    subprocess.run(["python3", str(stage / "chemistry/analysis/summarize_species_root.py"),
                    "--latest", "--csv", "species_summary.csv"], cwd=outdir, check=True)

    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo,
                                      text=True).strip()
    manifest = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "interpretation": "Geant4-DNA water-radiolysis simulation; not measured biological ROS.",
        "git_commit": git_sha,
        "geant4_version": subprocess.check_output(["geant4-config", "--version"],
                                                   text=True).strip(),
        "events": args.events,
        "threads": args.threads,
        "random_seeds": [args.seed_a, args.seed_b],
        "input_spectrum": str(spectrum),
        "input_spectrum_sha256": digest(spectrum),
        "macro_sha256": digest(macro),
    }
    (outdir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"[OK] {outdir}")


if __name__ == "__main__":
    main()
