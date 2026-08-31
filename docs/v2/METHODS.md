# Methods: thesis v2 physical-plausibility study

## Question and evidentiary boundary

The simulation asks whether Cannon/Bolding X-ray exposures can create rapid
secondary-electron and water-radiolysis environments close to *C. elegans*
nervous and muscle anatomy. It does not model LITE-1 molecular activation and
cannot prove that radiolysis causes the behavior.

## Anatomy and transport geometry

The model scale is 0.1 mm per source-model unit. The stable v1 physical
manifest is retained: a watertight whole-body residual mother plus priority-
baked reproductive, digestive, and body-wall muscle daughters. The original
high-resolution nervous STL and excretory anatomy are scoring atlases, not
physical daughters. This avoids the resolution-dependent classification and
navigation instability of earlier voxelized nervous solids.

The body center from the authoritative transport manifest defines the atlas
translation. All STL vertices are translated by that center and multiplied by
0.1 mm/unit. Model Y is longitudinal; X and Z span the cross-section. The v2
experimental beam propagates predominantly along world −Z from above the
specimen. This corrects the v1 runner's generic +Y source orientation.

## Photon sources

The focused source models the reported tungsten iMOXS-MFR at 50 kV with a
0.85 mm Gaussian FWHM footprint and a nominal 50 mm capillary-to-agar distance.
The diffuse source models the silver Amptek Mini-X at 20 kV with nozzle and
filters removed. Diffuse histories are launched from 10 mm above and
conditioned on crossing a 1.2 × 1.2 mm target plane around the worm. That is an
importance-sampling device; absolute fluence is obtained only from dose
normalization.

Exact instrument spectra at the sample were not recovered. The study therefore
uses explicit soft/nominal/hard ensembles. Each begins with a Kramers
photon-number continuum, adds target-characteristic lines, and applies NIST
XCOM Be/Al attenuation. The assumed line fractions and additional filtration
are in `config/v2/source_models.yaml`. Resulting mean energies are 10.47,
12.83, and 14.58 keV for focused; 5.53, 6.09, and 7.57 keV for diffuse. These
are physics brackets, not instrument measurements.

Primary setup sources are Cannon et al. (2023), the IFG iMOXS manual, and the
Amptek Mini-X2 manual/product data. The Amptek source has a manufacturer-
specified 125 µm Be window and 120° uncollimated cone. At 20 kV, Ag K lines
cannot be excited; the low-energy Ag L contribution is explicitly bracketed.

## Experimental environments

Three environments are implemented:

- worm-only in air;
- focused worm resting on 3 mm water-equivalent NGM/agar over 1 mm
  polystyrene;
- diffuse worm immersed beneath up to 0.405 mm water-equivalent M9 above its
  top surface, with 0.010 mm below and 1 mm glass substrate.

The 0.5 mm diffuse liquid height is reported by Cannon et al.; its exact depth
over each worm is unknown and is varied. NGM composition is approximated as
water for photon transport. Geometry dimensions labeled as assumptions are not
presented as measurements.

## Physics and regional scoring

Transport uses Geant4 11.3.2 with `G4EmLivermorePhysics`, a 100 nm production
cut, and a 2 µm maximum step in biological volumes. Materials are NIST soft
tissue, brain proxy (unused physically in v2), skeletal muscle, reproductive
proxy, and water-rich soft tissue as documented in
`config/region_materials.csv`. A pure-water material map is a sensitivity case.

Regional energy deposition is scored in physical compartments. Every secondary
record includes PDG code, birth kinetic energy, position, parent step, and an
in-body flag. Neural scoring admits only finite PDG 11 births that are both
recorded and geometrically verified inside the whole-body mesh. This makes
escaped and out-of-body exclusions explicit.

## Neural and muscle endpoints

For each eligible birth, VTK's static triangle locator finds the exact closest
point on the full-resolution nervous surface. Reported shells are 0–1, 1–2,
2–5, 5–10, 10–25, 25–50, and ≥50 µm. Metrics include count, fraction, energy
distribution, per-primary rate, and conditional rate per whole-worm Gy.

Five equal Y-length sectors describe longitudinal position. They are coordinate
sectors, not named neuron classes. Muscle endpoints include births in the
physical body-wall compartment and distance to the body-wall surface.

The neural null uses the identical high-resolution atlas after small rigid
Y-axis rotations and translations. A transform is accepted only when sampled
atlas containment remains within one percentage point of baseline. Thus surface
area and morphology are matched. It tests whether proximity exceeds what a
large, similarly placed internal surface would obtain.

## Normalization and experimental dose series

Whole-worm dose per history is total scored energy divided by the sum of
physical scoring masses and event count. `births_per_whole_worm_Gy_conditional`
divides births per history by this dose. The condition is important: reported
experimental Gy is assumed to correspond to model whole-worm mean dose.

Transport is fluence-linear, so physically identical dose-rate conditions are
not rerun. The same per-Gy driver is scaled to 0.19–0.74 Gy/s for 20 s diffuse,
0.2–1 Gy/s for 10 s focused avoidance, and 1 Gy/s for 15 s focused egg
ejection. No dose-rate chemistry or biological saturation is asserted.

## Radiolysis

Neural- and muscle-proximity electron birth spectra drive the preserved
chem6-derived Geant4-DNA liquid-water chemistry. The IRT time-step model and validated
reaction lifecycle are unchanged. Species are reported at 1 ps, 10 ps, 100 ps,
1 ns, 10 ns, 100 ns, and approximately 1 µs, with 50 additional log bins.
Outputs are G values in molecules/100 eV. They are homogeneous-water
radiolysis predictions, not biological ROS measurements or intracellular
concentrations. Four 10k chemistry cases use the focused/diffuse spectra within
5 µm of the neural and body-wall muscle surfaces, with paired seeds for the
tissue comparison.

For an exposure-level energy-budget comparison, the workflow multiplies each
time-resolved G value by the summed kinetic energy of births within 5 µm,
scaled conditionally per reported whole-worm Gy. This calculation assumes that
the full birth-energy budget thermalizes locally in homogeneous water. The
result is labeled a *conditional homogeneous-water molecule equivalent*; it is
not a spatially resolved yield, a surviving intracellular molecule count, or a
concentration.

## Uncertainty and validation design

The sequence was 100k smoke/falsification, three independent 1M nominal seeds,
paired 1M source/environment/beam/material sensitivities where warranted, then
10M nominal production. Sensitivities include spectrum hardness, experimental
medium, M9 depth, beam position, beam FWHM, material model, neural threshold,
atlas placement, and stochastic seed. Focused absolute dosimetry retains the
paper's approximate factor-of-two uncertainty; it is not collapsed into the
Monte Carlo error bars.

## References

- Cannon KE et al. “LITE-1 mediates behavioral responses to X-rays in
  *Caenorhabditis elegans*.” *Frontiers in Neuroscience* 17, 1210138 (2023).
  https://doi.org/10.3389/fnins.2023.1210138
- Amptek, Mini-X2 User Manual, rev. B2.
  https://www.amptek.com/-/media/ametekamptek/documents/resources/products/user-manuals/mini-x2-user-manual-rev-b2.pdf
- IFG, iMOXS Modular X-ray Source Technical Manual.
  https://manualzz.com/doc/6740452/ifg-imoxs-modular-x-ray-source-technical-manual
- NIST XCOM photon cross sections.
  https://www.nist.gov/pml/x-ray-and-gamma-ray-data
- Geant4 Physics Reference Manual, Livermore electromagnetic models.
  https://geant4.web.cern.ch/documentation/dev/prm_html/PhysicsReferenceManual/electromagnetic/introduction/livermore.html
