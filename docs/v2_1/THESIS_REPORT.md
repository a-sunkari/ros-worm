# Actual neural energy deposition and LITE-1-relevant radiochemistry in ROS-Worm v2.1

## Abstract

ROS-Worm v2.1 asks whether Cannon/Bolding X-ray exposures create a rapid
physical and radiochemical input in and around *C. elegans* anatomy that could
precede LITE-1-dependent behavior. Stable Geant4 transport was retained, while
actual deposited-energy steps were scored against the original high-resolution
OpenWorm nervous atlas and a separately validated analysis-only neural volume.
The primary exact neural ROI is the set union of 276 individually closed source
objects; 0.25–2 µm voxelizations provide independent resolution tests. Neural
mean dose relative to whole-worm mean dose was 0.778 ± 0.101 for focused 50 kV
and 0.969 ± 0.224 for diffuse 20 kV irradiation (Monte Carlo standard errors).
Body-wall-muscle ratios were 1.067 ± 0.029 and 1.089 ± 0.058. Actual deposition
within 5 µm of the original nervous surface represented 14.32% and 14.73% of
whole-worm deposition, but matched-atlas controls showed no compelling neural
enrichment. Deposited-energy-weighted Geant4-DNA water chemistry changed 1 µs
OH and H2O2 yields by only several percent relative to the previous birth
spectrum approximation. Literature-rate competition calculations demonstrate
radiogenic Trp-like and thiol-like interaction opportunities across plausible
target/scavenger brackets. No calibrated mapping to LITE-1 gating exists, so
the mechanistic conclusion stops at chemical availability. The results support
rapid, broadly available radiolytic chemistry as a physically plausible input,
not neural-selective transport or molecular causation.

## Introduction and hypothesis

Cannon et al. reported LITE-1-dependent behavioral responses to focused and
diffuse X-rays. Prior ROS-Worm work reconstructed the source/environment,
validated stable non-neural transport anatomy, and quantified secondary-electron
births near a high-resolution nervous surface. Birth proximity is not absorbed
dose. V2.1 tests the narrower hypothesis that realistic exposures deposit
measurable energy in neural and muscle ROIs and generate water-radiolysis
products capable of interacting with LITE-1-relevant redox motifs on relevant
physical timescales. It does not test whether any individual chemical event
opens LITE-1 or causes behavior.

## Methods

### Transport and spatial deposition

The validated v2 focused tungsten 50 kV/NGM and diffuse silver 20 kV/M9 cases
were rerun only because the existing 10M ROOT files had spatial-step saving
disabled. A code audit found that `G4UserLimits` had been configured without
registering `G4StepLimiterPhysics`; this made the nominal step limit inert. The
physics constructor was added and both production cases were regenerated with
a verified 0.5 µm charged-particle maximum step. Deposited energy is assigned to
the midpoint of charged steps or the post-step interaction point of neutral
steps. Event-level and step-level energy sums are an exact invariant.

### Neural and muscle ROIs

The baked high-resolution nervous surface remains the distance atlas. It is
open/non-manifold and is never treated as physical Geant4 matter. Its source
manifest contains 276 closed, winding-consistent member meshes. Their exact
set union defines the primary analysis-only neural interior. Body clipping
removes the small portion extending beyond the body; a primary density of
1.04 g/cm³ and a 1.00 g/cm³ sensitivity case convert volume to mass.

Voxel-center unions at 0.25, 0.5, 1, and 2 µm were compared for volume,
connectivity, bounds, surface error, outside-body fraction, and dose. The
physical body-wall-muscle region supplies a same-basis comparator. Event-level
sample variance and first-order covariance propagation provide stochastic
uncertainty for regional/whole-worm dose ratios.

### Perineural shells and falsification controls

Every valid in-body deposition step is assigned exact closest-surface distance
and binned into 0–1, 1–2, 2–5, 5–10, 10–25, 25–50, and ≥50 µm shells. Atlas
translations, position conventions, independent seeds, source spectra,
environment, material, density, voxel pitch, and matched internal-surface
controls test robustness and specificity.

### Deposited-energy-driven chemistry

Six local electron spectra were weighted by actual deposited electron energy:
focused/diffuse × neural/perineural-5-µm/muscle. The preserved Geant4-DNA
chem6-derived water lifecycle generated time series from 1 ps to 1 µs with
10,000 histories per spectrum. Local molecule equivalents equal local deposited
energy times the appropriate homogeneous-water G value. This is a water
radiolysis budget, not a biological ROS concentration.

### LITE-1 evidence gate

Primary literature supports direct UV absorption involving LITE-1 tryptophans,
LITE-1-dependent peroxide sensing, oxidative inhibition/reset, cysteine/redox
regulation, and a proposed photon/H2O2 coincidence mechanism. It does not
provide a calibrated radical-hit-to-channel-gating function for X-rays. V2.1
therefore uses literature rate constants in a pseudo-first-order competition
model across target concentration and background-scavenging brackets. Outputs
are Level-1 Trp-like, thiol-like, and PRDX/H2O2 chemical opportunities only.

Full implementation details and citations are in `METHODS.md`,
`LITE1_MECHANISTIC_EVIDENCE.md`, and `LITE1_TARGET_CHEMISTRY.md`.

## Validation

The focused and diffuse runs contain 1,947,267 and 510,833 positive deposition
steps. Both conserve energy exactly between event and step trees and contain no
nonfinite or out-of-body deposition coordinates. Charged depositing steps obey
the 0.5 µm limit. Residual nonfatal navigation warnings occurred at rates of
2.02×10⁻⁵ and 4.7×10⁻⁶ per history, predominantly body/digestive boundaries.

Neural voxel volumes span 8,536–8,872 µm³ (3.9% range). At 0.25 µm, symmetric
surface errors are p50 0.119 µm, p95 0.246 µm, and p99 0.522 µm. Sparse source
objects produce resolution-dependent component counts; topology is therefore
not claimed to converge. Scientific dose outputs, not watertightness alone,
determine acceptance.

## Results

### Actual perineural deposition

Focused whole-worm deposition was 367,301 keV and diffuse deposition was
95,306 keV. The 0–5 µm shells contained 52,606 keV (14.32%) and 14,040 keV
(14.73%), respectively. Hybrid position assignment differed by no more than
6.9% across pre/mid/post conventions.

Matched-atlas null tests gave real/null 0–5 µm deposition ratios of 1.022
(empirical p=0.308) focused and 1.039 (p=0.231) diffuse. Consequently, the
perineural fraction is a valid anatomy-referenced exposure measure but is not
evidence of preferential nervous-system targeting.

### Neural, muscle, and whole-worm dose

The exact-union neural dose ratios were 0.778 ± 0.101 focused and
0.969 ± 0.224 diffuse. Across 0.25–2 µm voxel definitions, ratios ranged
0.819–0.912 and 0.913–1.127. The neural estimate is therefore scientifically
usable as an analysis-ROI mean dose, with large event-statistical and atlas
registration uncertainty; it is not cell-resolved dose.

Muscle ratios were 1.067 ± 0.029 and 1.089 ± 0.058. Comparable order-unity dose
in neural and muscle tissues argues against tissue-specific X-ray absorption as
the source of biological specificity. It is consistent with, but does not
prove, LITE-1 expression supplying that specificity.

Mapping these ratios to reported Cannon exposures gives, for example, focused
neural doses of 1.56 Gy at 0.2 Gy/s for 10 s and 11.67 Gy at 1 Gy/s for 15 s;
the corresponding muscle doses are 2.13 and 16.00 Gy. At diffuse 0.19–0.74 Gy/s
for 20 s, neural estimates span 3.68–14.35 Gy and muscle estimates 4.14–16.12 Gy.
These inherit the reported approximate factor-of-two experimental dosimetry
uncertainty in addition to model uncertainty.

### Water radiolysis and LITE-1-relevant chemistry

At 1 µs, deposited-energy-weighted spectra reduce OH G values by approximately
5.6–7.2% and increase H2O2 by approximately 1.6–3.4% relative to the prior
birth-spectrum approximation. For focused 0.2 Gy/s × 10 s, the homogeneous-water
equivalents are approximately 1.21 million OH and 0.80 million H2O2 molecules
in the neural ROI; muscle values are larger because its mass and deposited
energy are larger. These are scale estimates, not intracellular counts.

Published OH rate constants for Trp-like and cysteine-like sinks permit
transparent opportunity estimates, but unknown effective target concentration,
background scavenging, oxygenation, access, repair, and protein abundance span
orders of magnitude. The output therefore remains a conditional chemical
opportunity index. No activation or open probability is reported.

## Sensitivity and uncertainty

Source hardness changed the 0–5 µm deposition fraction by roughly −6.3% to
+2.1%; material substitution changed focused results by +3.0%. Removing the
medium changed focused results by +3.3% but diffuse results by −11.9%, showing
that the diffuse M9 environment is not negligible. Independent-seed effects
were +3.8% and −3.6%. Full-production ±2 µm atlas shifts bracket neural dose
ratios by 1.00–1.28 focused and 0.70–1.42 diffuse relative to baseline. The
dominant uncertainty is experimental dosimetry, followed by registration and
limited neural-hit statistics. Many 1M sensitivity cases contain too few neural
events for precise source-specific neural dose comparisons; they are retained
as a documented power limit rather than overinterpreted.

## Discussion

The v2.1 upgrade changes the central result from particle-birth bookkeeping to
actual spatial energy deposition. Neural and muscle mean doses are of the same
order as the whole-worm mean, while near-surface deposition is not enriched
over matched internal surfaces. Thus transport does not identify a neural
hotspot. Instead, it predicts a rapid radiolytic field available in both tissues
where LITE-1 expression can determine biological sensitivity. This is aligned
with the ectopic-muscle experiment at the level of physical plausibility only.

The explicit neural ROI makes an absorbed-dose calculation possible without
reintroducing unstable nervous daughters into Geant4. Its mass is an anatomical
model, not a measured individual-worm neural mass. Resolution stability is good
for volume and dose, while registration and topology remain important caveats.

## Limitations

- Cannon dosimetry carries an approximate factor-of-two uncertainty.
- Source spectra and environmental dimensions remain bounded reconstructions,
  not measurements of the exact apparatus used for each animal.
- Condensed-history transport plus separate homogeneous-water chemistry does
  not preserve nanometre local track structure or intracellular composition.
- Neural dose is an ROI mean and has relatively few contributing events.
- The neural source-member union represents OpenWorm geometry, not subject-
  specific anatomy, neurite radii, organelles, or membranes.
- LITE-1 abundance, accessibility, competing scavengers, oxygen, PRDX state,
  and a radical-to-gating transfer function are not known quantitatively.
- Behavioral causality, channel gating, and intracellular ROS concentration are
  outside the demonstrated scope.

## Experimental predictions and tests

The model predicts approximately linear scaling of deposited-energy-driven
chemistry with dose when dose rate does not alter biology, comparable physical
dose availability in neural and muscle tissues, and sensitivity of diffuse
irradiation to surrounding aqueous medium. Highest-value tests are calibrated
in-worm dosimetry; time-resolved LITE-1-dependent redox/calcium measurements;
radical-scavenger perturbations that preserve dose; oxygen dependence;
tryptophan/cysteine/PRDX mutants; and matched neural versus muscle expression.
Detailed discriminating experiments are prioritized in the repository-level
limitations and experiments document.

## Conclusion

Using stable Geant4 transport and a separately validated high-resolution neural
scoring model, ROS-Worm v2.1 calculates actual energy deposition in and around
*C. elegans* nervous anatomy under Cannon/Bolding-like X-ray conditions. Neural
mean dose is approximately 0.78–0.97 times whole-worm mean dose in the nominal
focused/diffuse cases, while muscle receives approximately 1.07–1.09 times the
whole-worm mean. Deposited energy supports prompt water-radiolysis and
literature-rate Trp/redox interaction opportunities in both tissues. The model
therefore supports radiolytic chemistry as a physically available intermediate,
but finds no neural-selective transport and does not establish LITE-1 gating,
intracellular ROS concentration, or behavioral causation.
