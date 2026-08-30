# Validation, known issues, and next steps

## Trusted validation results

### 100k no-physical-nervous exact-surface redo

This run reproduced the earlier surface-proximity result closely:

- input secondaries: 875
- <=5 um: 44
- fraction <=5 um: 5.03%
- median distance: 44.63 um
- p05: 5.17 um
- p95: 130.97 um

The earlier run had 878 secondaries, 44 <=5 um, and ~5.01% near-neural fraction.

That level of agreement is the strongest evidence that the recovered no-physical-nervous + exact-surface pipeline is numerically reproducible.

### 10M focused run with decimated neural surface

Recorded high-stat run:

`results/focused_10M_noPhysicalNervous_decimatedSurface_20260630_220943`

Results are local/generated and may not be tracked in git because `results/` is ignored.

Recorded values:

- events: 10,000,000
- secondary electrons: 91,489
- total scored edep: ~316,723 keV
- <=0.5 um: 0.164%
- <=1 um: 0.415%
- <=2 um: 1.149%
- <=5 um: 4.568%
- <=10 um: 11.53%
- <=25 um: 31.99%
- <=50 um: 52.42%

The high-stat shell fractions are broadly consistent with the 100k validation.

## Navigation warnings

With the nervous system removed as a physical daughter volume, nervous-related warning pairs disappeared.

The 10M run still had approximately 195 actual navigation/stuck-track incidents. The raw grep count was ~390 because both `GeomNav1002` and `Stuck Track` lines were counted.

Recorded pair counts:

- 174 `WholeBodyEnvelope <- ExcretorySystem`
- 7 `WholeBodyEnvelope <- BodyWallMuscle`
- 7 `WholeBodyEnvelope <- DigestiveSystem`
- 6 `DigestiveSystem <- WholeBodyEnvelope`
- 1 `WholeBodyEnvelope <- ReproductiveSystem`

These are low-frequency but not zero. The ExcretorySystem/body-envelope interface should be the first physical-geometry cleanup target.

## Out-of-body secondary issue

The 10M exact-surface metadata reported a maximum secondary Y coordinate around +50.7 mm, while the worm is sub-mm. The maximum neural-surface distance was therefore ~50 mm, even though the median and p95 remained biologically sized.

Do not simply discard such rows without audit.

Next diagnostic should determine:

1. whether these are legitimate escaped secondaries recorded after leaving the worm;
2. whether the scorer is intended to operate on *all* secondaries or only production/scoring points inside the worm;
3. whether transport ntuple semantics distinguish creation position, step position, or final track position;
4. whether a geometry/world coordinate bug exists.

If escaped secondaries are legitimate, define and document a body/ROI filter before computing biological proximity statistics.

## Chemistry validation

The chemistry side is based on Geant4-DNA `chem6` and should be treated as water radiolysis driven by transport-derived electron spectra.

Do not describe its OH/H2O2/eaq outputs as measured intracellular ROS concentrations without additional oxygen/scavenger/biomolecular chemistry.

Useful next chemistry checks:

- verify identical baseline behavior against the known `chem6` workflow;
- generate spectra for the Bolding/Cannon dose/exposure conditions;
- normalize species yields per Gy and per exposure;
- explicitly state chemistry medium assumptions;
- decide whether near-neural spectra should be fed into chemistry as a separate ROI analysis.

## Required next steps, in order

### 1. Audit the out-of-body secondary semantics

Inspect `transport_manifest` ntuple writing code and a few offending event IDs. Establish whether the +50 mm points are valid escaped tracks or a bug.

### 2. Clean the remaining non-neural navigation interface

Start with ExcretorySystem <-> WholeBodyEnvelope. Use cheap 100k tests and overlap/containment diagnostics. Do not globally shrink all organs as a first response.

### 3. Make nervous scoring production-safe

Choose one of:

- memory-efficient exact triangle proximity on the full-resolution mesh;
- a quantitatively validated multiresolution/BVH approach;
- a converged implicit/voxel neural ROI.

Keep the current decimated surface only as a documented approximation.

### 4. Reproduce the experimental matrix

At minimum, model focused 50 kV conditions near 1 Gy/s and diffuse conditions around 0.19, 0.38, 0.56, and 0.74 Gy/s with the exposure durations used in the experimental work. Do not rely on filenames; inspect `/run/beamOn`, source type, kVp, spot size, and normalization in every macro.

### 5. Couple transport to chemistry cleanly

Produce regional and near-neural electron spectra from the same authoritative transport run, run chemistry, and generate one machine-readable run manifest containing:

- git commit SHA
- geometry manifest
- STL hashes or paths
- macro contents/hash
- materials config
- random seeds if controlled
- event count
- dose normalization
- output files

### 6. Generate final figures

Final visualization set should include:

- whole-body + physical compartments
- high-resolution nervous atlas overlay
- beam footprint/direction
- representative secondary tracks/creation points
- <=5/10/25/50 um near-neural points
- dose/energy-deposition by compartment
- chemistry yields versus dose/exposure
- geometry QC figure showing why nervous is scored as an atlas rather than a physical solid

## Completion criterion

The project is ready for scientific handoff when a fresh clone can reproduce one focused and one diffuse case, regenerate the neural proximity/ROI analysis, regenerate the chemistry outputs, and produce the final figures without undocumented manual geometry edits.
