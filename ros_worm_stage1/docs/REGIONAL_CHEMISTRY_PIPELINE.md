# Region-specific chemistry pipeline

This document describes the next Stage-1 extension after the first successful
transport-to-chemistry run.

## Goal

The original Stage-1 workflow generated a single electron spectrum from the
whole simplified worm region and used it to drive Geant4-DNA water radiolysis.
That proves the physics/chemistry bridge works, but it does not yet tell us how
radiolysis products differ between anatomical targets.

The regional pipeline runs transport once, then generates separate chemistry
inputs for each scoring region that has electron hits.

Current Level-1 region IDs:

| ID | Region | Interpretation |
|---:|---|---|
| 1 | worm | whole simplified worm body |
| 2 | head | head proxy; may be zero-hit depending on beam/statistics |
| 3 | vnc | ventral nerve cord proxy; may be zero-hit depending on beam/statistics |
| 4 | bodywall | body-wall / muscle proxy |
| 5 | intestine | intestine proxy |

The default regional pipeline runs regions `1:worm`, `4:bodywall`, and
`5:intestine`, because those are the regions that produced nonzero electron
steps in the current working run.

## Command

```bash
./scripts/run_region_chemistry_pipeline.sh region_test
```

To include all current proxy regions:

```bash
REGIONS="1:worm 2:head 3:vnc 4:bodywall 5:intestine" \
  ./scripts/run_region_chemistry_pipeline.sh all_regions
```

Zero-hit regions are skipped rather than crashing the pipeline.

## Outputs

The run writes to:

```text
results/<run_name>/
```

Main files:

```text
transport.log
transport_summary.txt
dose_scaling_1.0Gy_s.txt
transport_output0.root
region_species_summary.csv
region_species_summary.txt
```

Per-region outputs:

```text
results/<run_name>/regions/region1_worm/
results/<run_name>/regions/region4_bodywall/
results/<run_name>/regions/region5_intestine/
```

Each per-region folder contains:

```text
electron_spectrum.csv
spectrum_generation.txt
chemistry.log
Species.txt
Species*.root
species_summary.csv
species_summary.txt
```

## Interpretation

This is still a water-radiolysis model. Region-specific chemistry means:

```text
transport region electron spectrum -> local water chemistry yields
```

It does not yet mean a full biochemical ROS model with oxygen, scavengers,
membranes, mitochondria, LITE-1 biophysics, or antioxidant response. Those are
future layers.

## Why this is the right next step

Before importing OpenWorm geometry, the code needs to reliably support:

1. multiple region spectra from one transport run;
2. separate chemistry runs for each region;
3. a combined table of radiolysis products by region;
4. reproducible result directories.

That creates the analysis structure needed for OpenWorm-informed anatomical
regions later.
