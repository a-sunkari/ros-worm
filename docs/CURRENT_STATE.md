# Current project state — August 2026

> **V2.1 update (August 31, 2026):** v2.1 is the current analysis/reporting
> authority. It preserves v2 transport but adds verified spatial energy-
> deposition output, nervous-surface edep shells, an analysis-only neural dose,
> muscle comparison, deposited-energy-driven chemistry, and a literature-gated
> LITE-1 target-interaction metric. Start with `V2_1_EXECUTIVE_SUMMARY.md` and
> `docs/v2_1/THESIS_REPORT.md`; verify with
> `scripts/v2_1/run_authoritative_v2_1.py --stage audit`.

> **V2 update (August 30, 2026):** the validated v1 architecture remains the
> geometry/chemistry baseline, and a completed thesis-study extension now lives
> under `config/v2`, `scripts/v2`, and `validation/v2`. Start with
> `V2_EXECUTIVE_SUMMARY.md` and `docs/v2/THESIS_REPORT.md`. The v2 production
> cases use vertical −Z irradiation, source uncertainty ensembles, experimental
> medium/substrates, 10M transport, matched neural nulls, muscle comparison,
> and time-resolved chemistry.

## Authoritative workflow

The working implementation is `ros_worm_stage1/`. The authoritative physical
geometry is `config/transport_geometry_v1.csv`; it contains the residual body,
body-wall muscle, digestive system, and reproductive system at 0.1 mm per model
unit. The nervous and excretory anatomies are non-physical scoring atlases listed
in `config/scoring_atlases_v1.csv`.

`scripts/run_reproducible_case.py` is the single transport entry point. It
generates a macro from `config/bolding_cases.yaml`, builds and runs Geant4,
extracts regional output, analyzes warnings, applies the body-validity filter,
scores the full-resolution nervous surface, and records hashes and seeds.

## Why the scoring anatomy is separate

The original nervous STL has 1,355,686 faces, 676,952 vertices, 54
face-connected structures (26 by shared vertices), 5,591 boundary edges, and 12
non-manifold edges. It preserves recognizable anatomy but is not a well-defined
closed material volume. Exact closest-surface scoring with a VTK static locator
works on the full mesh without the earlier 21 GB memory failure.

Watertight voxel candidates were rejected as authoritative neural volumes. The
0.020 and 0.030-model-unit meshes changed volume by a factor of 1.655 and changed
inside-electron classification from 59 to 173 in the same focused 10M dataset.
Their reference-to-candidate p95 surface errors were 21.2 and 33.4 µm. This is
not volumetric convergence at cellular length scales.

The excretory mesh is also omitted physically. Its material was identical to
the residual body, while its body boundary caused the dominant historical
navigation failures and impossible secondary coordinates. It remains available
as a post-processing volume ROI, so anatomy has not been deleted.

## Verified production results

The new focused 50 kV and diffuse 20 kV runs each used 10,000,000 histories.
The focused run recorded 90,514 eligible secondary-electron births; 6,562
(7.250%) were within 5 µm of the neural surface. The diffuse run recorded 62,968;
4,056 (6.441%) were within 5 µm. Neither run had recorded or geometrically
out-of-body electron births.

The focused run had 18 `GeomNav1002` incidents (1.8e-6/history), split among
body/digestive and body/body-wall boundaries. The diffuse run had three
(3e-7/history). These residual 0.1-nm boundary pushes are reported, not hidden;
they produced no out-of-body secondary records in the new runs.

The 10k-event near-neural chemistry cases use the transport-derived electron
birth spectra and the preserved chem6-derived Geant4-DNA water lifecycle.
Results are G values at 1 µs in liquid water. They are not intracellular
concentrations or measured biological ROS.

Tracked summaries are under `ros_worm_stage1/validation/v1/`, with figures under
`ros_worm_stage1/docs/figures/`. Large ROOT files remain ignored under
`ros_worm_stage1/results/`.

## Corrected historical issues

- Files named `*_1e6.mac` actually requested 10M histories; they now request 1M,
  with explicit `*_10m.mac` files added.
- The former chemistry `ros_spectrum_10k.in` requested 25k events; it now requests
  10k and records fixed random seeds.
- The prior manifest bounds were stale and shifted physical placement by about
  50.9 µm relative to the scorer. The new manifest contains actual STL bounds and
  both transport and atlas scoring use the same zero-centered placement.
- The historic extreme +50.7-mm secondary was traced to an impossible 50.5-mm
  step assigned at an excretory/body navigation failure, not legitimate escape.
- Secondary output now distinguishes particle type and body membership;
  proximity statistics use finite PDG-11 births inside the body only.
- The Cannon diffuse Mini-X condition is 20 kV with a silver target, not 50 kV.

## Remaining limitations

The source spectra are generic Kramers endpoint distributions, not measured
target/filtration spectra. The physical body is a stable ellipsoidal envelope,
not a cellular material map. The simulation lacks agar/M9/container detail.
Neural results are proximity statistics, and chemistry is an uncoupled homogeneous
water calculation driven by electron birth energy. These restrictions prevent a
claim of neuron-level absorbed dose or a mechanistic prediction of LITE-1 activation.

The paragraph above describes the v1 boundary and is superseded for current
analysis by v2/v2.1. V2 adds source/environment reconstruction; v2.1 uses actual
deposited energy and supports a mean dose to an explicit analysis-only neural
ROI. It still does not support individual-neuron dose, intracellular ROS, or a
mechanistic LITE-1 activation prediction. Residual navigation incidents and the
factor-of-two experimental dosimetry interval remain disclosed.
