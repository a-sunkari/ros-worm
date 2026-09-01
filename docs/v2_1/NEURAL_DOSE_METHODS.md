# Nervous-surface deposited energy and neural-dose methods

## Transport record

V2.1 appends fields to the existing `steps` ROOT tree without changing any v2
column. A row is written for every positive energy-deposition step in a worm
physical compartment when `/rosworm/saveSteps true`. It contains event, region,
PDG, track and parent IDs; deposited energy; pre-step kinetic energy; step
length; explicit pre/mid/post coordinates; body containment at those three
positions; and Geant4 process type/subtype identifiers.

The authoritative scoring location is the geometric midpoint of the pre- and
post-step positions. The historical `x_um/y_um/z_um` columns retain their
pre-step meaning for backward compatibility. Process labels are diagnostics;
the process that limits a step is not assumed to be the unique cause of
continuous energy loss.

## Eligibility and conservation checks

`scripts/v2_1/score_edep_v2_1.py` requires finite coordinates, positive finite
energy deposition, and midpoint containment in the whole-body envelope. It
then verifies that the sum of saved positive step deposition exactly reproduces
the per-event whole-worm ROOT total. Any discrepancy terminates the analysis.

The 1k and 100k focused tests both pass this equality exactly. They contain no
non-finite or midpoint-outside-body deposition rows and no navigation warnings.

## Surface-referenced endpoint

Every eligible midpoint is queried against the original full-resolution
nervous triangle surface. The primary shell bins are 0-1, 1-2, 2-5, 5-10,
10-25, 25-50, and at least 50 micrometres. Each row reports total deposition,
deposition/history, whole-worm deposition fraction, deposition per modeled
whole-worm Gy, contributing events, step count, and event-level uncertainty.

This is **nervous-surface-referenced deposited energy**, not neural dose.

## Volumetric dose

For each explicit analysis-only ROI:

`D_neural = sum(Edep at eligible midpoints inside ROI) / ROI mass`.

The same transport histories are scored against every pitch. Body-wall muscle
dose uses region 3 deposition and the physical compartment mass from the
transport summary. Ratios to whole-worm dose use the sum of mutually exclusive
physical-compartment masses, avoiding parent/daughter double counting.

Stochastic standard errors use event-level sample variance. Deposition-fraction
and dose-ratio errors use first-order covariance propagation because numerator
and whole-worm denominator come from the same histories. Independent-seed
replicates will be used to check those analytic errors before production.

## Required remaining sensitivities

- 0.25 versus 0.5 micrometre ROI classification and exact member-union checks;
- 1.00 versus 1.04 g/cm3 neural density;
- midpoint versus pre/post assignment and maximum-step sensitivity;
- rigid atlas registration uncertainty;
- source-spectrum and environment brackets;
- exact-atlas deposited-energy nulls;
- independent random seeds;
- neural versus physical body-wall muscle dose.

