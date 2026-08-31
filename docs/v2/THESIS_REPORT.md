# ROS-Worm v2: anatomy-informed X-ray transport and water radiolysis in *C. elegans*

## Abstract

Cannon et al. reported rapid LITE-1-dependent *C. elegans* responses to focused
and diffuse X-rays and showed that ectopic muscle LITE-1 confers X-ray
sensitivity. ROS-Worm v2 tests whether the preceding physical and radiochemical
steps are plausible under those exposure conditions. Geant4 transport was run
through stable OpenWorm-derived physical compartments while the original
high-resolution nervous anatomy was retained as a closest-surface atlas. New
v2 models include physics-bracketed W 50 kV and Ag 20 kV spectra, vertical beam
geometry, NGM/M9 and substrate environments, shell- and longitudinally resolved
neural proximity, muscle comparison, matched-atlas nulls, independent seeds,
sensitivity studies, and time-resolved Geant4-DNA water radiolysis.

In 10M nominal histories, 14.19% of focused and 14.88% of diffuse eligible
in-body electron births lay within 5 µm of the nervous surface, corresponding
conditionally to approximately 1.15–1.17 million births per whole-worm Gy.
However, matched perturbations of the identical atlas yielded nearly the same
fractions; no compelling neural-specific enrichment was found. Neural- and
muscle-surface proximity rates were also similar. Water-radiolysis products
arose by picoseconds; at approximately 1 µs, G(•OH) was 1.46–1.49 and
G(H₂O₂) was 0.885–0.889 molecules/100 eV. The diffuse liquid layer was the
dominant tested environmental uncertainty. These results support radiolytic
chemistry as a physically possible intermediate stimulus present near both
neural and muscle tissues, while neither establishing neural targeting nor
linking any chemical species causally to LITE-1 activation.

## Introduction

The key experiment is Cannon KE et al., *Frontiers in Neuroscience* 17,
1210138 (2023), DOI 10.3389/fnins.2023.1210138. Wild-type animals showed acute
focused-beam avoidance, whereas LITE-1 disruption strongly reduced the
response. Muscle expression of LITE-1 produced X-ray-dependent paralysis and
egg ejection, and diffuse dose-rate experiments showed a monotonic behavioral
trend. These experiments establish genetic dependence and tissue-transferable
sensitivity; they do not measure neuron-level hydroxyl radical, peroxide, or a
specific radiolytic activation pathway.

Ionizing photons necessarily produce secondary electrons and water chemistry.
The mechanistic uncertainty is whether the magnitude, timing, and spatial
distribution under the actual experiment make radiolysis a credible
intermediate. A model that merely demonstrates some ROS in water would be
insufficient. The relevant tests are source realism, sample medium, anatomical
association, null geometry, dose scaling, tissue comparison, and dominant
uncertainties.

## Scientific hypothesis

The tested hypothesis is that Cannon-like X-ray exposures produce a rapid,
dose-scaled secondary-electron and radiochemical input close to tissues capable
of expressing LITE-1. The hypothesis does not require preferential neural
transport. Its physical-plausibility prediction is that neural and muscle
regions both receive such an input; biological response specificity may then
arise from LITE-1 expression and cellular context.

## Methods

Detailed methods are in [METHODS.md](METHODS.md). Briefly, the validated v1
physical geometry was preserved. The non-watertight nervous source STL was not
converted into a physical daughter because prior voxel solids were
resolution-dependent and anatomically altered. Finite in-body PDG-11 births
were scored by exact closest point to the full-resolution surface.

Focused transport used a 50 kV tungsten soft/nominal/hard ensemble, a 0.85 mm
Gaussian footprint, and NGM/agar plus dish. Diffuse transport used a 20 kV
silver ensemble and an M9 layer over glass. Nominal sources propagated from
above along −Z. Macroscopic transport used Geant4 Livermore physics; water
radiolysis used the preserved chem6-derived Geant4-DNA lifecycle.

The primary design included 100k falsification cases, three 1M nominal seeds,
paired 1M sensitivities, and 10M nominal productions. A rigid, containment-
screened perturbation family of the same nervous atlas provided the
surface-area/morphology-matched null. Dose-series outputs were obtained by
fluence-linear scaling, with an explicit conditional whole-worm-Gy
normalization.

## Validation

All critical inputs are hashed in run manifests. Actual macros contain the
recorded `beamOn`, seeds, spectrum file, source coordinates, beam direction,
environment, and material map. The source generator is deterministic. The v1
architecture remains buildable and was not replaced.

Three 1M nominal replicates showed near-neural birth-rate coefficients of
variation of about 2.7% focused and 7.2% diffuse. Ten-million-history runs
contained 65,612 and 16,396 eligible births, respectively. Independent in-body
tests excluded no nonfinite or out-of-body production coordinates. The known
non-neural `GeomNav1002` issue remained low-frequency and nonfatal; destructive
anatomical repair was not performed.

## Results

Full tables are in [RESULTS.md](RESULTS.md) and
`ros_worm_stage1/validation/v2/`. The main production endpoints were:

| Endpoint | Focused | Diffuse |
|---|---:|---:|
| Eligible births | 65,612 | 16,396 |
| Within 5 µm | 14.19% | 14.88% |
| Matched-null mean | 14.12% | 14.52% |
| Real/null ratio | 1.005 | 1.025 |
| Conditional near-neural births/Gy | 1.150×10⁶ | 1.170×10⁶ |
| Conditional near-muscle births/Gy | 1.128×10⁶ | 1.157×10⁶ |

The matched-null result is central. The actual nervous surface is spatially
associated with many births, but not substantially more than small allowed
perturbations of the same anatomy. Near-neural proximity must not be described
as a selective neural dose.

The physical input was also present near and inside body-wall muscle. This
matches the logical structure of the ectopic-expression experiment: X-ray
transport does not need to distinguish muscle from nervous tissue for LITE-1
to confer sensitivity in both.

Physical-compartment deposition was stable across sources: approximately 90%
occurred in the residual body, 2.4–2.5% in body-wall muscle, 4.9–5.1% in the
digestive compartment, and 2.6% in the reproductive compartment. The neural
and excretory atlases correctly carry no physical-volume deposition.

Medium tests showed negligible effect from agar downstream of the focused worm
but a strong effect from M9 upstream of the diffuse worm. Paired source
hardness, focused beam position, and focused FWHM brackets did not remove the
conditional near-neural signal. Diffuse M9 depth dominated the tested geometry
uncertainty.

Water chemistry began promptly. •OH G values were about 5.04 at 1 ps and
1.46–1.49 at 1 µs; H₂O₂ rose from about 0.051 to about 0.887. The chemistry
therefore easily precedes second-scale behavior, but timing compatibility is a
necessary rather than sufficient causal criterion.

Conditional homogeneous-water energy-budget conversions span roughly
0.19–1.42 billion •OH molecule equivalents across the focused conditions and
0.35–1.36 billion across the diffuse series at ~1 µs. They assume full local
thermalization of near-neural birth kinetic energy and must not be interpreted
as intracellular yields or concentrations.

## Sensitivity and uncertainty

Monte Carlo replication, source brackets, environment, beam geometry, material
model, neural shell threshold, and atlas placement were separated where
feasible. The strongest supported sensitivity was the diffuse water layer:
removing it increased near-neural births/Gy by 41%. Focused spectrum hardness
changed that endpoint by +5% to −11%; diffuse hardness by about ±1.5%.
Focused ±0.2 mm offsets and 0.65–1.05 mm FWHM brackets changed the paired 1M
endpoint by less than 5%.

These are model sensitivities, not complete confidence limits. The focused
factor-of-two dosimetry uncertainty and unknown instrument spectra remain
external systematic uncertainties. The null result is robust enough to reject
a strong neural-enrichment narrative, but larger and more diverse null families
would be needed to bound subtle enrichment.

## Discussion

The simulation supports the existence, magnitude scaling, and rapid timing of
a radiolysis-capable physical input under the experimental dose regime. It does
not find a special neural X-ray transport property. That negative result
improves the biological interpretation: the physical field is broadly
available, while LITE-1 expression can determine which cells respond.

The dose-response comparison is deliberately modest. Linear transport must
increase with total dose, so agreement with a monotonic phenotype is a
compatibility check, not a mechanistic fit. A real mechanism would additionally
need radical survival in cellular media, access to the relevant molecular
target, receptor transduction, and circuit-level response.

The nervous surface remains the scientifically preferable endpoint. A
watertight nervous solid would offer an intuitive inside-volume dose but would
be misleading unless it converged geometrically and preserved morphology.
Current evidence does not justify sacrificing anatomy to obtain that label.

## Limitations

The exact spectra, polycapillary transmission, individual worm geometry,
meniscus, medium composition, dissolved oxygen, intracellular scavenging, and
LITE-1 molecular kinetics are not modeled. Conditional per-Gy normalization is
not an independent fluence calibration. The chemistry is homogeneous water,
and residual physical-volume navigation warnings remain. A detailed list and
discriminating experiments are in
[V2_LIMITATIONS_AND_EXPERIMENTAL_TESTS.md](../../V2_LIMITATIONS_AND_EXPERIMENTAL_TESTS.md).

## Experimental predictions

The most discriminating predictions are that liquid depth will change the
diffuse spectrum and birth count per dose; radical-lifetime perturbations may
change behavior at fixed dose if radiolysis is intermediate; and neural versus
muscle phenotype differences should follow expression/cellular context more
than physical exposure. Spatial beam scans should follow modeled deposition,
with sharper phenotype localization indicating circuit biology.

## Conclusions

Under X-ray conditions approximating Cannon et al., anatomy-informed Monte
Carlo transport predicts rapid low-energy secondary-electron production and
homogeneous-water radiolysis in close spatial association with nervous and
muscle tissues. The signal scales across the experimental exposure regime and
survives the tested source and beam uncertainties, while diffuse liquid depth
materially changes it. The analysis supports radiolytic chemistry as a
physically plausible intermediate input but does not establish molecular
causality, intracellular ROS concentration, neuron-selective irradiation, or
LITE-1 activation. The matched-null result specifically shows that near-neural
proximity is primarily an anatomical exposure descriptor rather than evidence
of preferential neural targeting.
