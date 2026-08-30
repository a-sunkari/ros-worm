# v1 tracked validation package

These small tables and figures are the reviewable extracts from the ignored
large production directories:

- `production_focused_10M_v1`
- `production_diffuse_10M_v1`
- `geometry_qc_highstat_v1`
- `chemistry_focused_near_neural_10k_v1`
- `chemistry_diffuse_near_neural_10k_v1`

The production jobs were executed from the working-tree implementation later
committed as `1625515` (`Make transport and neural scoring reproducible`). Their
original run manifests record the preceding base SHA plus the then-uncommitted
file list, Geant4 11.3.2, fixed seeds 1357911/2468022, literal macro, input
hashes, event count, and thread count.

Regenerate this package only through
`ros_worm_stage1/scripts/build_release_artifacts_v1.py`; do not hand-edit numeric
tables. Absolute result paths are intentionally omitted. Monte Carlo production
ROOT/log files stay under ignored `ros_worm_stage1/results/`.
