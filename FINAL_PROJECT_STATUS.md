# Final ROS-Worm project status

## Overall readiness: COAUTHOR REVIEW READY

The computational study is complete for its bounded physical-plausibility claim. A journal-style manuscript, nine main figures, supplementary package, machine-readable tables, hostile-review response, and deterministic release audit are present. It should be sent to Dr. Bolding and coauthors now. It is not labeled SUBMISSION READY because the experimental setup assumptions and biological framing require coauthor confirmation, and the strongest remaining uncertainties require measurements rather than additional nominal simulation.

## Go/no-go answers

1. **Is the transport model computationally validated? — Yes.** Geant4 11.3.2 transport uses the validated non-neural physical architecture, recorded source/environment configurations and seeds, active 0.5 µm charged step limiting, exact step/event energy conservation, and explicit containment filtering. Nonfatal boundary-warning frequencies are quantified.

2. **Is neural absorbed dose defensible? — Yes, with an explicit analysis-only ROI definition.** Energy is summed inside the exact set union of 276 verified closed nervous source objects and divided by the body-clipped 0.25 µm union mass at a stated proxy density. It is a mean ROI dose, not cell-, neurite-, membrane-, or histological dose.

3. **Is neural-dose statistical precision adequate? — Yes.** Direct 100M runs give focused `0.9316±0.0339` and diffuse `0.8730±0.0616` neural/whole ratios (Monte Carlo SE), corresponding to 3.6% and 7.1% relative error. There are 1,264/318 raw and 753/200 energy-effective contributors. Event bootstraps and independent 10M replicates corroborate the estimators.

4. **Is reconstruction sufficiently converged for mean-dose claims? — Yes, with assumptions.** Volume changes 3.94% over 0.25–2 µm pitch. Voxel dose ratios remain whole-worm order. Rare terminal/process outliers change the net numerator by no more than 1.51% at 0.25 µm. Fine-structure dosimetry is not supported.

5. **Is muscle comparison defensible? — Yes.** Physical muscle mass/deposition, event-level dose statistics, surface-distance shells, local spectra, and dedicated chemistry are all scored on parallel terms. Muscle/whole ratios are `1.0600±0.0093` focused and `1.0834±0.0185` diffuse.

6. **Is perineural deposited-energy scoring defensible? — Yes.** Exact distances to the original full-resolution nervous surface define mass-free energy shells. Approximately 14.23% focused and 14.39% diffuse whole-worm energy lies within 5 µm. Muscle-surface fractions are nearly identical. The 99-control matched-atlas test does not support a strong neural-enrichment claim.

7. **Is chemistry based on actual deposited energy? — Yes.** Six seeded 10k Geant4-DNA cases use local edep-weighted electron spectra and actual all-particle local deposited energy for absolute normalization. Birth-energy bookkeeping is not primary.

8. **Is the LITE-1 bridge evidence-grounded? — Yes at Level 1 only.** Critical Trp, Cys/PRDX/redox biology, H2O2 inhibition/reset, and free-solute OH kinetics are documented from primary literature. Effective target/scavenging assumptions are swept. No unsupported H/eaq target rate or receptor transfer function is inserted.

9. **Highest scientifically justified mechanistic claim.** Cannon/Bolding-like X-rays generate whole-worm-order energy deposition in neural and muscle tissue and prompt homogeneous-water radiolysis capable of providing Trp-like and thiol/redox chemical interaction opportunities. The physical/radiochemical stimulus is broadly available; LITE-1 expression can plausibly supply tissue specificity. The computation does not establish that radiolysis activates or gates LITE-1.

10. **Ready to send to Dr. Bolding? — Yes.** The results, negative controls, assumptions, literature boundary, and discriminating experiments are explicit.

11. **Ready for coauthor review? — Yes.** The manuscript and figures are complete enough for scientific editing and authorship decisions.

12. **Ready for journal submission? — Not yet.** Coauthors should verify experimental source/sample details, decide the target journal, approve biological wording, and decide whether to submit the bounded computation alone or pair it with a new experiment. These are not missing computational tasks.

13. **Limitations solvable only experimentally.** Measure specimen-plane spectra and dose in exact NGM/M9 geometries; image animal posture and neural registration; obtain population anatomy; measure oxygen/scavenging and LITE-1/PRDX-2 target abundance; record LITE-1-dependent current/calcium/redox during X-ray exposure; test hydroxyl scavengers, catalase, PRDX-2, C44, and critical-Trp perturbations.

## Final claim grades

| Claim | Grade |
|---|---|
| Stable transport and actual-edep scoring | Strongly supported |
| Analysis-only neural mean dose is whole-worm order | Supported with assumptions |
| Neural-dose precision meets the prespecified target | Strongly supported |
| Neural and muscle dose are comparable | Strongly supported |
| Nervous-surface deposited-energy shells are reproducible | Strongly supported |
| Nervous anatomy is preferentially irradiated | Unsupported |
| Prompt homogeneous-water radiolysis follows local edep | Strongly supported for the stated model |
| Trp/thiol/PRDX interaction opportunity exists | Exploratory, literature-grounded |
| Radiolysis gates LITE-1 or predicts behavior | Unsupported |

## Stop decision

No remaining obvious computational fix would materially strengthen the bounded conclusion. More nominal histories would yield diminishing returns; more molecular complexity would be unconstrained. The next information gain must come from experiment and coauthor review.
