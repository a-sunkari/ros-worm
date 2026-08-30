# Legacy audit

The repository retains historical material for provenance, but the following
are not authoritative:

- `debug_core_voxel_remesh_plus_nervous_voxel030_manifest.csv`: physical voxel
  nervous candidate rejected for resolution-dependent anatomy/scoring.
- `debug_core_voxel_remesh_NO_PHYSICAL_NERVOUS_manifest.csv`: useful predecessor,
  but its recorded body metadata was stale and caused placement disagreement.
- `highres_nervous_exact_surface_scoring.py`: earlier brute-force scorer whose
  full-resolution high-stat run exceeded ~21 GB memory.
- `NervousSystem_baked_union_decimated_150k.stl`: actual 522,169 faces; retained
  only as a fidelity comparison.
- `transport/`: an older transport implementation using `/worm/*` commands;
  production uses `transport_manifest/` and `/rosworm/*` commands.
- `transport_manifest/macros/diffuse_50kvp.mac`: historical 50-kV comparison,
  not the Cannon diffuse condition.
- `transport_manifest/macros/alignment_test/`: historical alignment diagnostics
  containing absolute paths and the rejected physical-neural manifest.
- `chemistry/chem6_reference/`: lifecycle/reference assets, not a second active
  chemistry implementation.
- `wu_c_elegans_mesh_model/`: literature benchmark, not OpenWorm replacement.

Historical output must not be combined numerically with v1 results. In
particular, the earlier 44/875 within-5-µm result used a neural atlas shifted by
approximately 50.9 µm relative to the physical meshes, and the historic 10M run
included an impossible excretory-boundary secondary coordinate.

No source geometry or historical result was deleted during the v1 work.
