# Tracked v2 validation package

This directory is the compact, version-controlled evidence package generated
by `scripts/v2/collect_v2_results.py`. It contains the data behind the v2 report
without committing the large ROOT files and complete secondary-electron tables
under `results/`.

## Authoritative production cases

| Case | Histories | Environment | Eligible e- births | Within 5 um | Conditional births / whole-worm Gy | Navigation warnings / million |
|---|---:|---|---:|---:|---:|---:|
| Focused W 50 kV nominal | 10,000,000 | NGM/agar + polystyrene | 65,612 | 9,311 (14.19%) | 1.150e6 | 22.0 |
| Diffuse Ag 20 kV nominal | 10,000,000 | M9 + glass | 16,396 | 2,440 (14.88%) | 1.170e6 | 4.2 |

“Within 5 um” means exact distance to the retained high-resolution nervous STL,
not dose inside a nervous volume. “Conditional” means normalized using model
whole-worm mean absorbed dose; it does not reconstruct photons per tube
electron.

## Contents

- `transport_run_index.csv`: one row per collected transport run, including
  seeds, event count, geometry/source choices, exclusions, and warning rates.
- `replicate_summary_1M.csv`: mean, standard deviation, and count for the three
  independent nominal replicates.
- `all_neural_distance_shells.csv`: shell-resolved counts, spectra summaries,
  and normalizations.
- `all_longitudinal_sectors.csv`: equal-length atlas-Y sectors. These are
  coordinate sectors, not neuron-class annotations.
- `all_neural_nulls.csv`: anatomy-preserving rigid neural-atlas perturbations.
- `all_neural_muscle_metrics.csv`: neural-surface, muscle-surface, and physical
  muscle-compartment comparisons.
- `all_regional_transport.csv`: physical-compartment energy deposition and
  absorbed-dose summaries for every collected run.
- `sensitivity_effects.csv`: paired one-at-a-time 1M effects.
- `experimental_condition_model_scaling.csv`: fluence-linear scaling over the
  Cannon exposure conditions.
- `experimental_condition_radiolysis_scaling.csv`: conditional homogeneous-
  water molecule-equivalent energy budgets over those conditions. These assume
  full local thermalization and are not intracellular concentrations.
- `chemistry/` and `chemistry_timeseries_all.csv`: time-resolved homogeneous
  water-radiolysis results, input spectra, and manifests for focused/diffuse
  neural- and muscle-proximity cases.
- `chemistry_neural_muscle_comparison_1us.csv`: direct paired tissue-spectrum
  G-value comparison near the chemistry endpoint.
- `runs/`: compact per-run macros, manifests, and summaries with input hashes.
  The tracked production macros let the release audit verify actual `beamOn`,
  source, direction, and environment commands without the ignored ROOT files.
- `figures/`: publication-resolution PNG and vector PDF figures.
- `release_audit.json`: machine-readable verification of event counts, macro
  direction/source settings, artifact hashes, exclusions, replicate design,
  chemistry times, and figure completeness.
- `v1_regression/`: compact evidence from a fresh 1k v1 execution after the v2
  implementation, including its macro, summary, manifest, and zero-warning
  navigation summary.

Regenerate the complete package using the command in
`docs/v2/REPRODUCIBILITY.md`. Numerical interpretation and limitations are in
`docs/v2/THESIS_REPORT.md`.
