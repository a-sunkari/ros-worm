# ROS Worm Stage-1 Geant4 / Geant4-DNA Workflow

This repository contains the first working ROS-Worm physics/chemistry bridge for Dr. Bolding's X-ray/ROS modeling project.

It is **not** the final OpenWorm anatomical model. It is the stable regression-test layer we will build on.

## Current working pipeline

```text
transport/ros_worm
  simplified C. elegans-sized worm/agar X-ray transport
  → output0.root
  → electron_spectrum.csv

chemistry/ros_worm_chem
  chem6-derived Geant4-DNA water radiolysis
  → Species*.root
  → Species.txt
```

The chemistry code preserves the working Geant4 `chem6` lifecycle. The ROS-Worm-specific change is limited to source generation: `ros_worm_chem` can sample electron energies from `electron_spectrum.csv`.

## One-command build

```bash
./scripts/build_all.sh
```

## One-command stage-1 run

```bash
./scripts/run_stage1_pipeline.sh first_run
```

Outputs will be copied to:

```text
results/first_run/
```

including:

- `transport.log`
- `transport_summary.txt`
- `dose_scaling_1Gy_s.txt`
- `electron_spectrum.csv`
- `chemistry.log`
- `species_summary.txt`
- `species_summary.csv`
- `Species*.root`
- `Species.txt`

## Manual coupled run

```bash
# 1. Transport side
cd transport/build
./ros_worm macros/run_focused_transport.mac
python3 analysis/summarize_transport.py output0.root
python3 analysis/make_chemistry_spectrum.py output0.root --region 1 --output electron_spectrum.csv

# 2. Chemistry side
cp electron_spectrum.csv ../../chemistry/build/electron_spectrum.csv
cd ../../chemistry/build
./ros_worm_chem ros_spectrum.in
python3 analysis/summarize_species_root.py --latest --csv species_summary.csv Species*.root
```

## Region IDs in transport step output

| ID | Region |
|---:|---|
| 1 | whole worm |
| 2 | head proxy |
| 3 | ventral nerve cord proxy |
| 4 | body-wall / muscle proxy |
| 5 | intestine proxy |


## Region-specific chemistry pipeline

After the basic Stage-1 pipeline works, run the region-specific chemistry workflow:

```bash
./scripts/run_region_chemistry_pipeline.sh region_test
```

This runs transport once, generates separate electron spectra for the current
nonzero proxy regions, runs Geant4-DNA chemistry for each region, and writes a
combined `region_species_summary.csv` table under `results/region_test/`.

To request all current proxy regions, including regions that may have zero hits:

```bash
REGIONS="1:worm 2:head 3:vnc 4:bodywall 5:intestine" ./scripts/run_region_chemistry_pipeline.sh all_regions
```

Zero-hit regions are skipped. See `docs/REGIONAL_CHEMISTRY_PIPELINE.md`.

## OpenWorm direction

The next model target is **OpenWorm-informed C. elegans anatomy**, not the mouse brain yet.

Read:

```text
docs/OPENWORM_INTEGRATION_PLAN.md
```

The short version:

1. Preserve this working Stage-1 pipeline.
2. Add OpenWorm-derived spatial region/cell tables.
3. Generate Geant4 region placements from those tables.
4. Produce region-specific spectra.
5. Run region-specific chemistry.
6. Only then add LITE-1/neuronal interpretation and mouse brain attenuation.

## Critical rule

Do not rewrite the Geant4-DNA chemistry lifecycle unless `chem6` baseline behavior still passes. The previous failures came from custom chemistry scheduling/counter code. This repo avoids that by preserving the `chem6` plumbing.

## Stage 2A: imported OpenWorm / Virtual Worm outer-body mesh

The transport code now supports a first static OpenWorm mesh mode using the
exported STL:

```text
transport/geometry/openworm/worm_outer_openworm.stl
```

Run the mesh-based pipeline with:

```bash
./scripts/build_all.sh
./scripts/run_mesh_stage1_pipeline.sh openworm_mesh_test
```

The mesh run keeps the chem6-derived Geant4-DNA chemistry pipeline unchanged.
It only replaces the analytic cylindrical worm surrogate with a tessellated
outer-body mesh for the transport stage. Internal proxy ROIs are disabled by
default in the mesh macro; use the analytic model or later OpenWorm-derived
region meshes for region-specific scoring.

See `docs/OPENWORM_STL_IMPORT.md` for details.
