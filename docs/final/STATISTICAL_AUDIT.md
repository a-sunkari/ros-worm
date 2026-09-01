# Final statistical audit

## Independence and estimator

One Geant4 primary history per unique event ID is the independent unit. All steps from a history are aggregated before statistics. The neural or muscle dose ratio shares histories and energy with the whole-worm denominator, so its standard error includes event-level numerator–denominator covariance. The reported 95% Monte Carlo interval is the covariance delta interval; 2,000 Poisson(1) event-weight bootstrap replicates provide a nonparametric check while preserving complete histories.

## Final precision and tail diagnostics

| Irradiation | ROI | Ratio | SE | Relative SE | 95% delta interval | 95% bootstrap interval | Raw contributors | Effective contributors | Largest event share |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Focused | neural | 0.9316 | 0.0339 | 3.6% | 0.8651–0.9980 | 0.8636–0.9993 | 1,264 | 753 | 0.43% |
| Focused | muscle | 1.0600 | 0.0093 | 0.88% | 1.0417–1.0783 | 1.0426–1.0777 | 15,707 | 12,515 | 0.039% |
| Diffuse | neural | 0.8730 | 0.0616 | 7.1% | 0.7522–0.9938 | 0.7594–1.0013 | 318 | 200 | 1.01% |
| Diffuse | muscle | 1.0834 | 0.0185 | 1.7% | 1.0473–1.1196 | 1.0477–1.1212 | 4,077 | 3,349 | 0.076% |

Delta and bootstrap widths agree within 10%. With at least 318 raw and 200 energy-effective neural contributors, no single event dominates. Normal intervals are adequate for the stated Monte Carlo sampling uncertainty, but bootstrap intervals remain tracked.

## Convergence and replication

Prefix estimates are tracked at 1, 2, 5, 10, 20, 50, and 100 million histories. Early neural estimates fluctuate as predicted for rare deposition, then stabilize with shrinking SE. Independent earlier 10M runs are consistent with the 100M estimates: focused neural z=1.44, diffuse neural z=−0.41, focused muscle z=−0.22, and diffuse muscle z=−0.09. Prefixes are not mislabeled as independent replicates.

## Interpretation of intervals

- Monte Carlo intervals are sampling intervals conditional on one model.
- ROI-pitch and registration results are deterministic assumption ranges.
- source/environment results are one-at-a-time sensitivity estimates; the one-million-history neural variants are underpowered and are not used as precise neural-dose effects.
- Cannon's factor-of-two uncertainty is an external multiplicative dosimetry interval on absolute Gy.

These are not combined into a single Gaussian error. The final publication table retains separate columns and descriptions.

Machine-readable source: `ros_worm_stage1/validation/final/statistics/` and `validation/final/tables/final_uncertainty_budget.csv`.
