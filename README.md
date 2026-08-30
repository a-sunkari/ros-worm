# ROS-Worm

OpenWorm-informed Geant4 / Geant4-DNA modeling of X-ray transport and radiolysis in *Caenorhabditis elegans*, motivated by the Bolding/Cannon X-genetics experiments.

## Start here

Future humans and AI agents should read, in order:

1. [`AGENTS.md`](AGENTS.md) — operating rules and authoritative paths.
2. [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md) — what is working now and what is not.
3. [`docs/SCIENTIFIC_CONTEXT.md`](docs/SCIENTIFIC_CONTEXT.md) — Bolding/Cannon literature and the modeling question.
4. [`docs/GEOMETRY_AND_NERVOUS_SYSTEM.md`](docs/GEOMETRY_AND_NERVOUS_SYSTEM.md) — the anatomy/mesh problem and current nervous-system strategy.
5. [`docs/VALIDATION_AND_NEXT_STEPS.md`](docs/VALIDATION_AND_NEXT_STEPS.md) — known results, warnings, and completion plan.

The active implementation is under [`ros_worm_stage1/`](ros_worm_stage1/). The older `ros_worm_full_pipeline_v2` staging copy, build trees, scratch backups, and command-dump notes were removed from the working tree during the August 2026 cleanup; their history remains in git.

## Authoritative run

From the repository root, a focused validation run is:

```bash
python3 ros_worm_stage1/scripts/run_reproducible_case.py \
  --case focused_avoidance_50kv --events 100000 \
  --run-name validation_focused_100k
```

Use `diffuse_paralysis_20kv` for the Cannon/Bolding diffuse condition. The
runner builds transport, records the actual macro and hashes, extracts regional
results, audits navigation warnings, excludes invalid/out-of-body records, and
performs exact closest-surface scoring against the original high-resolution
neural atlas. See [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) for the
10M transport and 10k chemistry commands.

## One-sentence project goal

Reproduce the X-ray conditions used in the Bolding/Cannon *C. elegans* work, compute physically grounded regional energy deposition and secondary-electron spectra, feed those spectra into Geant4-DNA radiolysis chemistry, and determine whether the resulting near-neural/radiolytic signal is spatially and dose-wise compatible with the observed LITE-1-dependent behavioral responses.

## Important limitation

The high-resolution nervous-system STL is anatomically useful but not a clean
watertight solid. The validated method is therefore **transport without a
physical nervous daughter volume plus post-processing against the original
high-resolution nervous surface**. This is a secondary-electron birth-proximity
metric, not nervous-tissue absorbed dose. Geant4-DNA outputs are simulated water
radiolysis yields, not measured biological ROS.
