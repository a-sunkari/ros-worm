# ROS-Worm v2.1 methods

## Study question and evidentiary boundary

ROS-Worm v2.1 asks how much energy is deposited in and around *C. elegans*
nervous anatomy under the Cannon/Bolding X-ray conditions and what
homogeneous-water radiochemistry that energy can support. It then estimates
chemical opportunities for interaction with Trp-, thiol-, and PRDX-like target
classes. It does not model LITE-1 open probability, intracellular ROS
concentration, or behavior.

The validated v2 source spectra, external media, physical worm compartments,
and chem6-derived Geant4-DNA lifecycle are preserved. The nervous system and
excretory system remain post-processing atlases rather than Geant4 daughter
volumes. v2 electron-birth proximity results remain historical comparisons;
the v2.1 primary endpoints are actual deposited energy and analysis-only dose.

## Software and provenance

Transport and chemistry use Geant4 11.3.2. Analysis uses the project `ros`
Conda environment with ROOT, VTK, NumPy, pandas, SciPy, and Matplotlib. Every
transport run records the expanded macro, event count, two random seeds,
source/environment choices, input hashes, Geant4 version, and git commit.
Critical compact outputs and their manifests are tracked under
`ros_worm_stage1/validation/v2_1/`; multi-gigabyte ROOT files remain ignored.

The branch is `ai/neural-dose-lite1-v2.1`, based on
`ai/thesis-grade-v2`. Original STL files and v2 outputs are unmodified.

## Physical transport

The stable physical geometry comprises a body-envelope residual plus mutually
exclusive reproductive, digestive, and body-wall-muscle daughters. Transport
uses `G4EmLivermorePhysics`, a 100 nm production cut, tissue-proxy materials,
and v2 focused/diffuse source and environmental definitions. Focused nominal
transport represents the bracketed W/50 kV source, 0.85 mm Gaussian FWHM spot,
NGM/agar, polystyrene dish, and air. Diffuse nominal transport represents the
bracketed Ag/20 kV source, broad illumination conditioned on the worm target
plane, M9 drop, glass, and air. Source spectra remain soft/nominal/hard
uncertainty models, not measured at-sample spectra.

The authoritative v2 10M files had a `steps` tree but macros explicitly set
`/rosworm/saveSteps false`; the trees contained zero rows. Two minimal
step-enabled 10M v2.1 production reruns were therefore required. They use the
same nominal source/environment architecture and seeds.

## Deposited-energy record and spatial assignment

For every positive deposition in a worm physical compartment, the ROOT
`steps` tree stores:

- event, region, particle, track, and parent identifiers;
- deposited energy and pre-step kinetic energy;
- step length and pre/mid/post coordinates;
- body containment at those coordinates;
- process and creator-process type/subtype;
- the authoritative deposition coordinate and its assignment code.

Charged-particle deposition is assigned to the midpoint of a step bounded by a
0.5 micrometre maximum. Neutral discrete-interaction deposition is assigned to
the post-step interaction point. This hybrid definition avoids treating the
middle of a long photon flight as the interaction location.

An initial v2.1 implementation revealed that `G4UserLimits` existed without
`G4StepLimiterPhysics`; the macro step limit was inert and depositing electron
steps reached about 187 micrometres. Those preliminary spatial results are
superseded. The physics list now registers the limiter, the log prints the
active limit, and direct ROOT QC verifies charged deposition steps at or below
0.5 micrometres. Pre/mid/post/hybrid scoring is retained as an assignment
sensitivity.

The scorer requires finite positive deposition and an in-body authoritative
coordinate. It verifies that the sum of positive step deposits equals the
event-level whole-worm deposit; a mismatch aborts. Both 10M production runs
have exact equality and zero invalid or out-of-body scoring rows.

## Nervous-surface-referenced deposition

The original 1,355,686-triangle
`NervousSystem_baked_union.stl` is the authoritative distance atlas. A VTK
static cell locator calculates exact unsigned point-to-triangle distance for
each eligible deposition. Bins are 0–1, 1–2, 2–5, 5–10, 10–25, 25–50, and
at least 50 micrometres. Each bin reports total energy, energy/history,
fraction of whole-worm energy, energy per whole-worm Gy, contributing events,
step count, and event-level uncertainty. This endpoint is not neural absorbed
dose.

Matched-atlas nulls use the identical high-resolution surface under small
contained translations/rotations, preserving triangle content and surface
area exactly. Twelve accepted transforms are compared with the real atlas on a
deterministic 1M event-ID prefix. The empirical p value is `(1 + number nulls
at least as large as real)/(1 + number nulls)`.

## Analysis-only neural volume

The aggregate nervous STL is open/nonmanifold and is not used as an interior.
The source manifest identifies 276 component nervous objects. Actual content
checks after merging facet-duplicate vertices show that every component is
watertight and consistently wound. The set-theoretic union of their interiors
therefore supplies a mathematically valid analysis ROI without global Boolean
repair, hole filling, smoothing, or a physical Geant4 volume.

Union occupancy is sampled on body-clipped grids of 0.25, 0.5, 1, and 2
micrometre pitch. QC includes bounds, volume, mass, outside-body fraction,
26-connected components, largest-component fraction, longitudinal morphology,
visual overlay, symmetric p50/p95/p99 surface error, and a sampled maximum.
The primary density is 1.04 g/cm3 (`G4_BRAIN_ICRP` proxy); 1.00 g/cm3 is a
required sensitivity. Neither is a measurement of worm neural density.

The primary neural numerator uses exact membership in any of the 276 source
interiors. The mass uses the finest body-clipped voxel volume:

`D_neural = sum(Edep in exact member union) / (V_0.25 × 1.04 g/cm3)`.

Voxel-specific doses define a reconstruction interval. The exact-member
numerator avoids making scientific classification depend on one voxel pitch;
the finest-grid volume supplies a reproducible mass for overlapping objects.

## Whole-worm and body-wall-muscle dose

Whole-worm mass is the sum of mutually exclusive physical scoring masses.
Whole-worm mean dose is total energy divided by that mass. Body-wall-muscle
dose is physical region-3 energy divided by the physical muscle mass. Neural,
muscle, and whole-worm results are reported on the same basis:

`R_region = D_region / D_whole-worm`.

Stochastic standard errors use event-level sample variance. Ratio errors use
first-order covariance propagation because numerator and denominator share
histories. Reconstruction, registration, step-position, source/environment,
and experimental dosimetry intervals are kept separate from Monte Carlo
standard errors.

## Registration and physical-input sensitivities

Atlas registration is varied by ±2 micrometres in X/Z, ±5 micrometres
longitudinally, and ±3 degrees about Y, while checking body containment. The
full 10M caches are used for registration intervals.

Corrected 1M runs test soft/hard source spectra, worm-only environment,
water-material substitution, and independent seeds. They use the same active
0.5 micrometre limiter. Because the neural ROI receives very few events at
1M, these runs test perineural edep and muscle dose quantitatively; neural-dose
variant estimates are retained with explicit power warnings.

The reported experimental dose is conditionally treated as whole-worm mean
dose. The Cannon setup's approximate factor-of-two dosimetry uncertainty is
propagated as a 0.5×–2× external multiplicative interval, not a Gaussian error.
Fluence-linear conditions reuse transport and scale local energy; nominally
different Gy/s values do not trigger redundant transport simulations.

## Deposited-energy-weighted Geant4-DNA chemistry

The preserved chem6-derived liquid-water lifecycle and IRT timing are unchanged.
For neural ROI, 0–5 micrometre perineural region, and muscle, electron
deposition is binned by pre-step kinetic energy. Bin weight is local electron
deposited energy rather than electron-birth count. Six seeded 10k chemistry
runs (focused/diffuse × neural/perineural/muscle) report species G values at
1 ps, 10 ps, 100 ps, 1 ns, 10 ns, 100 ns, and approximately 1 microsecond.

Absolute local molecule equivalents are

`N_s(t) = Edep_local / (100 eV) × G_s(t)`.

The full local deposited-energy budget is used, while the spectrum comparison
is electron conditioned. This is a homogeneous-water yield conversion, not a
surviving intracellular molecule count. v2 birth-count spectra are retained
as a sensitivity comparison.

A direct nanometre track-chemistry continuation is not supported: the
condensed-history transport records micrometre-bounded steps, not the
individual liquid-water ionizations/excitations required to seed a faithful
Geant4-DNA track. Treating each step as one local electron would invent track
structure and was rejected.

## LITE-1-relevant target chemistry

Primary literature supports Level-1 chemical opportunity only. The model uses
OH + free tryptophan `k=(1.25±0.30)×10^10 M^-1 s^-1` and OH + free cysteine
`k=(5.35±0.82)×10^9 M^-1 s^-1`. For target concentration `C` and generic
background scavenging `k_bg`, the capture fraction is

`f = kC/(kC+k_bg)`.

Concentrations 1 micromolar–1 millimolar and `k_bg=10^8–10^10 s^-1` are swept.
H2O2 molecule-time integral from 1 ps to 1 microsecond is combined with a
PRDX-family `10^5–10^8 M^-1 s^-1` bracket. The target concentration and
background are assumptions, not fitted values. Results are interaction
opportunities/encounter capacities, not residue modifications or receptor
activation. The evidence audit is in `LITE1_MECHANISTIC_EVIDENCE.md`.

## Validation gates

Release requires: nonzero step records; exact step/event energy conservation;
zero invalid/out-of-body scoring locations; logged active step limit; verified
charged step lengths; source/macro/seeds in manifests; ROI hashes; chemistry
input hashes; all required tables/figures; and machine-readable release audit.

## Primary references

- Cannon et al. (2023), DOI [10.3389/fnins.2023.1210138](https://doi.org/10.3389/fnins.2023.1210138).
- Gong et al. (2016), DOI [10.1016/j.cell.2016.10.053](https://doi.org/10.1016/j.cell.2016.10.053).
- Bhatla and Horvitz (2015), DOI [10.1016/j.neuron.2014.12.061](https://doi.org/10.1016/j.neuron.2014.12.061).
- Hanson et al. (2023), DOI [10.1016/j.cub.2023.07.008](https://doi.org/10.1016/j.cub.2023.07.008).
- Armstrong and Swallow (1969), DOI [10.2307/3573010](https://doi.org/10.2307/3573010).
- Mezyk (1996), DOI [10.2307/3579203](https://doi.org/10.2307/3579203).
- Geant4-DNA chemistry documentation: [official Geant4 application guide](https://geant4.web.cern.ch/documentation/dev/bfad_html/ForApplicationDevelopers/TrackingAndPhysics/physicsProcess.html).
