# Nervous-surface deposited energy and neural-dose methods

## Transport record

V2.1 appends fields to the existing `steps` ROOT tree without changing any v2
column. A row is written for every positive energy-deposition step in a worm
physical compartment when `/rosworm/saveSteps true`. It contains event, region,
PDG, track and parent IDs; deposited energy; pre-step kinetic energy; step
length; explicit pre/mid/post coordinates; body containment at those three
positions; and Geant4 process type/subtype identifiers.

The authoritative scoring location is the geometric midpoint for a charged
particle after an enforced 0.5-micrometre step limit, and the post-step
interaction point for a neutral particle. The historical `x_um/y_um/z_um`
columns retain their pre-step meaning for backward compatibility. Process labels are diagnostics;
the process that limits a step is not assumed to be the unique cause of
continuous energy loss.

## Eligibility and conservation checks

`scripts/v2_1/score_edep_v2_1.py` requires finite coordinates, positive finite
energy deposition, and midpoint containment in the whole-body envelope. It
then verifies that the sum of saved positive step deposition exactly reproduces
the per-event whole-worm ROOT total. Any discrepancy terminates the analysis.

The corrected smoke and 10M production tests pass this equality exactly. They
contain no non-finite or scoring-position-outside-body deposition rows.

### Falsified initial implementation

The first v2.1 audit correctly saved pre/mid/post positions but uncovered a
deeper legacy defect: `G4UserLimits` was configured while
`G4StepLimiterPhysics` was absent. A paired 0.5/2-micrometre run was identical,
and actual electron steps extended to 187 micrometres. Fine spatial assignment
from those runs is invalid. The physics list now registers the limiter, the log
prints the active value, and direct ROOT checks show electron deposition steps
at or below 0.5 micrometres. Photon steps may remain long because their local
discrete deposition is scored at the post-step interaction point.

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

## Completed sensitivities and remaining power limit

The release includes 0.25/0.5/1/2 micrometre ROI classification, exact-member-
union scoring, 1.00/1.04 g/cm3 density, pre/mid/post/hybrid positions, rigid
registration, source spectra, physical environment, material model,
independent seeds, matched-atlas nulls, and muscle comparison.

The 1M variant runs are underpowered for the small neural ROI: some variants
have fewer than 10 contributing events. They are retained as falsification
tests, not used to claim precise source-specific neural-dose effects. The 10M
nominal runs, reconstruction interval, full-production registration bracket,
and event-level standard errors define the neural-dose result. Perineural
shell and muscle sensitivities have many more contributing events and are the
appropriate endpoints for 1M source/environment comparisons.
