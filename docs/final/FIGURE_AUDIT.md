# Publication figure audit

## Decision summary

The previous nine-figure main-text set diluted the central physical argument and mixed primary results with validation detail. The redesigned paper uses six main figures and two supplementary figures. All quantitative panels are regenerated from tracked CSV/JSON/configuration data; existing PNG files are never used as analytical inputs.

| Previous figure | Decision | Final location | Reason |
|---|---|---|---|
| 1. Geometry/workflow | Redesigned substantially | Main Figure 1 | Retains the two experimental geometries, adds source-spectrum brackets and the actual OpenWorm anatomy, and removes presentation-style boxes and workflow prose. |
| 2. Neural ROI validation | Redesigned substantially | Main Figure 2 | Combines the real atlas/ROI overlay and anatomical zoom with volume, surface-error, and dose convergence on one coherent resolution axis. |
| 3. Regional dose | Redesigned and merged | Main Figure 3a | Replaces large bars with point estimates, covariance-aware Monte Carlo intervals, a whole-worm reference, and separately encoded ROI-pitch ranges. |
| 4. Surface deposition/nulls | Redesigned and merged | Main Figure 3b–d | Places cumulative nervous/muscle surface deposition beside the regional dose result and shows all 99 matched-atlas controls rather than a generic boxplot. |
| 5. Longitudinal deposition | Redesigned; supplementary | Supplementary Figure S1 | The aligned spatial profiles are useful validation but do not add a separate main-text mechanistic claim after regional and surface analyses. |
| 6. Cannon dose mapping | Redesigned substantially | Main Figure 4 | Replaces connected fluence-linear lines with discrete experimental-condition estimates and a separate factor-of-two dosimetry envelope. |
| 7. Radiolysis | Redesigned substantially | Main Figure 5 | Separates short-lived radicals from molecular/ionic products, uses logarithmic time, and directly labels species while retaining focused/diffuse line styles. |
| 8. LITE-1 chemistry | Redesigned substantially | Main Figure 6 | Keeps the result quantitative: target/scavenger parameter matrices and interval estimates across exposures. No receptor cartoon or activation metric is introduced. |
| 9. Uncertainty | Redesigned; supplementary | Supplementary Figure S2 | History convergence and separated uncertainty sources remain important support, but the central Monte Carlo and reconstruction intervals already appear in Figure 3a. |

No validated numerical result was changed during redesign. Main-text removal means relocation, not deletion: the spatial and detailed uncertainty evidence remains in the supplementary directory.

## Narrative role of the final figures

1. **Figure 1 — modeled experiment and anatomy.** The two actual irradiation configurations, spectral uncertainty, and the anatomy used for regional and surface-referenced analysis.
2. **Figure 2 — validity of the neural scoring model.** The analysis-only ROI follows the original atlas sufficiently for whole-system mean-dose inference, and the scientific dose endpoint is stable across tested pitch.
3. **Figure 3 — central dosimetric result.** Neural and muscle doses are whole-worm-order; both surfaces sample a substantial deposition field; the native neural atlas is not enriched above matched rigid controls.
4. **Figure 4 — link to Cannon conditions.** Actual experimental exposures map to multi-gray neural and muscle doses without implying a nonlinear modeled response.
5. **Figure 5 — radiochemical timing.** Actual local energy deposition yields prompt water-radiolysis chemistry from picoseconds through microseconds.
6. **Figure 6 — supported LITE-1 boundary.** Published kinetics admit broad Trp-like and thiol-like interaction opportunities, with uncertainty dominated by target/scavenger assumptions; receptor activation is not calculated.

## Authoritative source trace

| Figure | Machine-readable inputs |
|---|---|
| 1 | `config/v2/study_cases.yaml`, `config/v2/source_models.yaml`, `config/v2/spectra/*.csv`, original anatomy meshes, 0.25 µm ROI NPZ |
| 2 | `validation/v2_1/neural_roi/neural_roi_resolution_convergence.csv`, `validation/final/production/production_neural_muscle_dose.csv`, `validation/final/statistics/final_nominal_dose_statistics.csv`, original atlas and ROI NPZ |
| 3 | `validation/final/statistics/final_nominal_dose_statistics.csv`, `validation/final/production/production_neural_muscle_dose.csv`, `validation/final/tables/neural_muscle_surface_edep_shells.csv`, `validation/final/nulls/*/nervous_surface_edep_matched_nulls.csv`, null metadata JSON |
| 4 | `validation/final/tables/final_cannon_condition_table.csv` |
| 5 | `validation/final/chemistry/edep_weighted_chemistry_timeseries.csv` |
| 6 | `validation/final/chemistry/lite1_target_interaction_sweep.csv`, `validation/final/tables/final_cannon_condition_table.csv` |
| S1 | `validation/final/tables/longitudinal_edep_profiles.csv` |
| S2 | `validation/final/statistics/history_convergence.csv`, `validation/final/tables/final_uncertainty_budget.csv` |

Exact hashes for all tabular/configuration sources and all exports are recorded in `ros_worm_stage1/validation/publication_figures/publication_figure_manifest.json`.

## Visual review outcome

The final set was inspected as individual 600 dpi panels and as color/grayscale contact sheets at 182 mm-equivalent width. The redesign avoids default plotting-library colors, filled ratio bars, arbitrary connecting lines, redundant main figures, data-obscuring legends, and infographic-like mechanistic claims. Shapes and line styles preserve focused/diffuse and neural/muscle distinctions in grayscale. The remaining local rasterization is confined to million-facet anatomy point clouds; axes and text remain vector/editable.
