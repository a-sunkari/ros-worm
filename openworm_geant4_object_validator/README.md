# OpenWorm Geant4 Object Validator

Purpose: diagnostic-only Geant4 project to load every exported OpenWorm anatomical STL as its own `G4TessellatedSolid` / physical volume and run Geant4 overlap checks.

This is intentionally separate from the ROS worm simulation code.

## Build

```bash
cd ~/ros-worm
cp -r /mnt/data/openworm_geant4_object_validator .
cd openworm_geant4_object_validator
mkdir -p build && cd build
cmake ..
make -j$(nproc)
```

## Visual sanity check of exported STLs

```bash
blender --python ../scripts/preview_openworm_object_stls_in_blender.py -- \
  /home/asunkari/ros-worm/openworm_geometry/object_stls/openworm_object_stl_manifest.csv all
```

Use the Outliner collections to toggle categories. This imports every STL in the world coordinates exported by the Blender batch exporter.

To preview only neurons/cells first:

```bash
blender --python ../scripts/preview_openworm_object_stls_in_blender.py -- \
  /home/asunkari/ros-worm/openworm_geometry/object_stls/openworm_object_stl_manifest.csv neuron-or-cell
```

## Full all-object Geant4 overlap check

```bash
cd ~/ros-worm/openworm_geant4_object_validator/build
G4FORCENUMBEROFTHREADS=1 timeout 90m ./openworm_validator \
  --manifest /home/asunkari/ros-worm/openworm_geometry/object_stls/openworm_object_stl_manifest.csv \
  --mm-per-unit 0.1 \
  --res 1000 \
  --tol-mm 0.0001 \
  --maxerr 20 \
  > all_object_overlap_check.log 2>&1
```

Summarize:

```bash
../scripts/summarize_validator_log.sh all_object_overlap_check.log | tee all_object_overlap_summary.txt
```

## Faster smoke checks

Load/check only first 20 objects:

```bash
./openworm_validator --manifest /path/to/openworm_object_stl_manifest.csv --max-objects 20 --res 500
```

Load everything but do not check overlaps:

```bash
./openworm_validator --manifest /path/to/openworm_object_stl_manifest.csv --no-check > load_only.log 2>&1
```

Exclude obvious envelope objects if you want internal-object-only overlap signal:

```bash
./openworm_validator \
  --manifest /path/to/openworm_object_stl_manifest.csv \
  --exclude-names Cuticle,hyp7 \
  --res 1000 > no_envelope_overlap_check.log 2>&1
```

Category-only check:

```bash
./openworm_validator \
  --manifest /path/to/openworm_object_stl_manifest.csv \
  --include-categories neuron-or-cell \
  --res 1000 > neuron_only_overlap_check.log 2>&1
```

## Important interpretation

This checks Geant4 placement overlaps between separate named anatomical objects. It does not mean the raw anatomy is automatically a valid final material hierarchy.

A closed outer cuticle surface may behave as a filled solid. Therefore, overlaps between internal objects and Cuticle can be expected if all objects are placed as siblings under the world. That is still useful diagnostic information, but it must be interpreted as geometry-partition evidence, not as proof that the biological anatomy is wrong.
