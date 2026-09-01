# ROS-Worm v2.1 completion matrix

| Requirement | Evidence | Status / boundary |
|---|---|---|
| Preserve validated v2 transport | v2 configs plus additive v2.1 output code | Complete; no neural Geant4 daughter |
| Actual spatial deposited-energy steps | production ROOT hashes, macros, `edep_scoring_metadata.json` | Complete; exact event/step conservation |
| 0.5 µm charged step localization | step-length QC and log signature | Complete after registering `G4StepLimiterPhysics` |
| Original full nervous atlas distances | `score_edep_v2_1.py`, atlas SHA-256 | Complete; no decimated authoritative surface |
| Deposited-energy shells | `production_nervous_surface_edep_shells.csv` | Complete, seven requested shells |
| Analysis-only neural volume | `neural_roi/`, reconstruction report | Complete; exact 276-member set union |
| Resolution convergence | 0.25, 0.5, 1, 2 µm ROI files and table | Complete for volume/same-order dose; not topology |
| Neural absorbed dose | `production_neural_muscle_dose.csv` | Supported with explicit ROI/mass assumptions |
| Muscle comparison | same dose table and Figure 5 | Complete |
| Focused/diffuse 10M production | `production_run_index.csv` | Complete |
| Position/registration/null controls | production control folders | Complete; no significant neural enrichment |
| Source/environment/material/seed sensitivity | `sensitivity/` | Complete for perineural/muscle; 1M neural variants underpowered |
| Actual-edep chemistry normalization | `chemistry/cannon_condition_edep_radiolysis.csv` | Complete for homogeneous water |
| Edep-weighted local spectra | six input spectra and 6×10k run index | Complete |
| Time-resolved chemistry | `edep_weighted_chemistry_timeseries.csv` | Complete, 1 ps–1 µs |
| Focused LITE-1 primary-literature audit | `LITE1_MECHANISTIC_EVIDENCE.md` | Complete |
| Real-kinetics target metric | config and target-interaction sweeps | Level 1 only; target availability |
| LITE-1 activation probability | evidence gate | Unsupported and deliberately omitted |
| Cannon condition summary | `cannon_condition_summary.csv` | Complete; includes 0.5×–2× dosimetry bounds |
| Publication figures | `figures/figure_manifest.json` | Ten PNG/PDF figures, hash verified |
| Reproducibility | `REPRODUCIBILITY.md`, authoritative runner | Complete |
| Skeptical review | `PAPER_READINESS_REVIEW.md` | Complete; claim grades included |
| Machine release audit | `release_audit.json` | 21/21 checks pass |

The package is complete for a bounded physical-plausibility study. Higher-stat
diffuse neural scoring, exact specimen-plane dosimetry/spectra, subject-specific
registration, intracellular chemistry, and a calibrated LITE-1 response model
remain future experimental/modeling work, not hidden release requirements.
