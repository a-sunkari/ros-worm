# Supplementary methods

## Event-level ratio estimator

For independent history `i`, let `X_i` be regional energy and `Y_i` whole-worm energy. With regional and whole masses `m_X` and `m_Y`, the reported ratio is `(mean X/m_X)/(mean Y/m_Y)`. Its variance uses the first-order delta expansion including `Cov(X,Y)` because regional energy is a component of whole-worm energy. Ignoring covariance slightly overestimates the final standard errors but was not used. Poisson(1) weights resampled whole events, retaining within-event steps and numerator/denominator pairing.

## Effective contributing-event diagnostics

Raw contributing events count histories with positive regional energy. Energy-weighted effective count is `(sum X_i)^2/sum(X_i^2)`. The largest-event share and nonzero-event skewness diagnose dominance by rare histories. Prefixes use original event order and are diagnostic rather than independent replicates; the earlier 10-million-history files use independent seeds and supply the replicate test.

## Neural geometry algorithm

Facet-duplicate vertices are merged before watertightness and winding checks. For voxel union, grid points are classified inside each closed member and accumulated by logical OR in spatial chunks. Whole-body containment clips centers before volume calculation. Exact numerator membership evaluates deposition points in member interiors and also uses logical OR. Thus overlaps are neither physically added nor counted multiple times. Density conversion is `V(µm3)×10−18 m3/µm3×1040 kg/m3`.

## Outlier localization

One hundred thousand original-surface samples were compared with the nearest 0.25 µm ROI boundary center; a reciprocal sample of ROI boundary centers was queried against original triangles. Large reference-to-ROI values were localized by longitudinal coordinate. Exact-only and voxel-only deposited-energy sets quantify scientific effect directly. The analysis avoids using a maximum distance alone to characterize a thin, highly branched atlas.

## Containment and navigation handling

The authoritative position filter excludes nonfinite, nonpositive, or outside-body coordinates before regional scoring. Exclusion counts and energy are reported. No escaped secondary coordinate can enter neural proximity or dose. `GeomNav1002` warning text is parsed into boundary-pair counts. Warnings are retained when geometry changes would compromise anatomy and all energy/localization gates pass.

## Chemistry normalization and target sweep

Electron energy spectra are weighted by electron-deposited energy in each local region. Chemistry G values are multiplied by all-particle local deposited energy; this explicitly separates spectral selection from energy normalization. The target sweep treats free-solute rate constants as motif analogues. The capture fraction omits site accessibility and downstream fate and is therefore an upper-level opportunity estimator. H/eaq species are reported in the water chemistry but excluded from the LITE-1 target metric because no sufficiently direct protein-relevant neutral-target rate was identified for this application.

## Linear exposure reuse

Within the modeled low-fluence regime, independent photon transport and homogeneous-water yield budgets scale with fluence. Cannon conditions sharing source/environment therefore reuse nominal transport and scale by reported Gy. Dose-rate-dependent biological kinetics are not represented; no independent transport run is warranted solely because Gy s−1 changes.
