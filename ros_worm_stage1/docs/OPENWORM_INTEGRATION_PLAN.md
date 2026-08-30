# OpenWorm integration plan for ROS-Worm

The long-term goal is an OpenWorm-informed C. elegans radiation/ROS model, not a simple cylinder. The practical path is to integrate OpenWorm in layers while keeping the validated Stage-1 transport→chemistry workflow stable.

## What OpenWorm contributes

OpenWorm is an open-source project aiming to create a virtual C. elegans. The pieces most relevant here are not a single drop-in Geant4 geometry; they are model components:

- `c302`: NeuroML2 network models based on C. elegans connectivity data.
- `CElegansNeuroML`: NeuroML-based C. elegans models and connectome-related resources.
- `Sibernetic`: C++/OpenCL/SPH-style neuromechanical/body simulation infrastructure for C. elegans locomotion.

For radiation transport, the most useful OpenWorm-derived information is spatial/anatomical: where neurons, body-wall muscle, intestine, gonads, and other tissues should be in the worm coordinate system. For chemistry, the most useful information is region-specific interpretation: which region receives dose and chemistry products. For electrophysiology, c302/NeuroML becomes relevant after we define a ROS/LITE-1-to-neuron coupling model.

## Stage 2 target: OpenWorm-informed anatomy, not full behavior yet

The next model should not immediately simulate all OpenWorm neuromechanics. The next defensible step is:

```text
OpenWorm/anatomy-derived spatial regions
→ Geant4 transport regions
→ region-specific electron spectra
→ region-specific Geant4-DNA chemistry
```

This is what “OpenWorm-based” should mean first: real anatomical placement and segmentation, while preserving the working physics/chemistry chain.

## Proposed geometry layers

### Layer A: current proxy model

- Cylinder worm body.
- Simple proxy ROIs.
- Good for debugging only.

### Layer B: OpenWorm-informed regional model

- Keep the worm body as a smooth enclosing surface.
- Replace arbitrary proxy ROIs with data-driven regions:
  - head neurons,
  - ventral nerve cord,
  - body-wall muscle quadrants,
  - intestine,
  - gonad/reproductive tract if needed,
  - pharynx,
  - hypodermis/cuticle shell.
- Store regions in a versioned CSV or JSON file.
- Generate Geant4 placements from this file.

### Layer C: cell-level point/volume model

- Add neuron/muscle cell centroids from OpenWorm/NeuroML-compatible sources.
- Use small spheres/ellipsoids or voxel labels for neuron/muscle scoring.
- Do not attempt full cell morphology until scoring and output are stable.

### Layer D: detailed mesh/particle model

- Use Sibernetic/body mesh/particle data only after region/cell-level scoring is stable.
- This may require GDML, tessellated solids, or voxelized phantom import.

## Data schema for the next implementation

Use this schema for OpenWorm-derived region placements:

```csv
region_id,region_name,parent,material,shape,center_x_um,center_y_um,center_z_um,radius_x_um,radius_y_um,radius_z_um,length_um,notes
1,whole_worm,world,water,capsule,0,0,0,40,40,500,1000,current Stage-1 body
2,head_neurons,whole_worm,water,sphere,430,0,0,35,35,35,,placeholder
3,ventral_nerve_cord,whole_worm,water,cylinder,0,-22,-15,3,3,430,860,placeholder
```

Coordinates should be in a worm-centered frame, with the body axis along x. The current Geant4 cylinder uses a local z-axis rotated into world x; be careful when converting local-to-world coordinates.

## Stage 2 acceptance criteria

Before claiming an OpenWorm-based model, require:

1. The region/cell coordinate source is documented.
2. Every Geant4 region has a clear biological interpretation.
3. A visualization/geometry overlap test passes.
4. Transport output can generate region-specific spectra.
5. Chemistry runs separately for at least whole worm, body-wall muscle, and head/neuron-rich region.
6. Results are normalized per primary and per Gy.

## Later biological coupling

After regional chemistry is stable, add biological interpretation:

```text
regional dose/electron spectrum
→ water radiolysis species yields
→ local ROS proxy
→ candidate LITE-1/neuronal activation model
```

Do not hard-code LITE-1 activation as if it is already solved. Treat it as a model layer with parameters that can be fit or bounded against Dr. Bolding's experiments.
