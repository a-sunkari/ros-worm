# Hostile technical review

## Recommendation before author response: major revision

The manuscript is unusually transparent, but a successful pipeline is not itself a biological mechanism. My concerns below deliberately test whether the paper's bounded physical-plausibility claim survives.

## Major criticisms

1. **Neural dose could be an arbitrary mesh construct (B/C).** The 276 interiors are computational source objects, not measured neuronal membrane/cytoplasm. Watertightness and volume convergence do not establish histological thickness. The paper must define the endpoint every time and show that local geometric outliers do not dominate it.

2. **Rare-event statistics may still invalidate diffuse dose (B).** Regional energy is compound and skewed. A normal ± value without event covariance, effective counts, bootstrap, convergence, and independent replicates would be unacceptable.

3. **The ratio shares numerator and denominator (B).** Treating them as independent would misstate uncertainty. Event-level independence and covariance must be explicit.

4. **Atlas-registration bounds are assumed (C).** The ±2/±5 µm and ±3° perturbations are not animal-derived distributions. They cannot be called confidence intervals.

5. **The 31 µm surface mismatch undermines “high resolution” (B).** A maximum of this size is incompatible with uniform submicrometre fidelity. Its location and energy impact need quantification.

6. **The near-neural fraction may be a surface-area artifact (B).** A 14% result is uninterpretable without enough identical-surface nulls for useful empirical resolution. Twelve controls and p≈0.2–0.3 would be weak.

7. **Muscle comparison may be asymmetric (A/B).** Neural distance is scored to a high-resolution atlas whereas muscle is a physical region. Equal rigor requires muscle dose, surface-distance shells, spectra, and chemistry.

8. **Step scoring may misplace energy (B).** A nominal user limit is insufficient unless the step-limiter process is registered and actual charged-step lengths are verified. Photon midpoint assignment would be physically wrong.

9. **Outside-body coordinates contradict perfect-QC claims (B).** Escaped or boundary positions must be excluded explicitly and their energy impact stated.

10. **Navigation warnings may signal biased deposition (B).** Thousands of warnings cannot be dismissed by calling them rare. Boundary pairs, frequency, energy conservation, and the cost of geometric repair must be reported.

11. **Source spectra are insufficiently measured (C).** Target/voltage/line-informed brackets do not replace specimen-plane spectra, filtration, or polycapillary transmission. Absolute claims must inherit this uncertainty.

12. **M9/NGM geometry is underconstrained (B/C).** Medium thickness and sample placement may change scatter. Worm-only sensitivity is needed; exact experimental geometry ultimately requires measurement.

13. **Chemistry could still be birth-energy bookkeeping (B).** Absolute yields must use actual local deposited energy. A birth-count spectrum cannot be the primary normalization.

14. **Condensed-history steps do not supply DNA track structure (B).** Treating micrometre steps as individual nanometre spurs would be invalid. The manuscript must admit that it uses a separate spectrum-conditioned water-chemistry reference.

15. **Homogeneous-water yields are biologically remote (D).** They omit oxygen, scavenging, macromolecules, membranes, diffusion, and clearance. Calling them intracellular ROS would warrant rejection.

16. **Trp/Cys metrics may be numerology (B/D).** Free-solute rate constants may not transfer to protein sites; target concentration and scavenging span orders of magnitude. Results must be opportunity ranges, not predicted modifications.

17. **H2O2 has contradictory LITE-1 biology (B).** Literature includes inhibition/deactivation as well as redox/coincidence effects. A monotone H2O2 activation narrative is untenable.

18. **No gating or behavioral calibration exists (C).** Linear physical scaling cannot explain a biological threshold or dose-rate response. A response probability must not be reported.

19. **One anatomy cannot represent animals (C).** Posture, dimensions, neural registration, and expression vary. These are not removable with more histories.

20. **Experimental dosimetry dominates absolute values (B/C).** Cannon's approximate factor-of-two uncertainty must not be hidden inside a small Monte Carlo error bar.

## Category-A items requiring correction before release

Only item 7 was identified as a computational asymmetry during this final review; it requires matched muscle surface scoring and local chemistry in addition to the existing muscle dose. All other computationally addressable concerns are classified B because the final package already contains quantitative evidence, but they must remain visible in the manuscript. Categories C require new experimental information. Category D is an explicit scope boundary.

## Claim grades before response

| Claim | Grade |
|---|---|
| Exact saved-step energy and active spatial localization | Strongly supported |
| Analysis-only mean neural dose | Supported with assumptions |
| Preferential neural transport | Unsupported |
| Comparable neural and muscle dose | Strongly supported |
| Perineural energy is enriched | Exploratory/unsupported pending null |
| Prompt homogeneous-water radiolysis | Strongly supported for the water model |
| Protein target interaction | Exploratory |
| LITE-1 activation or behavior prediction | Unsupported |

The paper should be considered only if the response demonstrates that the high-statistics, null-control, muscle, chemistry, and release-audit evidence is regenerated from authoritative tracked outputs.
