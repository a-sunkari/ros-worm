#!/usr/bin/env python3
"""Fail-fast audit of the tracked and full-result ROS-Worm v2 release."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pandas as pd


PRODUCTION_RUNS = {
    "focused": "v2_production_focused_nominal_ngm_10M",
    "diffuse": "v2_production_diffuse_nominal_m9_10M",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    stage = Path(__file__).resolve().parents[2]
    repo = stage.parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=stage / "results")
    parser.add_argument("--validation", type=Path, default=stage / "validation/v2")
    args = parser.parse_args()

    checks: list[dict] = []
    production: dict[str, dict] = {}

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    for label, run_name in PRODUCTION_RUNS.items():
        run = args.results / run_name
        full_result = run.exists()
        if not full_result:
            run = args.validation / "runs" / run_name
        anatomy_rel = ("anatomy_scoring_v2/anatomy_scoring_metadata.json"
                       if full_result else "anatomy_scoring_metadata.json")
        required = ["run_manifest.json", "transport.mac", "transport_summary.json", anatomy_rel]
        missing = [item for item in required if not (run / item).exists()]
        check(f"{label}.required_files", not missing, missing or "all present")
        if missing:
            continue
        manifest = json.loads((run / "run_manifest.json").read_text())
        summary = json.loads((run / "transport_summary.json").read_text())
        anatomy = json.loads((run / anatomy_rel).read_text())
        macro = (run / "transport.mac").read_text()
        beam_on = [int(value) for value in re.findall(r"^/run/beamOn\s+(\d+)\s*$", macro, re.MULTILINE)]
        check(f"{label}.beamOn", beam_on == [manifest["events"]] == [10_000_000], beam_on)
        check(f"{label}.summary_events", summary["events"] == manifest["events"], summary["events"])
        check(f"{label}.direction", "/rosworm/directionZ -1.0" in macro,
              manifest["case"]["direction"])
        check(f"{label}.tabulated_spectrum", "/rosworm/spectrumType tabulated" in macro,
              manifest["spectrum_variant"])
        artifact_status = {}
        for relative, recorded in manifest["artifacts"].items():
            path = repo / relative
            artifact_status[relative] = path.exists() and sha256(path) == recorded["sha256"]
        check(f"{label}.artifact_hashes", all(artifact_status.values()), artifact_status)
        exclusions = anatomy["exclusions"]
        outside = exclusions["nonfinite"] + exclusions["recorded_outside_body"] + exclusions["geometrically_outside_body"]
        check(f"{label}.eligible_coordinate_exclusions", outside == 0, exclusions)
        production[label] = {
            "run_name": run_name,
            "audit_source": "full ignored result" if full_result else "tracked compact result",
            "events": manifest["events"],
            "seeds": manifest["random_seeds"],
            "geant4_version": manifest["geant4_version"],
            "transport_git_commit": manifest["git_commit"],
            "git_status_at_transport": manifest["git_status_at_run"],
            "eligible_electrons": anatomy["n_eligible_electrons"],
            "near5_fraction": anatomy["null_model"]["real_fraction_within_5um"],
            "null_enrichment": anatomy["null_model"]["enrichment_ratio_real_over_null_mean"],
            "coordinate_exclusions": exclusions,
        }

    index = pd.read_csv(args.validation / "transport_run_index.csv")
    replicates = pd.read_csv(args.validation / "replicate_summary_1M.csv")
    sensitivity = pd.read_csv(args.validation / "sensitivity_effects.csv")
    chemistry = pd.read_csv(args.validation / "chemistry_reporting_times.csv")
    check("tracked.run_count", len(index) == 34, len(index))
    check("tracked.independent_nominal_replicates",
          (replicates["near5_fraction_count"] == 3).all(),
          replicates[["case", "near5_fraction_count"]].to_dict("records"))
    check("tracked.paired_sensitivity_contrasts", sensitivity["contrast"].nunique() == 12,
          sensitivity["contrast"].nunique())
    expected_times = {0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 999.999}
    check("tracked.chemistry_reporting_times",
          set(chemistry["requested_time_ns"].unique()) == expected_times,
          sorted(chemistry["requested_time_ns"].unique()))
    expected_tissue_pairs = [("Focused", "neural"), ("Diffuse", "neural"),
                             ("Focused", "muscle"), ("Diffuse", "muscle")]
    expected_tissues = set(expected_tissue_pairs)
    actual_tissues = set(map(tuple, chemistry[["condition", "tissue"]].drop_duplicates().to_numpy()))
    check("tracked.chemistry_tissue_conditions", actual_tissues == expected_tissues,
          chemistry[["condition", "tissue"]].drop_duplicates().to_dict("records"))
    chemistry_hashes = {}
    for condition, tissue in expected_tissue_pairs:
        stem = f"{condition.lower()}_{tissue}"
        manifest_path = args.validation / "chemistry" / f"{stem}_run_manifest.json"
        spectrum_path = args.validation / "chemistry" / f"{stem}_electron_spectrum.csv"
        valid = manifest_path.exists() and spectrum_path.exists()
        if valid:
            chemistry_manifest = json.loads(manifest_path.read_text())
            valid = (chemistry_manifest["events"] == 10_000
                     and chemistry_manifest["input_spectrum_sha256"] == sha256(spectrum_path))
        chemistry_hashes[stem] = valid
    check("tracked.chemistry_input_hashes", all(chemistry_hashes.values()), chemistry_hashes)
    pngs = sorted((args.validation / "figures").glob("fig*.png"))
    pdfs = sorted((args.validation / "figures").glob("fig*.pdf"))
    check("tracked.figure_pairs", len(pngs) == len(pdfs) == 10,
          {"png": len(pngs), "pdf": len(pdfs)})
    v1 = args.validation / "v1_regression"
    v1_required = [v1 / name for name in ["run_manifest.json", "transport.mac",
                                           "transport_summary.json", "navigation_warning_summary.json"]]
    check("tracked.v1_regression_files", all(path.exists() for path in v1_required),
          [path.name for path in v1_required if not path.exists()] or "all present")
    if all(path.exists() for path in v1_required):
        v1_manifest = json.loads((v1 / "run_manifest.json").read_text())
        v1_summary = json.loads((v1 / "transport_summary.json").read_text())
        v1_nav = json.loads((v1 / "navigation_warning_summary.json").read_text())
        v1_macro = (v1 / "transport.mac").read_text()
        check("tracked.v1_regression_behavior",
              v1_manifest["events"] == v1_summary["events"] == 1000
              and "/run/beamOn 1000" in v1_macro
              and v1_nav["geomnav1002_incidents"] == 0,
              {"events": v1_summary["events"], "warnings": v1_nav["geomnav1002_incidents"]})

    payload = {
        "schema_version": 1,
        "purpose": "Release-integrity audit; no scientific pass/fail threshold is inferred.",
        "production_runs": production,
        "checks": checks,
        "all_checks_passed": all(item["passed"] for item in checks),
    }
    output = args.validation / "release_audit.json"
    output.write_text(json.dumps(payload, indent=2) + "\n")
    for item in checks:
        print(f"[{'PASS' if item['passed'] else 'FAIL'}] {item['name']}: {item['detail']}")
    print(f"[{'PASS' if payload['all_checks_passed'] else 'FAIL'}] release audit -> {output}")
    raise SystemExit(0 if payload["all_checks_passed"] else 1)


if __name__ == "__main__":
    main()
