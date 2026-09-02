# ROS-Worm

OpenWorm-informed Geant4 / Geant4-DNA modeling of X-ray transport and radiolysis in *Caenorhabditis elegans*, motivated by the Bolding/Cannon X-genetics experiments.

## Start here

Future humans and AI agents should read, in order:

1. [`AGENTS.md`](AGENTS.md) — operating rules and authoritative paths.
2. [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md) — what is working now and what is not.
3. [`docs/SCIENTIFIC_CONTEXT.md`](docs/SCIENTIFIC_CONTEXT.md) — Bolding/Cannon literature and the modeling question.
4. [`docs/GEOMETRY_AND_NERVOUS_SYSTEM.md`](docs/GEOMETRY_AND_NERVOUS_SYSTEM.md) — the anatomy/mesh problem and current nervous-system strategy.
5. [`docs/VALIDATION_AND_NEXT_STEPS.md`](docs/VALIDATION_AND_NEXT_STEPS.md) — known results, warnings, and completion plan.
6. [`V2_EXECUTIVE_SUMMARY.md`](V2_EXECUTIVE_SUMMARY.md) — thesis-study result and its scientific boundary.
7. [`docs/v2/THESIS_REPORT.md`](docs/v2/THESIS_REPORT.md) — v2 methods, validation, results, and discussion.
8. [`docs/v2/COMPLETION_MATRIX.md`](docs/v2/COMPLETION_MATRIX.md) — requirement-to-evidence audit.
9. [`V2_1_EXECUTIVE_SUMMARY.md`](V2_1_EXECUTIVE_SUMMARY.md) — actual neural dose and LITE-1-relevant chemistry.
10. [`docs/v2_1/THESIS_REPORT.md`](docs/v2_1/THESIS_REPORT.md) — validated v2.1 baseline and evidentiary boundary.
11. [`FINAL_PROJECT_STATUS.md`](FINAL_PROJECT_STATUS.md) — final go/no-go decision and remaining experimental limits.
12. [`manuscript/ROS_WORM_MANUSCRIPT_REWRITE.md`](manuscript/ROS_WORM_MANUSCRIPT_REWRITE.md) — current coauthor-review manuscript using the final high-statistics results and publication figures.
13. [`manuscript/SUPPLEMENTARY_FIGURES.md`](manuscript/SUPPLEMENTARY_FIGURES.md) — assembled supplementary figure set.

The active implementation is under [`ros_worm_stage1/`](ros_worm_stage1/). The older `ros_worm_full_pipeline_v2` staging copy, build trees, scratch backups, and command-dump notes were removed from the working tree during the August 2026 cleanup; their history remains in git.

## Authoritative v2 run

The cumulative study runner is:

```bash
/home/asunkari/miniconda3/envs/ros/bin/python \
  ros_worm_stage1/scripts/v2/run_authoritative_v2.py --tier smoke
```

Use `--tier validation` for the independent 1M replicates and primary
sensitivity brackets, or `--tier production` for the full 10M transport + 10k
chemistry package. Existing provenance-complete results are reused. See
[`docs/v2/REPRODUCIBILITY.md`](docs/v2/REPRODUCIBILITY.md).

## Authoritative v2.1 verification

The final methodological upgrade is additive and lives under `config/v2_1`,
`scripts/v2_1`, and `validation/v2_1`. Verify the tracked package with:

```bash
/home/asunkari/miniconda3/envs/ros/bin/python \
  ros_worm_stage1/scripts/v2_1/run_authoritative_v2_1.py --stage audit
```

Use `--stage figures` to regenerate all ten figures from compact results or
`--stage analysis` to regenerate deposited-energy radiochemistry and figures.
See [`docs/v2_1/REPRODUCIBILITY.md`](docs/v2_1/REPRODUCIBILITY.md).

## Paper-ready final release

The final 100-million-history-per-configuration results, event-level statistical
audit, 99-member matched-null ensembles, local-edep chemistry, paper figures,
and manuscript are under `ros_worm_stage1/validation/final/`, `docs/final/`,
and `manuscript/`. Regenerate and verify all compact artifacts with:

```bash
/home/asunkari/miniconda3/envs/ros/bin/python \
  ros_worm_stage1/scripts/final/run_compact_release.py
```

See [`docs/final/REPRODUCIBILITY.md`](docs/final/REPRODUCIBILITY.md). The raw
100M ROOT files are ignored but identified by SHA-256 in the tracked production
index and release audit.

The manuscript's authoritative six main and two supplementary publication
figures are regenerated separately from the tracked compact outputs:

```bash
MPLCONFIGDIR=/tmp/mpl-pub /home/asunkari/miniconda3/envs/ros/bin/python \
  ros_worm_stage1/scripts/make_publication_figures_final.py \
  --repo . --outdir ros_worm_stage1/validation/publication_figures

/home/asunkari/miniconda3/envs/ros/bin/python \
  ros_worm_stage1/scripts/audit_publication_figures.py \
  --repo . --figure-root ros_worm_stage1/validation/publication_figures
```

See [`docs/final/FIGURE_STYLE_GUIDE.md`](docs/final/FIGURE_STYLE_GUIDE.md) and
[`docs/final/FIGURE_AUDIT.md`](docs/final/FIGURE_AUDIT.md).

## Validated v1 run

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

## Important interpretation

The high-resolution nervous-system STL is anatomically useful but not a clean
watertight solid. Transport therefore still uses **no physical nervous daughter
volume**. V2.1 scores actual deposited-energy steps against the original surface
and an analysis-only exact union of 276 verified closed source objects. This
supports an explicitly defined mean neural ROI dose, not cell-resolved dose.
Geant4-DNA outputs remain simulated homogeneous-water radiolysis yields, not
measured biological ROS or a prediction of LITE-1 activation.

The paper-ready high-statistics analysis likewise finds no compelling neural-
specific transport enhancement. Actual energy within 5 µm of the nervous
surface is 14.23% focused and 14.39% diffuse, essentially the same as the muscle-
surface fractions. Analysis-only neural/whole-worm dose is `0.932±0.034`
focused and `0.873±0.062` diffuse (Monte Carlo SE); muscle is `1.060±0.009`
and `1.083±0.018`. Transport is broadly available rather than neural-selective.
