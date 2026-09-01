# ROS-Worm Stage 1

This directory contains the active Geant4 transport + Geant4-DNA chemistry implementation for the ROS-Worm project.

The old analytic proxy model and early OpenWorm import notes remain useful for history, but the current project direction is the manifest-driven OpenWorm-derived geometry in `transport_manifest/`.

For authoritative project status, read the repository-level docs first:

- `../AGENTS.md`
- `../docs/CURRENT_STATE.md`
- `../docs/SCIENTIFIC_CONTEXT.md`
- `../docs/GEOMETRY_AND_NERVOUS_SYSTEM.md`
- `../docs/VALIDATION_AND_NEXT_STEPS.md`

## Active transport implementation

Source:

`transport_manifest/`

Typical built executable:

`transport_manifest/build/ros_worm_manifest`

Materials:

`config/region_materials.csv`

Current preferred geometry manifest:

`../openworm_geometry/compartment_pipeline/non_nervous_priority_bake/debug_core_voxel_remesh_NO_PHYSICAL_NERVOUS_manifest.csv`

Scale:

`0.1 mm / model unit`

The preferred physical transport geometry currently includes residual body, body-wall muscle, digestive, reproductive, and excretory compartments. The nervous system is intentionally omitted as a physical Geant4 daughter volume because the high-resolution nervous atlas is not a clean watertight solid and voxelized physical versions showed resolution-dependent behavior/navigation warnings.

## Nervous-system scoring

Reference anatomical surface:

`../openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl`

Exact surface-distance scorer:

`scripts/highres_nervous_exact_surface_scoring.py`

Alignment QC:

`scripts/qc_exact_nervous_surface_alignment.py`

This reports proximity to nervous anatomy, not automatically true inside-neuron dose.

V2.1 additionally scores actual deposited-energy steps and defines an analysis-
only neural mean dose from the exact union of verified closed nervous source
objects. See `../docs/v2_1/THESIS_REPORT.md`. The ROI is never installed as a
physical daughter and does not support individual-neuron dose.

## Chemistry

`chemistry/` preserves the Geant4-DNA `chem6`-derived water-radiolysis workflow. Transport-derived electron spectra can be used as chemistry source spectra. Until oxygen/scavenger/biomolecular chemistry is explicitly added, chemistry outputs should be described as water-radiolysis species/yields rather than measured intracellular ROS concentrations.

V2.1 normalizes water radiolysis to actual local deposited energy and applies
literature-rate Trp/thiol/PRDX competition brackets. These are chemical-
opportunity metrics, not receptor activation probabilities.

## Historical scripts/docs

Several scripts and documents under this directory refer to earlier analytic-proxy or physical-nervous approaches. Do not assume they are current simply because they are present. `../AGENTS.md` defines the current authority hierarchy.
