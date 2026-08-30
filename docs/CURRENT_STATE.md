# Current project state — August 2026

## What is working

The project has a functioning manifest-driven Geant4 transport pipeline with OpenWorm-derived compartment meshes and a Geant4-DNA/chem6-derived chemistry stage.

The current production-direction transport geometry uses these physical compartments:

- WholeBodyEnvelope / residual body
- BodyWallMuscle
- DigestiveSystem
- ReproductiveSystem
- ExcretorySystem

The nervous system is currently best treated as a **post-processing scoring anatomy**, not a physical Geant4 daughter volume.

Preferred transport manifest:

`openworm_geometry/compartment_pipeline/non_nervous_priority_bake/debug_core_voxel_remesh_NO_PHYSICAL_NERVOUS_manifest.csv`

Scale:

`0.1 mm / model unit`

Materials:

`ros_worm_stage1/config/region_materials.csv`

Transport source:

`ros_worm_stage1/transport_manifest/`

## Why the nervous system is excluded from physical transport

The original high-resolution nervous geometry visually resembles the real *C. elegans* nervous system but was built from many intersecting/overlapping CAD components. The aggregate mesh is not a clean closed solid.

Last recorded processed QC for:

`openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl`

was approximately:

- faces: 1,355,686
- vertices: 676,952
- connected components: 54
- watertight: false
- winding consistent: false
- boundary edges: 5,591
- non-manifold edges: 12
- broken faces: 5,290

Voxelized nervous meshes at 0.020 and 0.030 model-unit resolution were watertight, but physical Geant4 results changed with voxel resolution and nervous-related navigation warnings appeared. That made a physical nervous-volume dose result difficult to trust.

## Current nervous-system method

Use the high-resolution nervous STL as an anatomical surface/ROI after transport. The script:

`ros_worm_stage1/scripts/highres_nervous_exact_surface_scoring.py`

computes the exact closest point on the nervous triangle surface for each saved secondary electron position and reports thresholds such as 0.5, 1, 2, 5, 10, 25, and 50 um.

This means:

- valid statement: "secondary electron occurred within 5 um of high-resolution nervous anatomy"
- invalid statement without further work: "secondary electron occurred inside nervous tissue"

The scorer explicitly records that the method is a surface-proximity shell, not a closed-volume inside test.

## Reproducibility achieved

A 100k-event no-physical-nervous rerun reproduced the earlier exact-surface result closely:

- input secondaries: 875
- within 5 um: 44
- fraction within 5 um: 5.03%
- median distance to nervous surface: 44.63 um

The older run had 878 secondaries, 44 within 5 um, and a 5.01% fraction.

This strongly suggests the no-physical-nervous + high-resolution surface-scoring path is reproducible.

## High-stat run achieved

A 10M focused run was completed locally under:

`results/focused_10M_noPhysicalNervous_decimatedSurface_20260630_220943`

The `results/` tree is ignored and is not necessarily present in git.

Recorded values:

- events: 10,000,000
- secondary electrons: 91,489
- total scored edep: ~316,723 keV
- decimated-surface 5 um fraction: 4.57%
- 10 um: 11.53%
- 25 um: 31.99%
- 50 um: 52.42%

The full-resolution ~1.36M-face proximity mesh caused an OOM kill at ~21 GB resident memory on larger scoring jobs. A derived ~522k-face surface was used for high-stat scoring and consumed ~6 GB. Its filename says `150k`, but its actual face count was ~522k; never trust that filename as a face-count assertion.

## Remaining issues

1. **True neural volume versus proximity ROI.** The current method is scientifically useful but is not an inside-neuron volume classifier. Consider a validated implicit/voxel neural ROI if the biological question requires true volumetric scoring.
2. **Non-neural navigation warnings.** The 10M run had ~195 actual stuck/navigation incidents, dominated by ExcretorySystem <-> WholeBodyEnvelope, plus smaller bodywall/digestive/reproductive boundary signatures.
3. **Escaped/outlier secondary coordinates.** The 10M scoring metadata contained at least one extreme Y coordinate near +50.7 mm despite a sub-mm worm. Audit the origin before applying any permanent filter.
4. **High-resolution scoring memory.** Replace brute-force full-triangle proximity with a more memory-efficient exact or converged approximation if sub-micron shells matter.
5. **Chemistry integration.** Regional electron spectra can feed the chem6-derived chemistry, but near-neural surface scoring and region-specific chemistry need a clearly defined coupling strategy.
6. **Focused/diffuse experimental matching.** Final runs should explicitly match the Bolding/Cannon beam geometry, dose-rate series, and exposure durations.

## Repository status after cleanup

The August 2026 cleanup removes only obvious working-tree clutter whose history is preserved by git: old build trees, backup/scratch copies, ad hoc command-note dumps, and the redundant `ros_worm_full_pipeline_v2` staging package after its relevant content had already been incorporated into `ros_worm_stage1`.

Original geometry, current derived geometry, validators, active transport/chemistry source, and literature benchmark assets are retained.
