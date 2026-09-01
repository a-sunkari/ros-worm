#!/usr/bin/env python3
"""Authoritative v2 transport and anatomy-scoring runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def execute(command: list[str], cwd: Path, log: Path | None = None) -> None:
    print("+", " ".join(map(str, command)), flush=True)
    if log:
        with log.open("w") as handle:
            subprocess.run(command, cwd=cwd, stdout=handle, stderr=subprocess.STDOUT, check=True)
    else:
        subprocess.run(command, cwd=cwd, check=True)


def analysis_python(explicit: str | None) -> str:
    candidates = [explicit, os.environ.get("ROSWORM_ANALYSIS_PYTHON"),
                  str(Path.home() / "miniconda3/envs/ros/bin/python"), sys.executable]
    for candidate in candidates:
        if not candidate or not Path(candidate).exists():
            continue
        probe = subprocess.run([candidate, "-c", "import numpy,pandas,vtk,ROOT"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if probe.returncode == 0:
            return candidate
    raise SystemExit("No Python with numpy, pandas, VTK, and ROOT. Pass --analysis-python.")


def triplet_commands(prefix: str, values: list[float]) -> list[str]:
    return [f"/rosworm/{prefix}{axis} {value} mm" for axis, value in zip("XYZ", values)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=["focused_avoidance", "focused_egg_ejection", "diffuse_paralysis"], required=True)
    parser.add_argument("--spectrum", choices=["soft", "nominal", "hard"], default="nominal")
    parser.add_argument("--environment", choices=["worm_only", "ngm_agar_dish", "m9_drop_glass"], default=None)
    parser.add_argument("--material-model", choices=["tissue", "water"], default="tissue")
    parser.add_argument("--beam-y-mm", type=float, default=None, help="Override source and target Y for beam-position sensitivity")
    parser.add_argument("--spot-fwhm-mm", type=float, default=None)
    parser.add_argument("--environment-above-mm", type=float, default=None)
    parser.add_argument("--environment-below-mm", type=float, default=None)
    parser.add_argument("--events", type=int, default=100_000)
    parser.add_argument("--threads", type=int, default=min(16, os.cpu_count() or 1))
    parser.add_argument("--seed-a", type=int, default=1357911)
    parser.add_argument("--seed-b", type=int, default=2468022)
    parser.add_argument("--run-name")
    parser.add_argument("--analysis-python")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-scoring", action="store_true")
    parser.add_argument("--save-steps", action="store_true")
    parser.add_argument("--max-step-um", type=float, default=2.0)
    parser.add_argument("--null-count", type=int, default=12)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    stage = Path(__file__).resolve().parents[2]
    repo = stage.parent
    cfg_path = stage / "config/v2/study_cases.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    case = cfg["cases"][args.case]
    env_name = args.environment or case["default_environment"]
    environment = dict(cfg["environments"][env_name])
    if args.environment_above_mm is not None: environment["above_mm"] = args.environment_above_mm
    if args.environment_below_mm is not None: environment["below_mm"] = args.environment_below_mm
    source_position = list(case["source_position_mm"])
    target_position = list(case["target_position_mm"])
    if args.beam_y_mm is not None:
        source_position[1] = args.beam_y_mm; target_position[1] = args.beam_y_mm
    materials_path = stage / ("config/region_materials.csv" if args.material_model == "tissue" else "config/v2/region_materials_water_sensitivity.csv")
    spectrum = stage / "config/v2/spectra" / f"{case['experimental_source']}_{args.spectrum}.csv"
    if not spectrum.exists():
        execute([sys.executable, str(stage / "scripts/v2/generate_source_ensemble_v2.py")], repo)
    run_name = args.run_name or f"v2_{args.case}_{args.spectrum}_{env_name}_{args.events}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    outdir = stage / "results" / run_name
    if outdir.exists() and not args.resume:
        raise SystemExit(f"Refusing to overwrite {outdir}")
    outdir.mkdir(parents=True, exist_ok=True)
    build = stage / "transport_manifest/build"
    binary = build / "ros_worm_manifest"
    if not args.skip_build:
        execute(["cmake", "-S", str(stage / "transport_manifest"), "-B", str(build), "-DCMAKE_BUILD_TYPE=Release"], repo)
        execute(["cmake", "--build", str(build), "-j", str(args.threads)], repo)

    macro = [
        f"/run/numberOfThreads {args.threads}", f"/random/setSeeds {args.seed_a} {args.seed_b}",
        f"/rosworm/materials {materials_path}",
        f"/rosworm/manifest {stage / 'config/transport_geometry_v1.csv'}",
        f"/rosworm/mmPerUnit {cfg['mm_per_model_unit']}", f"/rosworm/maxStep_um {args.max_step_um} um",
        f"/rosworm/saveSteps {'true' if args.save_steps else 'false'}",
        f"/rosworm/sourceType {case['source_type']}", "/rosworm/spectrumType tabulated",
        f"/rosworm/spectrumFile {spectrum}",
    ]
    macro += triplet_commands("source", source_position)
    macro += [f"/rosworm/direction{axis} {value}" for axis, value in zip("XYZ", case["direction"])]
    macro += triplet_commands("target", target_position)
    if case["source_type"] == "focused":
        macro.append(f"/rosworm/spotFWHM {args.spot_fwhm_mm if args.spot_fwhm_mm is not None else case['spot_fwhm_mm']} mm")
    else:
        macro += [f"/rosworm/halfX {case['target_half_widths_mm'][0]} mm",
                  f"/rosworm/halfZ {case['target_half_widths_mm'][1]} mm"]
    macro += [
        f"/rosworm/environmentMode {environment['mode']}",
        f"/rosworm/environmentMaterial {environment['material']}",
        f"/rosworm/environmentHalfX {environment['half_x_mm']} mm",
        f"/rosworm/environmentHalfY {environment['half_y_mm']} mm",
        f"/rosworm/environmentAbove {environment['above_mm']} mm",
        f"/rosworm/environmentBelow {environment['below_mm']} mm",
        f"/rosworm/substrateMaterial {environment['substrate_material']}",
        f"/rosworm/substrateThickness {environment['substrate_thickness_mm']} mm",
        "/run/initialize", "/tracking/verbose 0", f"/run/printProgress {max(1, args.events // 10)}",
        f"/run/beamOn {args.events}",
    ]
    macro_path = outdir / "transport.mac"
    macro_path.write_text("\n".join(macro) + "\n")
    log_path = outdir / "transport.log"
    if not args.resume or not (outdir / "output0.root").exists():
        execute([str(binary), str(macro_path)], outdir, log_path)

    py = analysis_python(args.analysis_python)
    summary_path = outdir / "transport_summary.json"
    if not args.resume or not summary_path.exists():
        execute([py, str(stage / "scripts/extract_transport_outputs.py"), str(outdir / "output0.root"),
                 "--regions", str(stage / "config/regions.csv"), "--materials", str(materials_path),
                 "--transport-log", str(log_path), "--outdir", str(outdir),
                 "--target-dose-rate", str(max(case["dose_rates_Gy_s"])), "--pulse-s", str(case["exposure_s"]),
                 "--skip-step-csv"], repo)
        execute([py, str(stage / "scripts/summarize_navigation_warnings.py"), str(log_path), "--outdir", str(outdir)], repo)
    scoring_dir = outdir / "anatomy_scoring_v2"
    if not args.skip_scoring and (not args.resume or not (scoring_dir / "anatomy_scoring_metadata.json").exists()):
        execute([py, str(stage / "scripts/v2/score_anatomy_v2.py"), "--secondaries", str(outdir / "secondaries.csv"),
                 "--transport-summary", str(summary_path),
                 "--nervous-stl", str(repo / "openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl"),
                 "--placement-manifest", str(stage / "config/transport_geometry_v1.csv"), "--outdir", str(scoring_dir),
                 "--null-count", str(args.null_count)], repo)

    tracked_inputs = [cfg_path, stage / "config/v2/source_models.yaml", spectrum,
                      stage / "config/transport_geometry_v1.csv", materials_path,
                      repo / "openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl"]
    manifest = {
        "schema_version": 3, "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
        "git_status_at_run": subprocess.check_output(["git", "status", "--short"], cwd=repo, text=True).splitlines(),
        "case_name": args.case, "case": case, "spectrum_variant": args.spectrum,
        "environment_name": env_name, "environment": environment,
        "material_model": args.material_model, "beam_y_mm": source_position[1],
        "spot_fwhm_mm": args.spot_fwhm_mm if args.spot_fwhm_mm is not None else case.get("spot_fwhm_mm"),
        "events": args.events, "threads": args.threads, "random_seeds": [args.seed_a, args.seed_b],
        "save_positive_edep_steps": args.save_steps,
        "edep_step_position_definition": "midpoint of Geant4 pre-step and post-step positions",
        "maximum_biological_step_um": args.max_step_um,
        "geant4_version": subprocess.check_output(["geant4-config", "--version"], text=True).strip(),
        "normalization_warning": case["normalization_note"],
        "artifacts": {str(path.relative_to(repo)): {"sha256": sha256(path), "bytes": path.stat().st_size} for path in tracked_inputs},
        "result_directory": str(outdir.resolve()),
    }
    (outdir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"[OK] {outdir}")


if __name__ == "__main__":
    main()
