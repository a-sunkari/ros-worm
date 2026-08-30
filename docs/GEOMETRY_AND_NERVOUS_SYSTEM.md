# Geometry and nervous-system strategy

## The core geometry problem

The OpenWorm/Virtual Worm source anatomy was created for visualization/biological modeling, not Geant4 solid navigation. Many anatomical pieces overlap or intersect rather than forming a mutually exclusive set of closed material volumes. This is especially severe for the nervous system, where neurites and other components visually form a plausible neural network but are not one clean Boolean-unioned solid.

The practical consequence is that a mesh may look biologically correct in 3D and still be unsuitable as a Geant4 daughter volume.

## Current physical transport geometry

The preferred transport manifest is:

`openworm_geometry/compartment_pipeline/non_nervous_priority_bake/debug_core_voxel_remesh_NO_PHYSICAL_NERVOUS_manifest.csv`

It places:

- `WholeBodyEnvelope`
- `ExcretorySystem`
- `ReproductiveSystem`
- `DigestiveSystem`
- `BodyWallMuscle`

The physical nervous system is intentionally omitted.

The body envelope and child systems are derived/remeshed versions of the source anatomy intended to reduce overlap/navigation failures. Always inspect the actual STL files referenced by the manifest; some manifest min/max metadata has been stale in earlier iterations.

## High-resolution nervous anatomy

Primary anatomical surface:

`openworm_geometry/compartment_pipeline/baked_priority_meshes_test/NervousSystem_baked_union.stl`

Recorded processed QC:

- ~1.36 million faces
- ~677k vertices
- 54 components
- not watertight
- inconsistent winding
- ~5,591 boundary edges
- 12 non-manifold edges
- ~5,290 broken faces

Despite this topology, gross visual inspection shows a recognizable *C. elegans* nervous system. That distinction is critical: **topologically invalid as a closed solid does not mean anatomically useless as a surface atlas**.

## Why previous physical nervous meshes were rejected

Two voxel-remeshed candidates were explored at approximately 0.020 and 0.030 model-unit resolution. Both became watertight, but:

- neural morphology became resolution-dependent;
- the number/topology of connected components changed substantially;
- Geant4 navigation warnings involving nervous/body or nervous/bodywall boundaries persisted or worsened;
- the nervous energy-deposition fraction changed materially between resolutions.

This means "voxelize until Geant4 stops complaining" is not a scientifically acceptable criterion.

Do not resurrect the physical voxel nervous volume as the default unless a convergence study demonstrates stable anatomy and scoring.

## Current preferred method: surface-proximity scoring

Transport is run without a physical nervous daughter volume. Saved secondary-electron positions are then scored against the high-resolution neural surface with:

`ros_worm_stage1/scripts/highres_nervous_exact_surface_scoring.py`

For every point, the script computes the nearest point on the nervous triangle mesh and the Euclidean distance. It can report threshold shells such as 0.5, 1, 2, 5, 10, 25, and 50 um.

This method is robust to the mesh being non-watertight because it does not require an inside/outside test.

Interpretation:

- `distance <= 5 um` means the secondary position is within 5 um of nervous anatomy.
- It does **not** prove the secondary was inside a neuron or other nervous tissue.

## Coordinate/alignment sanity checks already performed

At `0.1 mm/model-unit`, recorded loaded bounds were approximately:

Whole-body envelope span:

- X: 82.7 um
- Y: 879.4 um
- Z: 190.1 um

High-resolution nervous span:

- X: 56.6 um
- Y: 797.9 um
- Z: 132.0 um

0.030 voxel nervous span:

- X: 54.1 um
- Y: 780.9 um
- Z: 127.0 um

The high-resolution and voxel nervous models therefore occupy broadly the same coordinate frame. Visual alignment QC also showed near-neural points close to the expected neural structures rather than a grossly shifted/rotated mesh.

Still, any future geometry rewrite must re-run alignment QC because other physical compartments may be resampled/shrunk independently.

## Memory issue in exact surface scoring

The full-resolution nervous mesh caused the proximity scorer to consume roughly 21 GB and be killed by OOM on larger runs. A decimated derivative was generated under:

`openworm_geometry/compartment_pipeline/baked_priority_meshes_test/decimated_scoring_surfaces/`

One file is named `NervousSystem_baked_union_decimated_150k.stl`, but the actual recorded face count was about 522k. The name is historical and should not be trusted.

100k validation showed that the decimated mesh preserved >=5-10 um shell statistics reasonably well but degraded sub-2-um behavior. Therefore:

- full-resolution surface = reference for low-stat validation;
- decimated surface = pragmatic high-stat approximation;
- if sub-micron accuracy matters, develop a more memory-efficient exact method rather than relying on the current decimation.

## Better future option for true neural-volume classification

If the scientific endpoint requires "inside nervous tissue" rather than proximity, prefer constructing a validated **implicit or voxel neural ROI** from the high-resolution atlas instead of blindly closing STL holes.

A good workflow would:

1. rasterize/splat the neural surface or centerline/process geometry onto a fine grid;
2. use a physically justified effective neural/process radius or morphological dilation;
3. classify hits in the resulting volumetric mask;
4. run voxel-size/radius convergence;
5. compare reconstructed ROI to the original high-resolution mesh using surface-distance/Hausdorff metrics and visual overlays;
6. keep the ROI out of Geant4 unless physical-material separation is actually needed.

A robust Boolean/implicit surface reconstruction could also be explored, but a watertight result is not enough by itself. It must preserve neural morphology quantitatively.

## What not to do

- Do not globally scale/inflate/deflate the nervous system merely to remove overlaps without quantifying anatomical error.
- Do not replace OpenWorm with the Wu worm model; Wu is a benchmark/reference only.
- Do not infer biological correctness from `is_watertight=True`.
- Do not infer failure from `is_watertight=False` when using surface-distance scoring.
- Do not call a proximity-shell result a true nervous absorbed dose.
