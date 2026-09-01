#!/usr/bin/env python3
"""Fail-fast integrity audit for the tracked ROS-Worm v2.1 release package."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    validation = repo / "ros_worm_stage1/validation/v2_1"
    output = args.output or validation / "release_audit.json"
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    required_docs = [
        "V2_1_EXECUTIVE_SUMMARY.md", "V2_1_LIMITATIONS_AND_EXPERIMENTAL_TESTS.md",
        "docs/v2_1/SCIENTIFIC_PLAN.md", "docs/v2_1/NEURAL_VOLUME_RECONSTRUCTION.md",
        "docs/v2_1/NEURAL_DOSE_METHODS.md", "docs/v2_1/LITE1_MECHANISTIC_EVIDENCE.md",
        "docs/v2_1/LITE1_TARGET_CHEMISTRY.md", "docs/v2_1/METHODS.md",
        "docs/v2_1/RESULTS.md", "docs/v2_1/THESIS_REPORT.md",
        "docs/v2_1/REPRODUCIBILITY.md", "docs/v2_1/PAPER_READINESS_REVIEW.md",
        "docs/v2_1/COMPLETION_MATRIX.md",
    ]
    missing = [item for item in required_docs if not (repo / item).is_file()]
    check("required_documentation", not missing, {"missing": missing, "count": len(required_docs)})

    production = []
    for irradiation in ("focused", "diffuse"):
        directory = validation / "production" / irradiation
        meta = json.loads((directory / "edep_scoring_metadata.json").read_text())
        macro = (directory / "transport.mac").read_text()
        production.append({"irradiation": irradiation, **meta})
        check(f"{irradiation}_10M_histories", meta["events"] == 10_000_000, meta["events"])
        check(f"{irradiation}_spatial_steps_present", meta["steps"] > 0, meta["steps"])
        check(f"{irradiation}_energy_conservation", abs(meta["step_minus_event_edep_keV"]) < 1e-9,
              meta["step_minus_event_edep_keV"])
        check(f"{irradiation}_coordinate_filter", meta["nonfinite_steps_excluded"] == 0 and
              meta["scoring_position_outside_body_steps_excluded"] == 0,
              {"nonfinite": meta["nonfinite_steps_excluded"],
               "outside": meta["scoring_position_outside_body_steps_excluded"]})
        check(f"{irradiation}_step_limit_macro", "/rosworm/maxStep_um 0.5 um" in macro, "0.5 um")

    roi = json.loads((validation / "neural_roi/neural_roi_metadata.json").read_text())
    volumes = [float(record["volume_um3"]) for record in roi["convergence_records"]]
    check("neural_source_members", roi["source_members"] == 276 and
          roi["all_members_watertight_actual"] and roi["all_members_winding_consistent_actual"],
          {"members": roi["source_members"], "watertight": roi["all_members_watertight_actual"]})
    check("neural_volume_resolution_stability", max(volumes) / min(volumes) - 1 < 0.05,
          {"minimum_um3": min(volumes), "maximum_um3": max(volumes)})

    dose = rows(validation / "production/production_neural_muscle_dose.csv")
    exact = [r for r in dose if r["roi"] == "neural_exact_member_union_with_0.25um_mass_density_1.04"]
    muscle = [r for r in dose if r["roi"] == "physical_body_wall_muscle"]
    check("authoritative_neural_dose_rows", len(exact) == 2, len(exact))
    check("muscle_comparator_rows", len(muscle) == 2, len(muscle))

    for irradiation in ("focused", "diffuse"):
        controls = validation / f"production/{irradiation}/controls_1M_prefix/nervous_surface_edep_matched_nulls.csv"
        null_rows = rows(controls)
        check(f"{irradiation}_matched_nulls", len(null_rows) >= 12, len(null_rows))

    sensitivity = rows(validation / "sensitivity/corrected_sensitivity_effects.csv")
    check("sensitivity_ensemble", len(sensitivity) >= 10, len(sensitivity))

    chemistry = rows(validation / "chemistry/chemistry_run_index.csv")
    chemistry_ok = len(chemistry) == 6 and all(int(r["events"]) == 10_000 for r in chemistry)
    check("chemistry_6x10k", chemistry_ok, {"rows": len(chemistry), "versions": sorted({r["geant4_version"] for r in chemistry})})
    chemistry_meta = json.loads((validation / "chemistry/analysis_metadata.json").read_text())
    check("lite1_evidence_gate", chemistry_meta["lite1_evidence_level"] == 1,
          chemistry_meta["lite1_decision"])

    manifest = json.loads((validation / "figures/figure_manifest.json").read_text())
    figure_hash_failures = []
    for record in manifest["figures"]:
        for suffix in ("png", "pdf"):
            path = validation / "figures" / f"{record['figure']}.{suffix}"
            if not path.is_file() or sha256(path) != record[f"{suffix}_sha256"]:
                figure_hash_failures.append(str(path))
    check("ten_figures_hash_verified", len(manifest["figures"]) == 10 and not figure_hash_failures,
          {"count": len(manifest["figures"]), "failures": figure_hash_failures})

    payload = {
        "schema_version": 1,
        "release": "ROS-Worm v2.1",
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
        "production_root_hashes": {item["irradiation"]: item["root_sha256"] for item in production},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"passed": payload["passed"], "checks": len(checks), "output": str(output)}))
    if not payload["passed"]:
        for item in checks:
            if not item["passed"]:
                print(f"FAIL: {item['name']}: {item['detail']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
