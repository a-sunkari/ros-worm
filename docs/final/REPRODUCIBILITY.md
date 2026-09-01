# Final authoritative reproducibility procedure

## Compact release regeneration

From the repository root in the tracked `ros` Conda environment:

```bash
conda run -n ros python ros_worm_stage1/scripts/final/run_compact_release.py
```

This deterministically regenerates paper tables, all nine PNG/PDF figures, the assembled manuscript, and `validation/final/release_audit.json`. The audit fails on wrong branch, ROOT/ROI hash, history count, step/event energy mismatch, insufficient neural precision, incomplete null/chemistry ensembles, stale/missing figures, or missing manuscript artifacts.

## Authoritative nominal transport

The ignored raw directories are:

- `ros_worm_stage1/results/final_highstat_focused_nominal_ngm_100M`
- `ros_worm_stage1/results/final_highstat_diffuse_nominal_m9_100M`

Each contains expanded `transport.mac`, `run_manifest.json`, `v2_1_run_manifest.json`, `transport.log`, and `output0.root`. The authoritative ROOT SHA-256 values are `9ca894f34111914a9722922185ab4c63c0f21b3aba7e37e46e9d202b32188e91` focused and `6f0dccd1e504f44e6ea7889c17bfaf0b23e4aaa01df229a5548d68d3ba0f6d4d` diffuse. Seeds are recorded in the manifests. Compact copies of macros/manifests, scoring metadata, and hash indices are tracked under `validation/final/production/`.

These runs use Geant4 11.3.2, Livermore electromagnetic physics, the validated v2 source/environment definitions, saved spatial deposited-energy steps, and active 0.5 µm charged-particle step limiting. They should only be rerun if an authoritative input hash or physics implementation changes.

## Analysis order

1. Score actual deposited-energy steps and exact member-union/voxel neural dose using the v2.1 anatomy scorer.
2. Run `audit_highstat_statistics.py` for event-level covariance and bootstrap statistics.
3. Run `audit_neural_roi_outliers.py` and full registration scoring.
4. Score nervous and muscle surfaces; run 99 matched-atlas controls on fixed one-million-event prefixes.
5. Build local edep-weighted spectra and run the six seeded 10k Geant4-DNA chemistry cases.
6. Run `build_final_tables.py`, `make_paper_figures.py`, and `audit_paper_release.py` via the compact runner.

The exact commands and arguments are represented by the final scripts; manual copying of numbers into paper tables is not authoritative.

## Reproduction boundary

Large ROOT and chemistry event directories are intentionally ignored. A clean clone can audit tracked compact artifacts and hashes but cannot recompute raw-event bootstraps without restoring or regenerating the two 100M ROOT files. No biological measurement, specimen-plane spectrum, or intracellular chemistry is implied by computational reproducibility.
