# Full ROS-Worm two-stage pipeline v2

## Scientific model

The package follows the two-stage strategy we discussed:

1. **Macroscopic/mesoscopic Geant4 transport** in the full multi-compartment worm geometry.
2. **Microscopic Geant4-DNA water chemistry** in a local water volume driven by region-specific secondary electron spectra.

This is intentionally not a simple edep-to-ROS proxy. The proxy layer is only optional analysis; the main chemistry stage remains the existing chem6-derived Geant4-DNA pipeline.

## Geometry used

Default geometry manifest:

```text
/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/non_nervous_priority_bake/debug_core_voxel_remesh_plus_nervous_voxel030_manifest.csv
```

Region IDs:

| ID | Region |
|---:|---|
| 1 | body / WholeBodyEnvelope |
| 2 | nervous |
| 3 | body wall muscle |
| 4 | digestive |
| 5 | reproductive |
| 6 | excretory |

## Stage 1 outputs

- `transport_output0.root`
- `transport_summary.json`
- `compartment_dose.csv`
- `edep_hits.csv`
- `secondary_electrons.csv`
- `electron_spectrum_region<ID>_<name>.csv`

## Stage 2 outputs

For every selected region:

- `regions/region<ID>_<name>/electron_spectrum.csv`
- `regions/region<ID>_<name>/Species*.root`
- `regions/region<ID>_<name>/Species.txt`
- `regions/region<ID>_<name>/species_summary.csv`

## Example commands

```bash
cd /home/asunkari/ros-worm/ros_worm_stage1
./scripts/build_full_pipeline_v2.sh
./scripts/run_full_worm_pipeline_v2.sh focused_1Gy_s_10s
```

For diffuse condition:

```bash
TRANSPORT_MACRO=macros/diffuse_50kvp.mac TARGET_DOSE_RATE=0.74 PULSE_S=20 \
  ./scripts/run_full_worm_pipeline_v2.sh diffuse_0p74Gy_s_20s
```

## Important assumptions

- Stage 1 treats worm compartments as water-equivalent unless you later assign tissue-specific materials.
- Stage 2 chemistry is pure-water Geant4-DNA radiolysis, not full tissue biochemical ROS.
- Region-specific chemistry means region-specific electron spectra drive local water chemistry.
- Absolute dose-rate normalization requires experimental/source calibration. The current scripts report the requested target dose-rate and pulse duration but do not infer beam current automatically.


## Stage-1 material model

Stage 1 assigns tissue-equivalent materials by anatomical region using `config/region_materials.csv`. Stage 2 remains liquid-water Geant4-DNA chemistry. See `docs/MATERIAL_MODEL.md`.
