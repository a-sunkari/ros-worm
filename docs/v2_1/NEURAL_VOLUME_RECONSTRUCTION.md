# Analysis-only neural-volume reconstruction

## Decision being tested

V2.1 does not restore a neural daughter volume to Geant4. Transport remains in
the validated non-neural physical geometry. The volume described here exists
only for post-transport point classification and mass normalization.

The full-resolution `NervousSystem_baked_union.stl` remains the authoritative
surface for closest-distance scoring. It is not a closed solid. Inspection of
the object-level source manifest revealed a more defensible volumetric route:
the atlas was assembled from 276 separately repaired nervous objects. Direct
content checks, performed after merging the facet-duplicated STL vertices,
find all 276 source objects watertight and consistently wound. Their
set-theoretic union therefore defines a valid interior without hole filling,
global Boolean repair, smoothing, or alteration of individual anatomy.

## Construction

`scripts/v2_1/build_neural_roi_v2_1.py` samples the union of the 276 source
interiors on grids anchored to the transport coordinate origin at 0.25, 0.5,
1, and 2 micrometres. Overlaps are counted once. Occupied voxel centers are
intersected with the validated whole-body envelope, and only sparse occupied
indices are saved. The original and derived geometry are never overwritten.

The primary mass proxy is

`mass = body-clipped occupied volume * 1.04 g/cm3`.

The density is the explicit `G4_BRAIN_ICRP` proxy already named in the material
table, not a measured *C. elegans* neuron density. A 1.00 g/cm3 sensitivity is
mandatory for reported dose.

## Geometric convergence found so far

The initial full-grid study gives body-clipped volumes of 8,663, 8,579, 8,872,
and 8,536 micrometres cubed at 0.25, 0.5, 1, and 2 micrometres, respectively.
The complete range is 3.9% of the 0.25-micrometre estimate. Only about 0.2-0.7%
of the pre-clipped voxel volume lies outside the body.

At 0.25 micrometres, the sampled symmetric surface-distance errors relative to
the full-resolution baked-union atlas are p50 0.119 micrometres, p95 0.246
micrometres, and p99 0.522 micrometres. The sampled maximum is much larger
(about 31 micrometres), so p95 convergence must not be presented as uniform
fidelity everywhere.

Thin, oblique processes fragment under center-sampled voxel connectivity even
at the finest pitch. This is a material limitation of the derived voxel files.
The exact member-union definition preserves each source interior; the voxel
files are resolution-study representations, not new anatomical truth.

## Final acceptance decision

The 10M production results meet a bounded, analysis-only dose standard. Across
0.25, 0.5, 1, and 2 micrometre voxel representations, focused neural/whole-
worm dose ratios were 0.819, 0.886, 0.829, and 0.912; diffuse ratios were
0.913, 1.010, 1.127, and 1.101. The full voxel-pitch range is 11% focused and
23% diffuse and is smaller than, or comparable to, the event-level uncertainty.
The exact 276-member union, normalized by the finest-grid mass, gives 0.778 ±
0.101 focused and 0.969 ± 0.224 diffuse (standard error).

This is practical convergence for the question "is neural mean dose strongly
different from whole-worm mean dose?" It is not evidence that every thin
neurite has a uniquely correct volume. The accepted authoritative result is
therefore the exact-member-union numerator with the 0.25 micrometre body-
clipped mass; all voxel results remain a reconstruction interval. Surface-
referenced deposited-energy shells remain co-primary because they do not
require a neural mass.

Registration remains important. Under the stated ±2 micrometre transverse,
±5 micrometre longitudinal, and ±3 degree bracket, full-production focused
ROI deposition ranged from 1.00 to 1.28 of baseline and diffuse deposition
from 0.70 to 1.42. These are assumption intervals, not probabilistic errors.
They are reported separately from Monte Carlo uncertainty.
