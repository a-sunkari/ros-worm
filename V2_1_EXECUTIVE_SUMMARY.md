# ROS-Worm v2.1 executive summary

> **Validated baseline, superseded for final numeric reporting.** The architecture
> and methodological findings here remain valid, but final paper numbers use the
> 100M campaigns in [`FINAL_EXECUTIVE_SUMMARY.md`](FINAL_EXECUTIVE_SUMMARY.md)
> and [`FINAL_PROJECT_STATUS.md`](FINAL_PROJECT_STATUS.md).

## What changed

V2.1 replaces secondary-electron birth proximity as the primary neural result
with actual Geant4 deposited-energy scoring. It retains the stable non-neural
transport geometry, scores every positive in-body energy-deposition step
against the original high-resolution nervous atlas, and defines an analysis-
only neural volume from the set-theoretic union of 276 verified closed source
objects. The neural volume is never placed in Geant4.

The chemistry budget now uses actual local deposited energy and Geant4-DNA
water G values conditioned on deposited-energy-weighted local electron
spectra. A focused literature audit supports only Level-1 LITE-1-relevant
chemical opportunities—not an activation probability.

## Main numerical results

Two corrected nominal production cases contain 10 million histories each. An
implementation audit discovered that the legacy `G4UserLimits` had no active
step-limiter process; preliminary spatial results were invalid. Production
registers `G4StepLimiterPhysics`, verifies a 0.5 micrometre charged-step limit,
uses neutral post-step interaction positions, exactly conserves saved step
versus event energy, and has zero invalid or out-of-body scoring coordinates.

The body-clipped neural ROI volume is stable to 3.9% from 0.25 to 2 micrometre
pitch. At 0.25 micrometres, symmetric surface error is p50 0.119, p95 0.246,
and p99 0.522 micrometres, although a roughly 31 micrometre sampled maximum
remains in local outliers.

Using exact member-union classification and the 0.25 micrometre mass proxy:

| Irradiation | Neural/whole dose | MC standard error | Muscle/whole dose | MC standard error |
|---|---:|---:|---:|---:|
| Focused nominal + NGM | 0.778 | 0.101 | 1.067 | 0.029 |
| Diffuse nominal + M9 | 0.969 | 0.224 | 1.089 | 0.058 |

Voxel-specific neural ratios span 0.819–0.912 focused and 0.913–1.127 diffuse.
Full-production atlas-registration brackets are 1.00–1.28 and 0.70–1.42 of
baseline. Neural dose is therefore defensible as a bounded analysis-only mean
dose, not as a precisely known dose to every neurite.

Actual deposited-energy fractions within 5 micrometres of the original
nervous surface are 14.322% focused and 14.732% diffuse. Matched-atlas null
ratios are only 1.022 and 1.039, with empirical p values 0.308 and 0.231. The
perineural fraction is anatomically referenced but not neurally enriched.

## Radiochemistry and LITE-1 boundary

Deposited-energy-weighted spectrum substitution changes 1 microsecond water
`G(OH)` by about −5.6% to −7.2% and `G(H2O2)` by +1.6% to +3.4% relative to
v2 birth-count spectra. The primary advance is absolute normalization to local
deposited energy.

Conditionally treating reported Gy as whole-worm mean dose, the focused 0.2
Gy/s × 10 s condition maps to 1.56 Gy neural and 2.13 Gy muscle. The focused 1
Gy/s × 10 s condition maps to 7.78 Gy neural and 10.67 Gy muscle. Diffuse
0.19–0.74 Gy/s × 20 s maps to 3.68–14.35 Gy neural and 4.14–16.11 Gy muscle.
All values also carry the Cannon setup's approximate 0.5×–2× dosimetry
interval.

At approximately 1 microsecond, the 2 Gy focused condition corresponds to
about `1.21×10^6` neural OH and `0.803×10^6` neural H2O2 homogeneous-water
molecule equivalents. These are not intracellular concentrations or measured
biological ROS.

Published aqueous rates for OH + Trp and OH + cysteine, plus a PRDX-family
H2O2 bracket, are applied across explicit target-concentration and background-
scavenging sweeps. The resulting interaction opportunities span orders of
magnitude because those biological parameters are unknown. Primary LITE-1
literature is contradictory to a simple monotone ROS model: Trp residues are
critical for photoreception; C44/PRDX-linked redox effects are plausible; and
H2O2 can also inhibit/deactivate LITE-1 photosensation. No receptor-open
probability is reported.

## Scientific conclusion

The model supports a bounded statement: Cannon/Bolding-like X-ray exposures
deposit ordinary, same-order dose in neural and muscle anatomy and rapidly
produce homogeneous-water radiolysis products that are chemically capable of
interacting with Trp/redox motifs. It does not support neural-selective
transport, a privileged nervous proximity enrichment, intracellular ROS
concentrations, LITE-1 gating, or causal proof that radiolysis mediates the
behavior.

The package is suitable for review by Dr. Bolding. Manuscript drafting is
reasonable as a physical-plausibility/modeling study, but a strong mechanistic
paper should first measure at-sample spectrum/dosimetry, worm/atlas
registration, and LITE-1-dependent responses under controlled scavenger/redox
perturbations.

## Where to review

- Methods: `docs/v2_1/METHODS.md`
- Results: `docs/v2_1/RESULTS.md`
- Neural reconstruction: `docs/v2_1/NEURAL_VOLUME_RECONSTRUCTION.md`
- LITE-1 evidence: `docs/v2_1/LITE1_MECHANISTIC_EVIDENCE.md`
- Reviewer audit: `docs/v2_1/PAPER_READINESS_REVIEW.md`
- Requirement audit: `docs/v2_1/COMPLETION_MATRIX.md`
- Reproduction: `docs/v2_1/REPRODUCIBILITY.md`
- Tables/figures: `ros_worm_stage1/validation/v2_1/`
