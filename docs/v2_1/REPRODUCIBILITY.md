# ROS-Worm v2.1 reproducibility

## Scope and authority

This document reproduces the tracked v2.1 analysis package. The validated v2
transport architecture remains intact. V2.1 adds spatial energy-deposition
output, an analysis-only neural volume, dose scoring, deposited-energy-driven
water radiolysis, and Level-1 LITE-1-relevant chemical-opportunity metrics.

The authoritative branch is `ai/neural-dose-lite1-v2.1`. The authoritative
compact evidence is `ros_worm_stage1/validation/v2_1/`. The large ROOT files
remain ignored in `ros_worm_stage1/results/`; their SHA-256 hashes are recorded
in the tracked production metadata.

## Software

- Geant4 11.3.2 for the recorded transport and chemistry runs.
- Python environment used for analysis:
  `/home/asunkari/miniconda3/envs/ros/bin/python`.
- Required Python packages include NumPy, pandas, uproot, trimesh, VTK,
  matplotlib, SciPy, and scikit-image.
- Transport and chemistry random seeds are recorded in their manifests and run
  indexes. Critical STL, configuration, spectrum, ROOT, and figure hashes are
  tracked with the results.

Paths in old run manifests are provenance records and may refer to the worktree
where the run was made. Reproduction is content-hash based; do not require that
the old absolute path still exist.

## Fast release verification

From the repository root:

```bash
/home/asunkari/miniconda3/envs/ros/bin/python \
  ros_worm_stage1/scripts/v2_1/run_authoritative_v2_1.py --stage audit
```

This checks the two 10M production summaries, spatial-step energy conservation,
coordinate filtering, active 0.5 µm step-limit macros, neural source members,
ROI convergence, neural/muscle endpoints, matched nulls, sensitivity ensemble,
six 10k chemistry cases, evidentiary gate, required documentation, and hashes
of all ten figures. It writes `validation/v2_1/release_audit.json` and fails if
an invariant is broken.

Rebuild figures from tracked compact results with `--stage figures`. Rebuild the
deposited-energy chemistry scaling and figures with `--stage analysis`. These
commands do not rerun transport or Geant4-DNA.

## Production transport provenance

The corrected runs are:

- `v2_1_production_focused_nominal_ngm_10M_steplimited0p5`
- `v2_1_production_diffuse_nominal_m9_10M_steplimited0p5`

They were generated with `scripts/v2_1/run_v2_1_case.py`, the nominal v2 source
and environment definitions, 10,000,000 histories, spatial step output enabled,
and a 0.5 µm charged-particle step limit. Exact commands and resolved parameters
are retained in each ignored result directory's `v2_1_run_manifest.json`; the
tracked copies are under `validation/v2_1/production/{focused,diffuse}/`.

Do not reuse any v2.1 output whose log lacks:

```text
[ROS-WORM][STEP_LIMIT] charged_max_step_um=0.5
```

The earlier v2.1 1M files are explicitly marked `SUPERSEDED.md`: they exposed
the missing `G4StepLimiterPhysics` defect and are retained only as an audit
trail.

## Rebuilding the analysis-only neural ROI

```bash
/home/asunkari/miniconda3/envs/ros/bin/python \
  ros_worm_stage1/scripts/v2_1/build_neural_roi_v2_1.py \
  --source-manifest openworm_geometry/compartment_pipeline/aggregate_testE_nervous_no_cube/testE_aggregate_with_nervous_no_cube.csv \
  --placement-manifest ros_worm_stage1/config/transport_geometry_v1.csv \
  --reference-stl openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl \
  --outdir ros_worm_stage1/validation/v2_1/neural_roi \
  --pitches-um 0.25,0.5,1,2 --density-g-cm3 1.04 \
  --surface-samples 30000 --seed 20260831
```

The authoritative membership test is the exact set union of 276 individually
closed source objects. The body-clipped voxel grids are resolution/fidelity
diagnostics and alternate ROI definitions; none is installed as Geant4 matter.

## Scoring and controls

`score_edep_v2_1.py` reads actual deposited-energy steps from a ROOT file and
produces shell, ROI dose, process/particle, uncertainty, and local spectrum
tables. `score_position_sensitivity_v2_1.py` compares pre/mid/post/hybrid
position conventions. `score_edep_controls_v2_1.py` performs registration and
matched-atlas null tests. `collect_v2_1_results.py` copies only compact results
and confirms the corrected macro/log signature.

The authoritative deposited-energy coordinate is the midpoint of a charged
step and the post-step interaction point for a neutral step. Whole-worm event
energy and summed positive steps must agree exactly. Nonfinite and out-of-body
positions are excluded and counted; both production runs contain zero.

## Chemistry

`build_edep_weighted_chemistry_spectra.py` builds six spectra: focused/diffuse
times exact-neural, 0–5 µm perineural, and body-wall muscle. Each was run for
10,000 Geant4-DNA chemistry histories using seeds `319057` and `720191`. The
compact time series and hashes are recorded in `chemistry_run_index.csv`.

`calculate_edep_radiochemistry_v2_1.py` multiplies local deposited energy by
the simulated homogeneous-water G values and evaluates the transparent
pseudo-first-order competition model in
`config/v2_1/lite1_target_chemistry.yaml`. It does not calculate intracellular
concentration, receptor occupancy, gating, or phenotype probability.

## Expected headline checks

- 10M histories in each production condition.
- Focused/diffuse positive spatial steps: 1,947,267 / 510,833.
- Exact energy conservation and zero invalid/out-of-body deposition records.
- Exact-union neural/whole-worm mean-dose ratio: 0.778 ± 0.101 focused and
  0.969 ± 0.224 diffuse (Monte Carlo standard errors only).
- Muscle/whole-worm ratio: 1.067 ± 0.029 and 1.089 ± 0.058.
- Deposited energy within 5 µm of the original surface: 14.32% and 14.73%.
- Release audit reports `passed: true`.

Experimental dosimetry, atlas registration, ROI definition/density, source and
environment assumptions are separate model uncertainties; the reported Monte
Carlo standard errors are not total uncertainty.
