# ROS-Worm v2 reproducibility

## Scope

This is the authoritative procedure for the thesis v2 study. It preserves the
validated v1 transport anatomy and chem6-derived chemistry lifecycle while
adding source ensembles, experimental medium, shell-resolved anatomy scoring,
matched neural nulls, independent seeds, sensitivity cases, and tracked
figures/tables.

## Software and inputs

- Geant4 version is recorded by every `run_manifest.json` (the completed study
  used Geant4 11.3.2).
- The runner hashes the transport manifest, material map, selected spectrum,
  source-model config, and high-resolution neural STL.
- Random seeds, actual macro, event count, environment, spectrum variant, and
  git status are recorded per run.
- Analysis requires Python with NumPy, pandas, VTK, ROOT, PyYAML, and
  Matplotlib. The tested interpreter is
  `/home/asunkari/miniconda3/envs/ros/bin/python`.

## One command

From the repository root:

```bash
/home/asunkari/miniconda3/envs/ros/bin/python \
  ros_worm_stage1/scripts/v2/run_authoritative_v2.py --tier production
```

The tiers are cumulative:

- `smoke`: focused and diffuse 100k cases.
- `validation`: smoke plus three independent 1M nominal replicates per source
  and paired 1M tests of spectrum, experimental medium, focused-beam position
  and width, diffuse liquid depth, and water-versus-tissue materials.
- `production`: validation plus one 10M focused case, one 10M diffuse case,
  10k chemistry for each near-neural spectrum, and artifact collection.

The runner reuses a case only when its result directory already contains a
`run_manifest.json`; it never silently overwrites a prior run.

The production tier ends with `audit_v2_release.py`. The audit independently
checks the actual `/run/beamOn` values, source direction and spectrum commands,
manifest artifact hashes, eligible-coordinate exclusions, replicate and
sensitivity design, chemistry reporting times, and figure pairs. Its tracked
output is `ros_worm_stage1/validation/v2/release_audit.json`.

## One-case examples

Focused nominal 100k with NGM/agar and dish:

```bash
/home/asunkari/miniconda3/envs/ros/bin/python \
  ros_worm_stage1/scripts/v2/run_v2_case.py \
  --case focused_avoidance --spectrum nominal \
  --environment ngm_agar_dish --events 100000 \
  --seed-a 11001 --seed-b 22002 \
  --run-name my_focused_100k --null-count 4
```

Diffuse nominal 100k with M9 and glass:

```bash
/home/asunkari/miniconda3/envs/ros/bin/python \
  ros_worm_stage1/scripts/v2/run_v2_case.py \
  --case diffuse_paralysis --spectrum nominal \
  --environment m9_drop_glass --events 100000 \
  --seed-a 11002 --seed-b 22003 \
  --run-name my_diffuse_100k --null-count 4
```

## Rebuild compact tables and figures

```bash
MPLCONFIGDIR=/tmp/rosworm-mpl \
/home/asunkari/miniconda3/envs/ros/bin/python \
  ros_worm_stage1/scripts/v2/collect_v2_results.py
```

Large ROOT files and full secondary tables remain under the ignored
`ros_worm_stage1/results/` tree. Compact manifests, summaries, shell tables,
null results, production macros, chemistry time series, PNG figures, and vector
PDFs are tracked under `ros_worm_stage1/validation/v2/`. The release audit
automatically falls back to those tracked compact production records when the
large local results are absent.

## Normalization boundary

`births_per_whole_worm_Gy_conditional` assumes that the experimental reported
Gy can be identified with the model whole-worm mean absorbed dose. This is a
useful dose-normalized comparison, not an independent reconstruction of tube
fluence. Focused dosimetry carries the paper's approximate factor-of-two
uncertainty. Diffuse targeted-cone histories are importance-conditioned on
crossing the worm target plane, so histories per tube electron are undefined.

Dose-rate conditions reuse the same transport because the model is linear and
does not contain dose-rate-dependent physics. Counts and electron-energy sums
are scaled by total dose; chemistry G values are not rerun for mathematically
identical spectra.

## Production provenance note

The two 10M transport manifests record commit `105cb56` plus an explicit dirty
working-tree list. The transport-relevant uncommitted scorer and chemistry
changes shown there were committed without alteration in checkpoint `eef465a`;
the collector preserves the original manifests rather than rewriting history.
Critical input files are independently hash-checked by the release audit. This
is transparent and reconstructable, though a future archival rerun from a clean
tag would give still stronger provenance.
