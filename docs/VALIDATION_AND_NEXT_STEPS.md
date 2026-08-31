# Validation and remaining work

> **V2 completion note (August 30, 2026):** the thesis extension has been
> executed through 100k falsification, independent 1M replicates and paired
> sensitivities, 10M focused/diffuse production, 10k time-resolved chemistry,
> compact tables, and ten figures. Remaining work is experimental
> discrimination rather than another geometry rewrite. See
> `V2_LIMITATIONS_AND_EXPERIMENTAL_TESTS.md`.

## Completed validation

Two 100k falsification runs and two 10M production runs completed with Geant4
11.3.2. The authoritative transport manifest, material file, macros, seeds, and
STL hashes are captured by each run manifest.

| case | histories | eligible electron births | within 5 µm | warning incidents | out-of-body |
|---|---:|---:|---:|---:|---:|
| focused 50 kV | 10,000,000 | 90,514 | 6,562 (7.250%) | 18 | 0 |
| diffuse 20 kV | 10,000,000 | 62,968 | 4,056 (6.441%) | 3 | 0 |

Focused scored-energy fractions were 94.52% residual body, 1.54% body-wall
muscle, 2.55% digestive, and 1.38% reproductive. Diffuse fractions were 95.28%,
1.36%, 2.26%, and 1.11%. These are fractions per incident-history simulation,
not experimental absolute doses. The tracked normalized table reports a
conditional conversion if an experimental dose is assumed to equal the model's
whole-worm average dose.

## Neural alternatives falsified

The high-resolution neural surface has open/non-manifold topology but retains
the most anatomy. Voxel 0.020 and 0.030 candidates are watertight yet differ by
65.5% in volume, show 21–33 µm p95 reference-to-candidate error, and change
inside-electron count by 2.93×. A true neural-volume result is therefore not
scientifically supported. Exact full-resolution surface proximity is the
authoritative endpoint.

## Warning and secondary audit

The historical +50.7-mm secondary was produced by a ~50.5-mm navigator step at
the excretory/body interface. Because excretory has the same material as residual
body and is tiny/disconnected, its physical boundary was removed and its mesh
retained as a post-processing ROI. New records include particle ID, creation
position, parent-step endpoints/length, and body membership. Nervous statistics
accept only finite PDG-11 births inside both recorded and geometric body tests.

Residual warnings occur at the body/digestive, body/body-wall, and one
body/reproductive boundary. At 3e-7–1.8e-6 per history without invalid output,
further anatomy-changing repair is not currently justified.

## Chemistry validation

Focused and diffuse 5-µm near-neural spectra each drove 10,000 Geant4-DNA events
through the working chem6 lifecycle. At 1 µs, focused/diffuse water G values were
1.363/1.337 molecules per 100 eV for •OH and 0.916/0.922 for H2O2. These are
model water-radiolysis yields per deposited energy, not quantities or
concentrations in a worm and not experimental ROS measurements.

## Remaining research, not workflow blockers

1. Replace the v2 physics-bracketed source ensembles with at-sample measured
   tungsten and silver spectra/fluence maps, including the exact filtration and
   polycapillary response.
2. Replace simplified v2 medium/substrate slabs with measured per-animal liquid
   depth, meniscus, dish/slide dimensions, and worm height.
3. Extend the completed independent-seed and paired one-at-a-time study to a
   larger global design spanning posture, orientation, dimensions, and source
   distance if quantitative confidence intervals beyond the current brackets
   are required.
4. Construct a true neural volume only if biological radii/segmentation data and
   a resolution-converged implicit representation become available.
5. Extend homogeneous water chemistry with oxygen/scavenger/biomolecular kinetics
   only after choosing validated concentrations and reaction data.

The present workflow is reproducible and suitable for scientific review of its
stated transport, proximity, and water-radiolysis outputs. It is not yet a
mechanistic model of LITE-1 activation.
