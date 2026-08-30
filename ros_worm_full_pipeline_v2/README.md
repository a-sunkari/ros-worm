# ROS-Worm full two-stage pipeline v2

This package adds a manifest-driven multi-compartment C. elegans transport stage and wrappers that feed region-specific secondary electron spectra into the existing Geant4-DNA/chem6-derived chemistry stage.

It is designed to be copied into an existing `/home/asunkari/ros-worm` checkout that already contains:

- `ros_worm_stage1/chemistry/` from the prior two-stage work
- the validated full worm manifest:
  `openworm_geometry/compartment_pipeline/non_nervous_priority_bake/debug_core_voxel_remesh_plus_nervous_voxel030_manifest.csv`

## What it does

Stage 1, `transport_manifest`, runs Geant4 transport through the remeshed OpenWorm-derived geometry:

- WholeBodyEnvelope / residual body
- NervousSystem
- BodyWallMuscle
- DigestiveSystem
- ReproductiveSystem
- ExcretorySystem

It writes ROOT ntuples for per-event dose, edep steps, and secondary particles. The analysis scripts then create region-specific electron spectra.

Stage 2 reuses the existing Geant4-DNA chemistry binary `ros_worm_chem` by copying each region's `electron_spectrum.csv` into the chemistry build directory and running `ros_spectrum.in`.

## Quick install

```bash
cd /home/asunkari/ros-worm
unzip /mnt/data/ros_worm_full_pipeline_v2.zip
cp -r ros_worm_full_pipeline_v2/* ros_worm_stage1/
```

Build the new transport app:

```bash
cd /home/asunkari/ros-worm/ros_worm_stage1/transport_manifest
mkdir -p build && cd build
cmake ..
cmake --build . -j"$(nproc)"
```

Build chemistry if needed:

```bash
cd /home/asunkari/ros-worm/ros_worm_stage1/chemistry
mkdir -p build && cd build
cmake ..
cmake --build . -j"$(nproc)"
```

Run full regional pipeline:

```bash
cd /home/asunkari/ros-worm/ros_worm_stage1
./scripts/run_full_worm_pipeline_v2.sh focused_1Gy_s_10s
```

Outputs go to:

```text
ros_worm_stage1/results/<run_name>/
```

## Notes

Stage 1 now uses region-specific biological/tissue-equivalent transport materials via `config/region_materials.csv`. Stage 2 intentionally remains pure-water Geant4-DNA radiolysis chemistry, driven by region-specific secondary electron spectra from Stage 1. See `docs/MATERIAL_MODEL.md`.
