# OpenWorm mesh-compartment pipeline

Purpose: programmatically derive and test a Wu-style **mesh compartment** model from the repaired OpenWorm per-object STLs.

This does **not** voxelize the physical Geant4 geometry. It does:

1. classify repaired OpenWorm STL objects into compartment roles,
2. write Geant4-validator manifests for category tests,
3. parse Geant4 overlap logs into useful pair tables,
4. optionally build aggregate compartment STL candidates in Blender using JOIN or BOOLEAN UNION,
5. optionally run containment checks against the outer body mesh.

The intended first physical model is:

- `whole_body` = outer body / Cuticle mesh as parent volume
- internal material compartments = digestive/pharynx/intestine, reproductive/rectal, body-wall muscle, excretory if clean enough
- neurons/support cells = mesh scoring atlas for later postprocessing, not physical volumes initially

## 0. Expected input

Use your repaired manifest:

```bash
/home/asunkari/ros-worm/openworm_geometry/object_stls_repaired_meshfix_defective/openworm_object_stl_manifest_repaired.csv
```

## 1. Make role annotations and compartment manifests

```bash
cd ~/ros-worm/openworm_geometry
python /path/to/scripts/make_compartment_manifests.py \
  --manifest /home/asunkari/ros-worm/openworm_geometry/object_stls_repaired_meshfix_defective/openworm_object_stl_manifest_repaired.csv \
  --outdir /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline
```

Outputs:

- `manifest_with_compartment_roles.csv`
- `compartment_groups.json`
- `manifest_wu_core_children.csv`              # digestive + reproductive only
- `manifest_material_children_no_body.csv`      # material children excluding whole body
- `manifest_scoring_atlas.csv`                  # neurons/support cells for scoring later
- `role_summary.csv`

## 2. Run overlap tests on candidate children

These tests intentionally exclude `whole_body` because in Geant4 the body should be the parent volume, not a sibling.

```bash
cd ~/ros-worm/openworm_geant4_object_validator/build

./openworm_validator \
  --manifest /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/manifest_wu_core_children.csv \
  --mm-per-unit 0.1 --res 1000 --tol-mm 0.0001 --maxerr 20 \
  > wu_core_children_overlap.log 2>&1

../scripts/summarize_validator_log.sh wu_core_children_overlap.log | tee wu_core_children_overlap_summary.txt
```

Parse pair details:

```bash
python /path/to/scripts/parse_overlap_log.py \
  --log wu_core_children_overlap.log \
  --out-csv wu_core_children_overlap_pairs.csv
```

Then test a richer material-child set:

```bash
./openworm_validator \
  --manifest /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/manifest_material_children_no_body.csv \
  --mm-per-unit 0.1 --res 1000 --tol-mm 0.0001 --maxerr 20 \
  > material_children_overlap.log 2>&1

../scripts/summarize_validator_log.sh material_children_overlap.log | tee material_children_overlap_summary.txt
python /path/to/scripts/parse_overlap_log.py --log material_children_overlap.log --out-csv material_children_overlap_pairs.csv
```

## 3. Optional: build aggregate STL compartment candidates in Blender

Start with `--method join` for visual checks. This preserves geometry but does not boolean-union it.

```bash
blender --background --python /path/to/scripts/build_compartment_unions_blender.py -- \
  --manifest /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/manifest_with_compartment_roles.csv \
  --groups /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/compartment_groups.json \
  --outdir /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/aggregate_join \
  --compartments whole_body,digestive_system,reproductive_system,bodywall_muscle,excretory_system \
  --method join
```

Try boolean union only after visual/join checks:

```bash
blender --background --python /path/to/scripts/build_compartment_unions_blender.py -- \
  --manifest /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/manifest_with_compartment_roles.csv \
  --groups /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/compartment_groups.json \
  --outdir /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/aggregate_boolean \
  --compartments digestive_system,reproductive_system,bodywall_muscle,excretory_system \
  --method boolean_union
```

`boolean_union` may fail on some groups; the report tells you where. Do not assume it is correct without visual and Geant4 validation.

## 4. Optional: containment check against whole body

```bash
python /path/to/scripts/check_compartment_containment.py \
  --body-stl /home/asunkari/ros-worm/openworm_geometry/object_stls_repaired_meshfix_defective/stl/Cuticle.stl \
  --manifest /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/manifest_wu_core_children.csv \
  --out-csv /home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/wu_core_containment.csv \
  --samples-per-object 5000
```

This checks whether child compartment surface samples are inside the body mesh. Requires `trimesh` and usually `rtree`.

## Interpretation

- If `manifest_wu_core_children` has low/no digestive-vs-reproductive overlaps, then the Wu-style baseline is viable.
- If `manifest_material_children_no_body` is noisy, inspect which categories cause conflict; do not blindly include all material-like objects.
- Neurons/support cells should remain in `manifest_scoring_atlas.csv` first, then used for scoring/postprocessing.
