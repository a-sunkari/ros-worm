# ROS-Worm v2.1 scientific plan

Date: 2026-08-31  
Branch: `ai/neural-dose-lite1-v2.1`  
Baseline: `ai/thesis-grade-v2` at `402dafd`

## Why v2.1 is necessary

V2 established stable anatomy-informed photon transport, explicit Cannon-like
source/environment brackets, exact nervous-surface proximity of in-body
secondary-electron births, matched-atlas nulls, muscle comparison, and the
validated chem6-derived water-radiolysis lifecycle. Its central limitation is
real: electron creation near an atlas is not energy deposited in neural tissue.
Its exposure-level molecule-equivalent calculation also uses electron birth
kinetic energy rather than measured local deposited energy.

Inspection of the actual focused and diffuse 10M ROOT files confirms that both
contain the `steps` schema but zero rows because their macros set
`/rosworm/saveSteps false`. Those files remain authoritative for v2 birth and
regional-deposition results, but cannot answer the v2.1 spatial-edep question.
Minimal step-enabled transport reruns are therefore required.

## V2 results that remain authoritative

- The stable non-neural Geant4 transport geometry and material assignments.
- The original full-resolution nervous STL as the anatomical reference atlas.
- The W 50 kV and Ag 20 kV soft/nominal/hard source brackets and experimental
  NGM/M9/substrate models, including their stated limitations.
- The focused/diffuse secondary-electron birth-proximity results and their
  matched-atlas null interpretation.
- The quantified non-neural navigation-warning rates.
- The chem6-derived Geant4-DNA lifecycle and time-resolved homogeneous-water G
  values, subject to replacing birth-energy exposure normalization in v2.1.

V2 will not be rewritten or relabeled. V2.1 is additive and will cite the exact
v2 results it reuses.

## Primary deposited-energy endpoint

The primary endpoint will be **nervous-surface-referenced deposited energy**:
the sum of positive Geant4 step energy deposits whose midpoint lies in each
exact closest-distance shell around the original full-resolution nervous
surface (0–1, 1–2, 2–5, 5–10, 10–25, 25–50, and >=50 micrometres), after finite
coordinate and whole-body containment checks.

For each shell the analysis will report deposited energy, energy/history,
fraction of whole-worm deposited energy, energy normalized per whole-worm Gy,
contributing events, particle composition, and event-level stochastic
uncertainty. The shell endpoint is not called neural dose because no neural
mass is implied.

The transport output will retain pre-, midpoint-, and post-step positions. A
2-micrometre maximum biological step already bounds spatial assignment error;
midpoint-versus-endpoint sensitivity will be checked. Process-defined-step
metadata may be recorded for diagnostics, but it will not be treated as an
unambiguous causal allocation of continuous energy loss.

## Analysis-only neural volume and dose

No nervous volume will be inserted into Geant4. Candidate analysis-only ROIs
will be derived from the unmodified high-resolution atlas on 0.25, 0.5, 1, and
2 micrometre grids where computationally practical. Candidate constructions
will include direct voxel occupancy/interior reconstruction and explicitly
parameterized implicit/morphological alternatives if the non-watertight input
prevents a stable interior.

Every ROI will be intersected with the validated body envelope and evaluated
for volume, mass, components, bounds/centroid, outside-body fraction,
longitudinal morphology, and surface-distance errors (p50/p95/p99 and a
Hausdorff-like maximum). Density will be 1.04 g/cm3 only as an explicit brain-
tissue proxy, with 1.00 g/cm3 water sensitivity; neither value is a measured
worm-neuron density.

For each accepted ROI:

`D_neural = sum(step edep inside ROI) / (ROI volume * assumed density)`

The scientifically decisive convergence quantity is neural dose, not mesh
watertightness. Body-wall muscle dose from the existing physical compartment
will provide a same-scale tissue comparison.

## Falsification and invalidation criteria

The neural-volume method will not support an authoritative neural absorbed dose
if any of the following occurs:

1. neural dose changes materially without convergence as grid pitch decreases;
2. accepted ROIs require undocumented hole filling or destructive topology
   changes;
3. outside-body volume, bounds, centroid, or longitudinal morphology are not
   anatomically credible;
4. geometric errors are large relative to neurite dimensions or dominate the
   inferred dose;
5. dose changes more with plausible ROI thickness/registration than can be
   bounded honestly;
6. step midpoint assignment or maximum-step length materially changes the
   conclusion;
7. the real-atlas edep result is indistinguishable from surface-area-matched
   internal nulls.

If dose does not converge, v2.1 will retain surface-referenced edep shells as
the primary result and report a reconstruction-dependent neural-dose interval,
not a single neural dose.

## Chemistry replacement and comparison

The primary exposure-level radiolysis normalization will use actual deposited
energy in the neural ROI, perineural shells, and muscle compartment. It will be
compared against the v2 birth-energy approximation and an edep-weighted local
electron spectrum. A direct local track-chemistry treatment will be attempted
only if the saved transport state and Geant4-DNA interface support it without
inventing track structure that condensed-history transport did not record.

## Supported level of LITE-1 modeling

The starting evidence boundary is deliberately Level 1: quantify availability
of radiogenic interactions with tryptophan-like, thiol/cysteine-like, and
H2O2/redox-relay target classes using primary-literature kinetics and explicit
concentration/oxygen/pH brackets. These are chemical opportunity metrics, not
LITE-1 activation probabilities.

A phenomenological response index will be added only if primary literature
provides quantitative, calibratable LITE-1-dependent response data with a
defensible exposure axis. A receptor open probability will be reported only if
a validated biochemical/channel-gating model exists. Neither stronger level is
assumed in advance.

## Execution gates

1. Extend and regression-test sparse step output at 1k/100k.
2. Establish full-surface edep shells before any volumetric claim.
3. Run ROI convergence and reject nonconvergent constructions.
4. Run paired 1M stochastic/geometry falsification cases before 10M nominal
   step-enabled production.
5. Base primary chemistry budgets on local edep.
6. Complete the primary-literature evidence table before implementing target
   kinetics.
7. End with a skeptical claim-by-claim paper-readiness review.
