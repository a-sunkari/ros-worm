# Materials and methods

## Study design and claim boundary

The study tested physical plausibility: whether X-ray conditions associated with LITE-1-dependent behavior can deposit energy in nervous and muscle anatomy and generate prompt water-radiolysis products. It did not fit behavior, intracellular concentration, channel open probability, or receptor activation. The preregistered hierarchy was transport, regional deposited energy, homogeneous-water chemistry, and literature-rate chemical opportunity. Each level was allowed to stop when the next transfer function was not experimentally constrained.

## Anatomy and transport geometry

OpenWorm-derived anatomy was placed using the tracked transport-geometry manifest. The physical Geant4 geometry retained the validated mutually exclusive whole-body residual, digestive, reproductive, and body-wall-muscle compartments. The nonmanifold aggregate nervous surface and excretory anatomy were not inserted as physical daughters. This avoided previously observed resolution-dependent neural volumes and nervous-related navigation instability while preserving the high-resolution anatomy for analysis.

Focused transport represented a bracketed tungsten-target 50 kV source, a Gaussian 0.85 mm FWHM footprint, NGM/agar, polystyrene substrate, and air. Diffuse transport represented a bracketed silver-target 20 kV source, broad illumination at the worm plane, M9, glass, and air. Spectra incorporated bremsstrahlung and characteristic-line structure but were not measured at the specimen plane; soft and hard alternatives were retained as model sensitivities. Transport used Geant4 11.3.2, `G4EmLivermorePhysics`, 100 nm production cuts, tissue-proxy materials, and two recorded random seeds per run.

## Spatial energy-deposition output

Every positive deposition in a worm physical compartment recorded event, region, particle, track, parent, process, deposited energy, pre-step kinetic energy, step length, pre/mid/post coordinates, body containment, and an authoritative position. Charged-particle deposition used the midpoint of a step bounded by an active 0.5 µm maximum through `G4StepLimiterPhysics`. Neutral discrete-interaction deposition used the post-step interaction point. The scorer required finite positive energy and an in-body authoritative coordinate. It aborted if the positive-step energy sum differed from event-level whole-worm deposition.

Nominal focused and diffuse campaigns each used 100,000,000 independent primary histories. Brute-force simulation was selected over variance reduction after pilot event rates predicted that this scale would meet a 10% relative neural-dose error target. No deposition event was duplicated or reweighted.

## Nervous-surface deposited energy

The original 1,355,686-triangle nervous atlas was queried with a VTK static cell locator. Unsigned point-to-triangle distances were binned at 0–1, 1–2, 2–5, 5–10, 10–25, 25–50, and at least 50 µm. Each shell reports total deposited energy, energy/history, fraction of whole-worm energy, energy per modeled whole-worm Gy, contributing events, and event-level uncertainty. This surface-referenced endpoint does not require a neural mass and is not neural absorbed dose.

As a falsification control, 99 rigid translations/rotations of the identical full-resolution atlas were accepted under anatomical containment constraints and scored on deterministic one-million-history prefixes. These controls preserve surface area, triangulation, and morphology. Empirical upper-tail probabilities were `(1 + number of null values at least as large as observed)/(99 + 1)`; the smallest resolvable value is 0.01. They test spatial enrichment relative to nearby anatomy-matched surfaces, not molecular targeting.

## Analysis-only neural volume and dose

The source manifest identified 276 nervous-system objects. Each actual mesh was rechecked after merging duplicate facet vertices and was watertight, consistently wound, and positive-volume. Neural membership was the logical OR of the 276 interiors, so overlaps were counted once. No Boolean repair, smoothing, global hole filling, or physical Geant4 daughter was used.

The union was sampled on body-clipped grids of 0.25, 0.5, 1, and 2 µm pitch. Validation included volume, mass, bounds, outside-body fraction, longitudinal morphology, connectivity, symmetric surface errors, sampled maximum distance, and visual overlays. The primary numerator used exact point membership in the source-object union. The primary mass was the 0.25 µm body-clipped union volume (8,663 µm3) at 1.04 g cm−3, yielding 9.00952×10−12 kg. This density is a proxy, not a measured worm neural density. Neural dose was `sum(Edep inside exact union)/mass`. Voxel-specific ratios defined reconstruction sensitivity.

The physical body-wall-muscle region supplied an analogous dose using its Geant4 scoring mass. Whole-worm mean dose used the sum of mutually exclusive physical scoring masses. Regional results were expressed as regional dose divided by whole-worm mean dose.

## Statistical analysis

Event ID defined the independent sampling unit. For each event, regional and whole-worm energy were aggregated before estimating means. Ratio standard errors used first-order covariance propagation for the paired numerator and denominator. A 2,000-replicate Poisson(1) event-weight bootstrap independently checked standard errors and percentile intervals. History-prefix convergence was evaluated at 1, 2, 5, 10, 20, 50, and 100 million histories; independent 10-million-history runs provided replicate checks. Rare-event diagnostics included raw contributing events, energy-weighted effective event count, largest event share, and nonzero-event skewness.

Monte Carlo statistics, ROI reconstruction, atlas registration, physical-input sensitivity, and experimental dosimetry were reported separately. Registration was bracketed by ±2 µm transverse, ±5 µm longitudinal, and ±3° rotation. The approximate Cannon factor-of-two dosimetry uncertainty was treated as an external 0.5–2 multiplicative interval, not as Gaussian noise. Soft/hard spectrum, environment, water-material, and seed tests used the validated corrected one-million-history sensitivity set; neural-dose variants with fewer than 30 contributors were not used to claim precise source effects.

## Water radiolysis

The validated chem6-derived Geant4-DNA water-chemistry lifecycle was preserved. For neural, muscle, and 0–5 µm perineural regions, electron pre-step kinetic spectra were weighted by the actual energy deposited locally. Six independent 10,000-event chemistry cases (focused/diffuse × three regions) recorded H3O+, OH, OH−, hydrated electron, H radical, H2, H2O2, and O at 1 ps, 10 ps, 100 ps, 1 ns, 10 ns, 100 ns, and approximately 1 µs. Absolute species equivalents used `N_s(t)=Edep_local/(100 eV) × G_s(t)`. They are homogeneous-water molecule equivalents, not intracellular counts or concentrations.

## LITE-1-relevant chemical opportunities

The mechanistic audit used primary studies of LITE-1 photoreception, ROS/H2O2 biology, Cys/PRDX-linked regulation, and pulse radiolysis. OH reaction with free tryptophan used `(1.25±0.30)×10^10 M−1 s−1`; OH with free cysteine used `(5.35±0.82)×10^9 M−1 s−1`. Effective target concentrations from 1 µM to 1 mM and background scavenging from 10^8 to 10^10 s−1 were swept with capture fraction `kC/(kC+k_bg)`. H2O2/PRDX opportunity used a 10^5–10^8 M−1 s−1 family bracket and the modeled molecule-time integral. These are chemical opportunities. Protein-bound accessibility, expression, intracellular scavenging, and a gating transfer function are unknown; activation probability was therefore not computed.

## Reproducibility

Expanded macros, event counts, seeds, software versions, source/environment definitions, input hashes, compact outputs, figures, and release-audit expectations are tracked. Large ROOT files remain ignored, but their SHA-256 hashes and regeneration commands are recorded. The final audit fails on energy mismatch, incorrect history count, missing nulls/chemistry cases, stale figure hashes, or missing manuscript artifacts.
