# Authoritative reproduction procedure

## Dependencies

The validated host used Geant4 11.3.2 with ROOT, Python 3, PyROOT, VTK,
trimesh, pandas, NumPy, matplotlib, and PyYAML. Git LFS geometry objects must be
materialized; pointer files are not usable STL inputs.

If the default `python3` lacks VTK/pandas/trimesh, pass a compatible interpreter
with `--analysis-python` or set `ROSWORM_ANALYSIS_PYTHON`. Codex desktop discovers
its bundled scientific Python automatically.

## Transport

Run from the repository root. Always falsify with 100k before production:

```bash
python3 ros_worm_stage1/scripts/run_reproducible_case.py \
  --case focused_avoidance_50kv --events 100000 \
  --run-name validation_focused_100k

python3 ros_worm_stage1/scripts/run_reproducible_case.py \
  --case diffuse_paralysis_20kv --events 100000 \
  --run-name validation_diffuse_100k
```

Production commands:

```bash
python3 ros_worm_stage1/scripts/run_reproducible_case.py \
  --case focused_avoidance_50kv --events 10000000 --threads 32 \
  --run-name production_focused_10M_v1

python3 ros_worm_stage1/scripts/run_reproducible_case.py \
  --case diffuse_paralysis_20kv --events 10000000 --threads 32 \
  --run-name production_diffuse_10M_v1
```

Each result directory contains the literal macro, ROOT output, transport log,
regional table, filtered secondary tables/spectra, navigation-warning analysis,
full-resolution neural distances and threshold scan, and `run_manifest.json`.
The runner refuses to overwrite a nonempty result directory.

## Geometry QC and volumetric falsification

```bash
python3 ros_worm_stage1/scripts/qc_geometry_v1.py \
  --secondaries ros_worm_stage1/results/production_focused_10M_v1/secondaries.csv \
  --samples 20000 \
  --outdir ros_worm_stage1/results/geometry_qc_highstat_v1
```

This is the deciding test for neural representations. Do not promote a derived
volume without convergence in surface error, morphology, volume, and scoring.

## Water radiolysis

The chemistry source must be the 5-µm near-neural electron-birth spectrum from
the corresponding transport run:

```bash
python3 ros_worm_stage1/scripts/run_chemistry_spectrum.py \
  --spectrum ros_worm_stage1/results/production_focused_10M_v1/nervous_surface_scoring/electron_spectrum_near_nervous_surface.csv \
  --outdir ros_worm_stage1/results/chemistry_focused_near_neural_10k_v1 \
  --events 10000 --threads 8

python3 ros_worm_stage1/scripts/run_chemistry_spectrum.py \
  --spectrum ros_worm_stage1/results/production_diffuse_10M_v1/nervous_surface_scoring/electron_spectrum_near_nervous_surface.csv \
  --outdir ros_worm_stage1/results/chemistry_diffuse_near_neural_10k_v1 \
  --events 10000 --threads 8
```

These are homogeneous liquid-water G values per 100 eV at 1 µs. The spectrum
is sampled as independent source electrons, so the result is not a spatially
coupled cellular chemistry calculation.

## Regenerate tracked tables and figures

```bash
MPLCONFIGDIR=/tmp/rosworm-mpl \
python3 ros_worm_stage1/scripts/build_release_artifacts_v1.py
```

Compare new tables with `ros_worm_stage1/validation/v1/`. Exact Monte Carlo
identity requires the same Geant4 build, thread count, and seeds; scientific
validation should focus on uncertainty-compatible aggregate agreement and zero
invalid/out-of-body electron records.
