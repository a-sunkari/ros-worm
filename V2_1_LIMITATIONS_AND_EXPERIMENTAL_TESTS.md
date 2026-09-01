# V2.1 limitations and discriminating experiments

## Dominant limitations

1. Cannon-condition dose has an approximate factor-of-two experimental
   interval. This dominates the focused neural-dose uncertainty.
2. The analysis-only neural volume is a union of OpenWorm source objects, not a
   histologically measured membrane/cytoplasm volume. Registration changes
   focused deposition by up to +28% and diffuse by roughly −30% to +42% under
   the tested bracket.
3. Diffuse 10M neural dose has only 30 contributing events. More histories can
   improve this one limitation.
4. Exact specimen-plane spectra and polycapillary transmission were not
   recovered; soft/nominal/hard brackets are used.
5. M9 geometry materially affects diffuse spatial deposition. Per-animal liquid
   depth is not known.
6. Water radiolysis is not intracellular biochemistry. Oxygen, macromolecular
   scavengers, antioxidant recycling, and seconds-scale clearance are absent.
7. LITE-1 target abundance and protein-bound reaction rates are unknown. No
   activation or gating metric is calibrated.
8. Matched-atlas nulls reject a neural-specific perineural enrichment claim.
9. Navigation warnings remain rare but nonzero at non-neural boundaries.
10. Fluence-linear simulation cannot by itself explain behavioral thresholds,
    adaptation, or dose-rate effects at fixed total dose.

## Highest-value experiments

### 1. Measure source spectrum and dose in the exact dish geometry

Measure photon spectra at the agar/M9 plane for the W/50 kV focused and Ag/20
kV diffuse sources, with the actual nozzle, filtration, polycapillary, distance,
and dish. Co-locate film/microdosimetry at the worm plane. This would collapse
the largest physical uncertainty and make absolute regional dose publishable.

### 2. Separate total dose from dose rate

Deliver equal total dose with different dose rates/exposure durations. The
transport/radiolysis source term here is fluence-linear; a response that depends
strongly on dose rate at fixed total dose would implicate biological clearance,
adaptation, or nonlinear redox/channel kinetics rather than transport.

### 3. Test radical and H2O2 pathways separately

Use compatible extracellular/intracellular hydroxyl scavengers, catalase/H2O2
manipulation, antioxidants, and PRDX-2 perturbations while measuring behavior
and, if possible, LITE-1-dependent cellular current/calcium. The model predicts
prompt radical production and slower H2O2 accumulation, but it does not predict
that either is activating. Opposite effects are scientifically possible.

### 4. Mutational discrimination

Compare X-ray responses for LITE-1 variants affecting W77/W328, C44, the
putative chromophore pocket, and proposed PRDX-2 interaction residues. A shared
UV/X-ray loss-of-function pattern would support common receptor chemistry; a
distinct X-ray pattern would argue for a different intermediate.

### 5. Neural versus ectopic muscle matched-dose experiment

Quantify LITE-1 expression and response in neural and pmyo-3 muscle lines under
the same measured dose. The model predicts same-order tissue dose and similar
water G values. Large response differences should therefore track expression,
cellular redox environment, or downstream excitability rather than X-ray
absorption.

### 6. Register anatomy to irradiation

Image a fluorescent nervous-system marker and body outline during or immediately
before exposure. Construct animal-specific transforms and rerun the existing
postprocessor. This directly tests the current ±2/±5 micrometre and ±3 degree
registration bracket.

### 7. Time-resolved redox measurement

Use fast H2O2/redox reporters with sham, wild-type, lite-1, and antioxidant
controls over subsecond to behavioral times. The Geant4-DNA curves describe
picosecond–microsecond spur chemistry; the critical missing bridge is how much
survives and accumulates during a 10–20 s exposure.

## Falsifying outcomes

The radiolysis-intermediate hypothesis would be weakened if measured
specimen-plane conditions yield much lower local dose than modeled; if
scavenging/PRDX perturbation leaves LITE-1-dependent X-ray responses unchanged;
if X-ray-sensitive LITE-1 mutants preserve none of the Trp/Cys/redox features;
or if a non-radiolytic control reproduces the phenotype while redox reporters
show no exposure-associated change. These outcomes should be reported, not
reinterpreted away.
