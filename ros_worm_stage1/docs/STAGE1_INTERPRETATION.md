# Stage-1 interpretation notes

Stage 1 is a working physics/chemistry bridge, not the final biological model.

## What is currently physical

The current transport model represents a C. elegans-sized target as a water/soft-tissue-equivalent cylinder in a water-like agar/M9 environment. It scores regional energy deposition and secondary electron steps in proxy regions:

- whole worm,
- head proxy,
- ventral nerve cord proxy,
- body-wall/muscle proxy,
- intestine proxy.

The chemistry model is a Geant4-DNA `chem6`-style water radiolysis model. It takes an electron energy spectrum from the transport model and computes molecular species yields in water. This is the appropriate first chemistry approximation for tissue aqueous phase radiolysis, but it is not yet a full tissue-biochemistry model.

## What the coupled run means

A successful run means:

```text
X-ray transport in a worm-sized target
→ secondary electron spectrum in a selected region
→ Geant4-DNA water radiolysis from that spectrum
→ species yields such as OH, e_aq, H2O2, etc.
```

That is the first useful computational validation target for Dr. Bolding's X-ray/ROS hypothesis: can the experimental radiation field plausibly generate local radiolysis/ROS-relevant species in worm-sized biological regions?

## What it does not mean yet

It does not yet model:

- true OpenWorm anatomical geometry,
- all 302 neurons or 95 muscle cells,
- individual cell morphologies,
- real tissue biochemical scavenging,
- oxygen concentration,
- LITE-1 kinetics,
- downstream electrophysiology,
- mouse brain/skull attenuation.

## Why keep this stage

This stage is the regression test. Any later OpenWorm geometry or biology layer must preserve this basic working chain:

```text
transport output ROOT
→ electron_spectrum.csv
→ chem6-derived chemistry run
→ Species ROOT/TXT outputs
```

Do not modify the Geant4-DNA chemistry lifecycle unless the baseline `chem6` behavior still passes first.
