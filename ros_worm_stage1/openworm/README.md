# OpenWorm bridge workspace

This folder is intentionally separate from the current working Stage-1 Geant4 code.

Use it to collect OpenWorm-derived anatomy/connectome/body-model data and convert those data into Geant4-friendly region definitions. The goal is to upgrade the transport model without destabilizing the Geant4-DNA chemistry pipeline.

Recommended first milestone:

```text
OpenWorm-informed region table
→ generated Geant4 ROI definitions
→ region-specific spectra
→ region-specific chemistry runs
```

Do not import a full OpenWorm simulator into Geant4. Instead, extract the geometry/anatomy information needed for radiation transport and scoring.
