# ROS-Worm transport app

This is a first-level C. elegans X-ray transport model.  It is intentionally simple:

- worm surrogate: water or soft-tissue cylinder,
- simple ROI proxy volumes: head, VNC, body-wall/muscle, intestine,
- agar/M9 modeled as water-like material,
- focused or diffuse photon source,
- optional Kramers-like X-ray spectrum,
- ROOT output for event dose and per-step electron spectrum extraction.

The purpose is not anatomical fidelity.  The purpose is to generate a defensible stage-1 source term for the Geant4-DNA water-radiolysis chemistry app.
