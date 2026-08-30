# Realism and validation notes for the current Stage-1 model

## What is realistic enough for Stage 1

The current workflow is physically meaningful as a proof of coupling:

```text
X-ray transport in a C. elegans-sized target
-> local secondary electron spectrum
-> Geant4-DNA water radiolysis chemistry
-> radiochemical G-values and molecular counts
```

The chemistry side uses the Geant4-DNA `chem6` structure, which is intended to
compute radiochemical yields, G, versus time and LET using the IRT method. This
is the correct class of tool for water radiolysis from electron tracks.

The transport side now uses a soft-tissue-like worm material and a simplified
1 mm x 40 um-radius cylindrical worm analogue with coarse proxy regions.

## What is not realistic yet

This model is not yet a full biological C. elegans model. It does not include:

- OpenWorm-derived body shape or cell coordinates;
- true neuron, muscle, pharynx, gonad, intestine, or cuticle geometries;
- oxygen concentration or M9/NGM chemistry;
- ROS scavenging by biomolecules;
- LITE-1 molecular activation;
- calcium or membrane-voltage dynamics;
- biological feedback, repair, or antioxidant response.

So the Stage-1 output should be described as **radiolysis products in water
under a region-specific electron spectrum**, not as directly measured cellular
ROS concentration.

## Are the current G-values plausible?

The latest working run reported final-time species yields around 1 microsecond,
for example:

```text
OH:       ~1.33 molecules / 100 eV
H2O2:     ~0.97 molecules / 100 eV
e_aq-:    ~1.48 molecules / 100 eV
H3O+:     ~2.16 molecules / 100 eV
```

Those values are in the broad range expected from Geant4-DNA water radiolysis
outputs at microsecond-scale chemistry times, especially for low-keV electron
spectra. They should not be treated as final biological ROS concentrations.
They should be treated as an internal Geant4-DNA water-chemistry result that is
suitable for relative comparisons between regions and dose conditions.

## Relation to Dr. Bolding / Cannon et al. C. elegans X-ray work

The Bolding/Cannon paper measured rapid behavioral responses to X-rays in
C. elegans and showed LITE-1 dependence. It reported dose rates around 0.19,
0.38, 0.56, and 0.74 Gy/s for diffuse stimulation, and focused X-ray tests up to
about 1 Gy/s. It did not directly report quantitative OH, H2O2, or hydrated
electron concentrations in the worm.

Therefore, the current simulation cannot yet be compared against a measured ROS
concentration from that paper. The defensible comparison is indirect:

1. match the experimental dose-rate/exposure conditions;
2. compute region-specific dose and radiolysis yields;
3. ask whether the physical radiolysis signal is present and scales with the
   same dose conditions that produced behavioral responses;
4. later connect the radiolysis signal to LITE-1/cell physiology.

## Next validation targets

1. Reproduce the paper's dose-rate conditions: 0.19, 0.38, 0.56, 0.74, and/or
   1.0 Gy/s.
2. Run the same transport spectrum extraction for whole worm, body wall/muscle,
   intestine, and future OpenWorm-informed regions.
3. Convert raw species counts/G-values into per-Gy and per-exposure summaries.
4. Add oxygen/scavenger chemistry using Geant4-DNA scavenger-style examples
   before claiming biological ROS concentration.
5. Replace proxy geometry with OpenWorm-informed region placements.
