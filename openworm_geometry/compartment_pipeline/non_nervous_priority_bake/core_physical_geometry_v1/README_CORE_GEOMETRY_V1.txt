Core physical geometry v1.

Physical Geant4 volumes:
- WholeBodyEnvelope parent
- ExcretorySystem_resolved child
- ReproductiveSystem_resolved child
- DigestiveSystem_resolved child
- BodyWallMuscle_resolved child

Excluded from physical daughter geometry for now:
- HypodermisSeam
- NervousSystem

Validation summary:
- Resolved child STLs are watertight.
- Resolved child STLs have bad_edges=0 in Trimesh edge-count audit.
- Geant4 loads flat-mode geometry with no GeomSolids1001/1002 defects.
- Strict CheckOverlaps at low tolerance still reports sliver/contact artifacts.
- Pairwise boolean intersection volumes are near-zero slivers, not large bulk intersections.
- Geant4 navigator probe passed 100k and 1M random samples:
  nullLocated=0, movedNull=0, badSafety=0, exceptions=0.

Use this as the first core transport geometry candidate.
Hypodermis and nervous system should be reintroduced first as scoring/ROI overlays, not physical daughter volumes.
