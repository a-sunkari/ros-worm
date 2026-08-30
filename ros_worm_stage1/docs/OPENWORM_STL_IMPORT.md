# OpenWorm / Virtual Worm STL import path

This repo now has a first static OpenWorm geometry mode for the transport side.
It imports the exported `worm_outer.stl` as a Geant4 `G4TessellatedSolid`.
This is intentionally a conservative first import: it validates the outer-body
mesh and transport navigation before we start adding OpenWorm organ/cell meshes.

## Geometry source

The current mesh file is:

```text
transport/geometry/openworm/worm_outer_openworm.stl
```

It was exported from the Virtual Worm/OpenWorm Blender model as an outer-body STL.
The mesh is treated as a static outer body/cuticle-like solid, assigned the same
`WormSoftTissue` or water material choices used by the analytic model.

## Why `G4TessellatedSolid`?

Geant4 supports tessellated solids made from triangular facets. The STL importer
in this repo reads a standard binary STL, recenters it, maps the longest mesh
axis to the worm local `z` axis, scales the longest dimension to the requested
`meshTargetLength`, and closes the resulting `G4TessellatedSolid`.

This avoids requiring an external CADMesh dependency for the first proof-of-import.
CADMesh or GDML can still be used later if we want a more general CAD pipeline.

## Macro controls

New transport geometry commands:

```text
/worm/geometry/mode analytic|mesh
/worm/geometry/meshFile geometry/openworm/worm_outer_openworm.stl
/worm/geometry/meshTargetLength 1.0 mm
/worm/geometry/useProxyROIs false
```

`analytic` keeps the original cylinder surrogate.
`mesh` uses the STL-derived OpenWorm outer body.

For the first mesh run, proxy ROIs are disabled. This prevents analytic daughter
volumes from causing overlap/navigation issues inside a tapered tessellated body.
Once the outer-body mesh is stable, the next step is either re-enable simple
proxy ROIs carefully or import separate OpenWorm anatomical region meshes.

## Mesh-mode test

```bash
cd ~/ros-worm/ros_worm_stage1
./scripts/build_all.sh
./scripts/run_mesh_stage1_pipeline.sh openworm_mesh_test
```

The script runs:

1. STL sanity check
2. transport through imported mesh
3. electron spectrum generation from region 1
4. chem6-derived Geant4-DNA chemistry
5. species summary export

## Important interpretation

This is not yet a full OpenWorm anatomical model. It is Stage 2A:

```text
current cylinder surrogate -> static OpenWorm outer-body mesh
```

The chemistry pipeline is unchanged. The next scientific upgrade is region-level
anatomical scoring using OpenWorm-derived body wall, intestine, nerve ring/VNC,
pharynx, and other region meshes or well-defined approximate masks.
