# AGENTS.md — ROS-Worm AI operating guide

This repository has accumulated several experimental geometry pipelines. Do not infer authority from filenames such as `v2`, `1e6`, or `150k`; inspect file contents and actual mesh statistics.

## First principles

- Preserve OpenWorm anatomy where it matters biologically. Do not make a mesh "valid" by silently destroying morphology.
- Use the most detailed geometry that remains numerically stable, but distinguish **physical Geant4 material volumes** from **biological scoring ROIs/atlases**.
- Do not call proximity-to-neural-surface results "nervous absorbed dose" unless a validated volumetric neural ROI exists.
- Do not overwrite original geometry. Derived meshes must have explicit names and provenance.
- Prefer 100k-event falsification/QC tests before high-stat runs.
- Geant4 warnings are data. Count unique incidents and physical-volume pairs, not just grep lines.
- Keep the Geant4-DNA chemistry lifecycle close to the working `chem6`-derived implementation unless a baseline regression test passes.

## Current authoritative implementation

Active code: `ros_worm_stage1/`

Transport executable source: `ros_worm_stage1/transport_manifest/`

Typical built binary: `ros_worm_stage1/transport_manifest/build/ros_worm_manifest`

Materials: `ros_worm_stage1/config/region_materials.csv`

Model scale: `0.1 mm / model unit`

Current preferred transport manifest:

`openworm_geometry/compartment_pipeline/non_nervous_priority_bake/debug_core_voxel_remesh_NO_PHYSICAL_NERVOUS_manifest.csv`

Historical physical-nervous manifest, useful only for comparisons:

`openworm_geometry/compartment_pipeline/non_nervous_priority_bake/debug_core_voxel_remesh_plus_nervous_voxel030_manifest.csv`

High-resolution nervous anatomy:

`openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl`

Exact neural-surface scorer:

`ros_worm_stage1/scripts/highres_nervous_exact_surface_scoring.py`

Alignment QC:

`ros_worm_stage1/scripts/qc_exact_nervous_surface_alignment.py`

## Region IDs

1. body / residual WholeBodyEnvelope
2. nervous
3. BodyWallMuscle
4. DigestiveSystem
5. ReproductiveSystem
6. ExcretorySystem

With the preferred no-physical-nervous manifest, region 2 should have zero physical Geant4 energy deposition by design.

## Files/directories that are historical rather than authoritative

- `openworm_geant4_object_validator/` is a geometry diagnostic tool, not the production transport baseline. If used, prefer `--smoke-run` for quick checks.
- `wu_c_elegans_mesh_model/` is a literature/benchmark reference, not a replacement anatomy.
- Old Stage-1 analytic proxy documentation may describe cylindrical/head/VNC proxies and is superseded for current geometry questions.
- The former `ros_worm_full_pipeline_v2/` directory was an installation/staging package copied into Stage 1; it was removed from the working tree after the code was incorporated.

## Before changing geometry

Read:

- `docs/CURRENT_STATE.md`
- `docs/SCIENTIFIC_CONTEXT.md`
- `docs/GEOMETRY_AND_NERVOUS_SYSTEM.md`
- `docs/VALIDATION_AND_NEXT_STEPS.md`

Then verify current mesh bounds, watertightness, component count, and transforms from the actual STL files. Manifest metadata has been stale in prior iterations.

## Definition of done

A finished handoff should include reproducible transport + chemistry commands, an authoritative manifest, documented geometry transformations, stable focused and diffuse runs at Bolding/Cannon conditions, nervous-system scoring with an explicitly justified interpretation, navigation-warning audit, high-stat convergence, and publication-quality anatomy/track/ROS figures.
