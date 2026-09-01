# Skeptical paper-readiness review

## Overall judgment

This is ready to send to Dr. Bolding as a thesis-grade computational study and
methodological audit. It is ready to begin manuscript drafting if framed as a
physical-plausibility and uncertainty paper. It is not ready for a manuscript
claiming that radiolysis activates LITE-1 or that neural tissue receives a
preferential X-ray dose.

## 1. Is neural absorbed dose now defensible?

**Supported with assumptions.** The numerator is actual Geant4 deposition
classified inside the exact union of 276 content-verified closed nervous
source objects. The denominator is an explicit body-clipped 0.25 micrometre
volume at 1.04 g/cm3, with a 1.00 g/cm3 sensitivity. Transport is unchanged by
the analysis ROI. This is a valid analysis-only mean absorbed dose.

The limitations are material: the source object interiors may not represent
true histological tissue thickness, the atlas is one morphology, density is a
proxy, overlaps are counted once, registration affects the result, and the
diffuse numerator has only 30 contributing events. The phrase "neural absorbed
dose" must always be accompanied by the ROI definition.

## 2. Is the neural ROI resolution-converged?

**Supported with assumptions.** Volume changes by only 3.9% from 0.25 to 2
micrometres. Voxel dose ranges are 0.819–0.912 focused and 0.913–1.127 diffuse,
with spread no larger than the event-level uncertainty. At 0.25 micrometres,
p95 surface error is 0.246 micrometres. This is enough to support the
same-order regional-dose conclusion.

It is not uniformly converged for all thin processes: connectivity fragments,
p95 error worsens sharply on coarse grids, and sampled maximum error stays
near 31 micrometres. Named-neurite or individual-neuron dosimetry is not
supported.

## 3. Are uncertainty bars meaningful?

**Supported with assumptions.** Event-level standard errors and covariance-
propagated ratios are mathematically appropriate and independently seeded
variants are retained. Reconstruction, density, registration, step position,
source/environment, and experimental dosimetry are not collapsed into a false
single Gaussian error bar. This separation is scientifically preferable.

The 1M neural-ROI sensitivity variants are underpowered, sometimes with only
2–21 contributing events. They cannot establish source-specific neural-dose
effects. The perineural and muscle variants are better powered. Registration
and factor-of-two dosimetry are assumption intervals rather than calibrated
probability distributions. A full probabilistic uncertainty distribution is
therefore not available.

## 4. Is local radiolysis based on deposited energy?

**Strongly supported for the stated water model.** Absolute molecule-equivalent
budgets use actual regional deposited energy, not summed electron-birth kinetic
energy. Six 10k Geant4-DNA cases use local electron-edep-weighted spectra and
retain input hashes/seeds. Birth-spectrum G values remain only a sensitivity.

The chemistry is still homogeneous liquid water. The condensed-history
transport cannot be continued as nanometre-resolved track chemistry without
inventing ionization structure. Oxygen, biomolecular scavenging, clearance,
and intracellular compartmentation are absent.

## 5. Does the LITE-1 bridge use real kinetics?

**Supported with assumptions.** OH + free Trp and OH + free cysteine rates are
from primary pulse-radiolysis studies; the H2O2/PRDX bracket is sourced to
measured peroxiredoxin family kinetics. Exact values and DOIs are in the
configuration.

Free amino-acid rates need not equal rates for protein-bound residues. The
PRDX rate is not a measured *C. elegans* PRDX-2/LITE-1 complex rate. Effective
target concentrations and background scavenging are swept because they are
unknown. The metric is chemical opportunity only.

## 6. Are any receptor metrics calibrated?

**Unsupported—and appropriately omitted.** No LITE-1 activation probability,
open probability, calcium response, or behavioral transfer function is
reported. The literature supports direct UV absorption, critical Trp residues,
Cys/PRDX-linked redox effects, ROS-dependent behavior, and H2O2-mediated
inhibition/deactivation. It does not supply an X-ray-radiochemistry-to-gating
calibration.

## 7. What would Reviewer 2 attack?

1. The 276-object interior may be a modeling construct rather than histological
   neural tissue thickness.
2. Diffuse neural dose has only 30 contributing events and broad registration
   sensitivity.
3. Exact at-sample spectra, polycapillary transmission, liquid depth, and
   per-worm dose are not measured.
4. The 14–15% perineural fraction fails the matched-surface enrichment test.
5. Homogeneous-water G values are far from intracellular chemistry.
6. Target-interaction ranges depend overwhelmingly on unknown concentration and
   scavenging; the upper range may be an unrealistic bound.
7. Remaining `GeomNav1002` incidents are nonzero.
8. Fluence-linear dose scaling cannot reproduce a biological threshold or
   dose-rate dependence beyond total dose.
9. One atlas and one worm morphology do not represent animal-to-animal anatomy.
10. The mechanistic narrative could still overread genetic dependence as
    chemical causality unless every claim follows the evidence labels.

The current repository addresses these attacks by quantifying or admitting
them; it does not make them disappear.

## 8. Which limitations require experiments rather than more simulation?

- Measure the focused and diffuse spectra at the specimen plane, including
  filtration and polycapillary transmission.
- Place microdosimeters/film under the exact NGM/M9 geometries to reduce the
  factor-of-two dose interval.
- Image worm posture relative to the beam and register a neural marker to body
  geometry.
- Measure LITE-1-dependent behavior/calcium/current under antioxidant,
  hydroxyl-scavenger, catalase, PRDX-2, and C44/Trp perturbations.
- Measure intracellular H2O2/redox probes at seconds-scale exposures with
  appropriate time resolution and radiation controls.
- Quantify LITE-1/PRDX-2 expression or effective reactive-site abundance in
  neurons and ectopic muscle.

Increasing Monte Carlo histories can narrow diffuse neural statistics but
cannot supply these missing biological parameters.

## 9. Is it ready to send to Dr. Bolding?

**Yes.** The analysis directly addresses the two requested methodological gaps,
contains negative/null results, exposes the step-limiter failure and correction,
and distinguishes transport, water chemistry, and biology. Dr. Bolding should
review the experimental setup assumptions and help prioritize the proposed
discriminating experiments.

## 10. Is it ready for manuscript drafting?

**Yes, with a bounded scope.** A methods/physical-plausibility manuscript can
be drafted now. Before submission, the authors should decide whether to:

- add higher-stat diffuse neural scoring;
- obtain measured at-sample spectrum/dose;
- add animal-specific registration data; and
- pair the simulation with one redox/scavenger perturbation experiment.

Without those additions, the paper must stop at physical availability and
interaction opportunity.

## Claim grades

| Claim | Grade | Reviewer rationale |
|---|---|---|
| Stable non-neural Geant4 transport reproduces v2 architecture | Strongly supported | Existing v2 validation retained; v2.1 changes output only |
| Saved steps reproduce whole-worm energy and valid coordinates | Strongly supported | Exact conservation; zero invalid/out-of-body rows |
| Nervous-surface edep shells are reproducible | Strongly supported | Full atlas, explicit bins, 10M statistics, exact locator |
| 14–15% within 5 µm is neurally enriched | Unsupported | Matched-null p=0.308/0.231 |
| Analysis-only neural mean dose is same-order as whole-worm dose | Supported with assumptions | Exact union, bounded mass, convergence and MC errors |
| Neural transport is preferential to muscle | Unsupported | Muscle/whole ratios are similar or higher |
| Environment matters for diffuse spatial deposition | Supported with assumptions | Worm-only changes 0–5 µm fraction by −11.9% at 1M |
| Local water radiolysis follows actual edep | Strongly supported | Edep normalization and 10k Geant4-DNA runs |
| Radiogenic species can encounter Trp/thiol/PRDX-like targets | Exploratory | Real rates, unknown target abundance/scavenging |
| Radiolysis activates LITE-1 | Unsupported | No calibrated gating or causal experiment |
| Modeled chemistry explains Cannon behavior | Unsupported | Linear compatibility is not causality |

## Final reviewer recommendation

Proceed to scientific review and manuscript planning. Require terminology and
claim checks before any external draft: **analysis-only neural dose**,
**nervous-surface-referenced deposited energy**, **homogeneous-water molecule
equivalent**, and **target-interaction opportunity** are the allowed terms.
