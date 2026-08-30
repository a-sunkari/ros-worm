# Stage-1 biological material model

This revision separates **Stage 1 transport material composition** from **Stage 2 Geant4-DNA chemistry medium**.

## Why two stages

The two-stage approach is retained because Geant4-DNA chemistry is water-radiolysis centered and is not intended to run full whole-worm chemistry in heterogeneous tissue geometry. Stage 1 uses ordinary Geant4 EM transport through anatomical compartments with biological/tissue-equivalent materials. Stage 2 uses the region-specific secondary-electron source terms from Stage 1 to run liquid-water Geant4-DNA chemistry in a representative microvolume.

## Default Stage-1 mapping

| Region | Material |
|---|---|
| WholeBodyEnvelope / residual body | `G4_TISSUE_SOFT_ICRU-4` |
| NervousSystem | `G4_BRAIN_ICRP` |
| BodyWallMuscle | `G4_MUSCLE_SKELETAL_ICRP` |
| DigestiveSystem | `G4_TISSUE_SOFT_ICRP` |
| ReproductiveSystem | `G4_TESTIS_ICRP` |
| ExcretorySystem | `G4_TISSUE_SOFT_ICRU-4` |

The mapping is stored in `config/region_materials.csv` and can be changed without recompiling.

## Biological basis and limitations

C. elegans tissue-specific elemental compositions are not comprehensively tabulated. The default model uses best-available radiological tissue proxies from the Geant4/NIST material database. This is more accurate than treating all Stage-1 regions as water, while preserving the correct Geant4-DNA water chemistry stage.

C. elegans dry biomass is reported as dominated by protein with substantial lipid, nucleic-acid, and carbohydrate fractions; the intestine is a major metabolic/storage organ. This justifies treating digestive/intestine as soft biological tissue rather than pure water, while avoiding unsupported invented elemental compositions.

## Chemistry stage

The chemistry stage remains liquid water. Its output should be described as aqueous radiolysis species yields driven by compartment-specific secondary-electron spectra, not as a full biochemical ROS network in heterogeneous tissue.
