# V2 completion and evidence matrix

This matrix maps the thesis-study requirements to repository evidence. “Done”
means implemented and exercised; it does not imply that an assumed parameter
has become experimentally measured.

| Requirement | Status | Authoritative evidence |
|---|---|---|
| Preserve validated v1 | Done | `scripts/run_reproducible_case.py`; fresh 1k regression; v2 is additive |
| Experimental source reconstruction | Done with bounded uncertainty | `config/v2/source_models.yaml`; six generated spectra; Figure 1 |
| Correct experimental beam orientation/profile | Done | tracked production `transport.mac`; Figure 0; release audit |
| Medium, substrate, and air comparison | Done | `study_cases.yaml`; paired environment/M9 tests; `sensitivity_effects.csv` |
| Stable physical anatomy | Done | unchanged `transport_geometry_v1.csv`; input hashes in manifests |
| Neural representation decision | Done | original high-resolution surface retained; matched-atlas null; geometry docs |
| Finite in-body electron eligibility | Done | dual recorded/geometric containment; zero production coordinate exclusions |
| Shell-resolved neural scoring | Done | `all_neural_distance_shells.csv`; Figure 2 |
| Longitudinal and 3D spatial mapping | Done | `all_longitudinal_sectors.csv`; Figure 8 |
| Geometry-matched neural null | Done | `all_neural_nulls.csv`; Figure 3 |
| Neural versus muscle comparison | Done | `all_neural_muscle_metrics.csv`; Figure 4 |
| Regional physical transport | Done | `all_regional_transport.csv`; Results regional table |
| Cannon exposure-series scaling | Done, conditional on reported Gy | `experimental_condition_model_scaling.csv`; Figure 5 |
| Behavioral comparison | Done at supported resolution | `cannon_observations.csv`; report separates compatibility from causality |
| Time-resolved water radiolysis | Done | four neural/muscle 10k cases at 1 ps–~1 µs; Figure 7 |
| Exposure-level radiolysis budget | Done with explicit local-water assumption | `experimental_condition_radiolysis_scaling.csv` |
| Stochastic uncertainty | Done | three independent 1M replicates/source; `replicate_summary_1M.csv` |
| Physical-input sensitivity | Done for primary brackets | twelve paired 1M contrasts; Figure 9 |
| High-stat production | Done | two verified 10M macros/manifests/summaries |
| Navigation-warning audit | Done, residual limitation retained | per-run warning summaries; Figure 6 |
| Reproducible runner | Done | `scripts/v2/run_authoritative_v2.py` |
| Machine-verifiable release | Done | `scripts/v2/audit_v2_release.py`; `release_audit.json` |
| Publication-quality figures/tables | Done | ten PNG/PDF figure pairs and tracked CSV/JSON package |
| Thesis report and executive summary | Done | `THESIS_REPORT.md`; `V2_EXECUTIVE_SUMMARY.md` |
| Limitations and experimental tests | Done | `V2_LIMITATIONS_AND_EXPERIMENTAL_TESTS.md` |

## Deliberately unresolved by simulation

- Exact at-sample spectra and polycapillary transmission require measurement.
- Per-animal liquid depth, posture, and atlas registration require experimental
  imaging or a larger animal-specific ensemble.
- Homogeneous-water G values do not determine intracellular chemistry.
- No modeled quantity establishes molecular activation of LITE-1.
- The neural atlas is a proximity surface, not a nervous absorbed-dose volume.

These are scientific boundaries and proposed follow-up measurements, not hidden
workflow gaps. Details are in the limitations document.
