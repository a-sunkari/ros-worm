# ROS-Worm v2.1 results

## Release-level finding

Actual deposited-energy scoring changes the interpretation but not the broad
physical-plausibility conclusion. Mean absorbed dose in the analysis-only
neural ROI is of the same order as whole-worm mean dose and body-wall-muscle
dose. About 14–15% of whole-worm deposited energy occurs within 5 micrometres
of the original nervous surface, but matched-atlas nulls show no significant
neural-specific enrichment. Homogeneous-water radiolysis occurs promptly and
scales linearly with local deposited energy. Literature kinetics permit only a
wide chemical-opportunity bracket for Trp/thiol/PRDX-like targets; receptor
activation remains unmodeled.

## Corrected 10M transport

| Quantity | Focused nominal + NGM | Diffuse nominal + M9 |
|---|---:|---:|
| Histories | 10,000,000 | 10,000,000 |
| Positive deposition steps | 1,947,267 | 510,833 |
| Whole-worm deposited energy | 367,301.33 keV | 95,305.53 keV |
| Step minus event energy | 0 keV | 0 keV |
| Invalid scoring positions | 0 | 0 |
| Out-of-body scoring positions | 0 | 0 |
| `GeomNav1002` incidents | 202 | 47 |

The active 0.5 micrometre charged-step limit is printed in both logs. Electron
deposition steps respect it; neutral photon flights can be longer, but their
discrete deposition is assigned to the post-step interaction point. For the
0.25 micrometre neural ROI, using pre-step coordinates instead of the hybrid
definition increases focused deposition by 6.9%; midpoint-only and post-only
assignments increase it by 3.1% and 1.3%. Diffuse position definitions range
from −2.9% to +4.0% around the hybrid result.

The navigation warnings remain nonfatal boundary push incidents. Focused
counts are 133 body/digestive, 51 body/muscle, and 18 body/reproductive;
diffuse counts are 32, 10, and 5. Their frequencies are `2.02×10^-5` and
`4.7×10^-6` per history. Because energy conservation, coordinates, and all
scorers pass, further destructive anatomy changes were not justified.

## Neural ROI geometry

| Pitch | Volume (µm³) | p50 error (µm) | p95 error (µm) | p99 error (µm) |
|---:|---:|---:|---:|---:|
| 0.25 µm | 8,663.0 | 0.119 | 0.246 | 0.522 |
| 0.5 µm | 8,579.1 | 0.236 | 1.260 | 5.098 |
| 1 µm | 8,872.0 | 0.732 | 8.107 | 13.415 |
| 2 µm | 8,536.0 | 2.593 | 17.612 | 25.219 |

Volume varies by 3.9% across a factor-of-eight pitch range. Pre-clipping
outside-body fractions are only 0.21–0.65%. The 0.25 micrometre ROI mass is
`9.00952×10^-12 kg` at 1.04 g/cm3. Thin process connectivity fragments at all
voxel pitches; the exact member-union classifier, not voxel connectivity, is
therefore the authoritative interior numerator. The sampled maximum surface
error remains about 31 micrometres even at 0.25 micrometres, so no claim of
uniform submicrometre fidelity is made.

## Nervous-surface-referenced deposited energy

| Shell | Focused whole-worm edep | Diffuse whole-worm edep |
|---|---:|---:|
| 0–1 µm | 1.271% | 1.470% |
| 1–2 µm | 2.405% | 2.473% |
| 2–5 µm | 10.646% | 10.790% |
| 5–10 µm | 17.168% | 16.253% |
| 10–25 µm | 28.055% | 28.377% |
| 25–50 µm | 23.900% | 23.639% |
| at least 50 µm | 16.555% | 17.000% |

Within 5 micrometres, the focused run deposits 52,605.93 keV, or 14.322% of
whole-worm energy; the diffuse run deposits 14,040.36 keV, or 14.732%. These
correspond to `6.483×10^6` and `6.669×10^6 keV` per modeled whole-worm Gy.
This co-primary endpoint requires no neural volume or density assumption.

## Neural and muscle dose

| Irradiation | Exact-union neural/whole dose | Neural MC SE | Neural events | Muscle/whole dose | Muscle MC SE | Muscle events |
|---|---:|---:|---:|---:|---:|---:|
| Focused | 0.778 | 0.101 | 101 | 1.067 | 0.029 | 1,611 |
| Diffuse | 0.969 | 0.224 | 30 | 1.089 | 0.058 | 413 |

Voxel-specific focused dose ratios are 0.819, 0.886, 0.829, and 0.912 from
0.25 to 2 micrometres; diffuse ratios are 0.913, 1.010, 1.127, and 1.101. The
resolution spread is not monotonic, but it is smaller than or comparable to
the event-level uncertainty. Reducing assumed density from 1.04 to 1.00 g/cm3
increases exact-union ratios to 0.809 focused and 1.008 diffuse.

Under the stated registration bracket, full-production focused neural
deposition ranges from 1.00 to 1.28 times baseline. Diffuse ranges from 0.70 to
1.42. The larger diffuse interval reflects both broad illumination and only 30
contributing neural events. Registration is a major anatomical uncertainty.

The neural and muscle ratios do not support neural-selective X-ray absorption.
That is biologically useful: Cannon's ectopic muscle experiment can be
interpreted without assigning muscle or nervous tissue a special transport
property. Both receive an ordinary aqueous/tissue X-ray energy field; LITE-1
expression provides the demonstrated genetic specificity.

## Matched-atlas null

On deterministic 1M prefixes, the real 0–5 micrometre edep fractions were
14.818% focused and 15.241% diffuse. Real/null-mean ratios were 1.022 and
1.039; empirical upper-tail p values were 0.308 and 0.231 (12 nulls each).
Thus the observed 14–15% perineural energy fraction is not enriched over the
tested same-surface-area, anatomy-contained nulls. It is a spatial descriptor,
not evidence of targeted neural deposition.

This falsifies the strongest version of the preferred interpretation: the
real nervous surface does not collect substantially more deposited energy than
a nearby matched internal atlas. The volumetric dose remains meaningful because
it asks a different question—mean energy per defined neural mass.

## Source, environment, material, and seed sensitivity

Corrected 1M variants are sufficiently powered for the perineural and muscle
endpoints, but not for fine neural-volume dose. Several neural variants contain
only 2–21 contributing events, and their large standard errors are reported
rather than converted into precise source effects.

Relative to nominal 10M 0–5 micrometre edep fractions:

- focused soft/hard spectra change the endpoint by −6.3%/−2.4%; only the soft
  comparison approaches two combined standard errors;
- diffuse soft/hard spectra change it by −2.8%/+2.1%, within Monte Carlo noise;
- focused worm-only changes it by +3.3%; focused water material by +3.0%;
- diffuse worm-only changes it by −11.9% (`−4.0` combined standard errors),
  confirming that the M9/glass environment is material to spatial deposition;
- independent seeds change it by +3.8% focused and −3.6% diffuse.

The central conclusion—regional doses of the same order as whole-worm dose and
substantial but non-enriched perineural deposition—survives the tested source
brackets. Exact at-sample spectrum and diffuse liquid geometry remain valuable
experimental measurements.

## Deposited-energy-weighted water radiolysis

At 1 ps, edep-weighted focused-neural `G(OH)=5.032 molecules/100 eV`. At
approximately 1 microsecond, focused neural/muscle `G(OH)` values are
1.379/1.386 and `G(H2O2)` values are 0.918/0.902. Diffuse neural/muscle values
are 1.378/1.380 and 0.915/0.903.

Relative to v2 birth-count spectra at 1 microsecond, the edep-weighted spectra
change `G(OH)` by −5.6% to −7.2% and `G(H2O2)` by +1.6% to +3.4%. These are
meaningful but modest. Replacing the exposure-level birth kinetic-energy sum
with actual local deposited energy is the more consequential methodological
change.

### Cannon-condition local budgets

The following values conditionally treat reported experimental Gy as
whole-worm mean dose and exclude the separate 0.5×–2× dosimetry interval.

| Condition | Region | Local dose | OH equivalent at 1 µs | H2O2 equivalent at 1 µs |
|---|---|---:|---:|---:|
| Focused 0.2 Gy/s × 10 s | neural | 1.56 Gy | 1.21×10^6 | 0.803×10^6 |
|  | muscle | 2.13 Gy | 3.09×10^7 | 2.01×10^7 |
| Focused 1 Gy/s × 10 s | neural | 7.78 Gy | 6.03×10^6 | 4.02×10^6 |
|  | muscle | 10.67 Gy | 1.55×10^8 | 1.01×10^8 |
| Focused 1 Gy/s × 15 s | neural | 11.67 Gy | 9.05×10^6 | 6.02×10^6 |
|  | muscle | 16.00 Gy | 2.32×10^8 | 1.51×10^8 |
| Diffuse 0.19 Gy/s × 20 s | neural | 3.68 Gy | 2.86×10^6 | 1.90×10^6 |
|  | muscle | 4.14 Gy | 5.97×10^7 | 3.91×10^7 |
| Diffuse 0.74 Gy/s × 20 s | neural | 14.35 Gy | 1.11×10^7 | 7.38×10^6 |
|  | muscle | 16.11 Gy | 2.33×10^8 | 1.52×10^8 |

Muscle molecule totals are larger mainly because the physical muscle ROI mass
is about 18.6 times the neural proxy mass. Dose, not total molecules, is the
appropriate same-mass comparison. These totals are homogeneous-water molecule
equivalents and do not include cellular scavenging or clearance.

## LITE-1-relevant interaction opportunities

The Level-1 competition sweep spans 1 micromolar–1 millimolar effective target
and `10^8–10^10 s^-1` background scavenging. Accordingly, ranges are wide. At
the 2 Gy focused avoidance condition, neural Trp-like OH interaction
opportunities span about 5.5 to `4.89×10^5`; thiol-like opportunities span 2.4
to `2.24×10^5`. At 10 Gy they scale to 27.5–`2.45×10^6` and 11.8–`1.12×10^6`.

These ranges demonstrate two things, not one. First, radiogenic reactive
species are physically available to interact with motifs implicated in LITE-1
biology. Second, unknown target abundance and cellular scavenging dominate by
orders of magnitude, so an activation probability would be indefensible.

The PRDX-like H2O2 metric is likewise an encounter capacity over the 1 ps–1
microsecond spur interval. It is not a direct LITE-1 reaction and does not
resolve the experimentally observed dual roles of H2O2 in coincidence/redox
signaling versus photosensory inhibition/reset.

## Supported conclusion

Under the modeled Cannon/Bolding conditions, an analysis-only neural ROI
receives a mean absorbed dose of the same order as whole-worm and body-wall-
muscle dose, with focused nominal `D_neural/D_whole=0.778±0.101` and diffuse
`0.969±0.224` before reconstruction, registration, source, and experimental
dosimetry intervals. Actual local deposited energy supports prompt
homogeneous-water radiolysis and a wide, literature-rate bracket of possible
Trp/thiol/PRDX-like interactions. The simulation supports radiolytic chemistry
as physically available under the exposure conditions. It does not establish
neural-selective transport, intracellular chemistry, LITE-1 gating, or causal
mediation of behavior.
