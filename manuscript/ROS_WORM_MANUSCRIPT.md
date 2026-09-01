# Anatomy-resolved X-ray energy deposition and radiochemical opportunity in *Caenorhabditis elegans* under LITE-1-dependent behavioral exposure conditions

## Abstract

X-rays evoke LITE-1-dependent behavior in *Caenorhabditis elegans*, but the physical and radiochemical inputs available to LITE-1-expressing tissues have not been quantified. We combined experimentally informed Geant4 transport, OpenWorm anatomy, and Geant4-DNA water radiolysis to test whether the Cannon/Bolding exposures can produce a rapid radiochemical environment in nervous and muscle tissue. Stable non-neural compartments were transported physically; the nervous system was scored independently as the exact set union of 276 verified closed source objects and against the original high-resolution nervous surface. Two 100-million-history nominal runs saved spatial energy-deposition steps with a 0.5 µm charged-particle step limit and exact step/event energy conservation. Neural-to-whole-worm mean-dose ratios were 0.932 (95% Monte Carlo confidence interval 0.865–0.998) for focused 50 kV tungsten irradiation in NGM and 0.873 (0.752–0.994) for diffuse 20 kV silver irradiation in M9. Body-wall-muscle ratios were 1.060 (1.042–1.078) and 1.083 (1.047–1.120), respectively. Approximately 14.2–14.4% of whole-worm deposited energy occurred within 5 µm of the nervous surface, but 99 anatomy-matched rigid-atlas controls did not establish preferential neural targeting. Deposited-energy-weighted water chemistry produced OH, H2O2, hydrated-electron, H-radical, and H3O+ yields from picoseconds to one microsecond. Published solution kinetics imply a broad range of Trp- and thiol-target interaction opportunities, not receptor activation probabilities. These results support a rapid, broadly available radiophysical and radiochemical stimulus under the behavioral exposure conditions. They do not establish that radiolysis gates LITE-1; instead, the comparable neural and muscle exposures are consistent with genetic LITE-1 expression supplying tissue specificity.

**Keywords:** *Caenorhabditis elegans*; Geant4; Geant4-DNA; X-ray neuromodulation; LITE-1; water radiolysis

# Introduction

Ionizing radiation can perturb excitable biology at exposures far below those used for tissue ablation, but the chain from photon transport to a genetically specified response is usually uncertain. Cannon et al. reported that focused and diffuse X-rays evoke behavioral responses in *Caenorhabditis elegans* that require the unusual photoreceptor LITE-1. Focused 50 kV irradiation produced avoidance, whereas broader 20 kV irradiation elicited dose-rate-dependent responses; ectopic expression of LITE-1 in body-wall muscle conferred X-ray sensitivity. Those observations identify a genetic sensitivity element but do not identify the physical or chemical intermediary between X-ray absorption and receptor-dependent physiology.

Water radiolysis is a plausible intermediate because low-energy secondary electrons rapidly produce hydroxyl radical, hydrated electron, hydrogen radical, molecular hydrogen, hydrogen peroxide, and related species. Plausibility is not causality. A relevant model must first establish where energy is actually deposited under the experimental irradiation geometry, then distinguish aqueous reference yields from intracellular chemistry, and finally stop before receptor activation unless a quantitative transfer function exists.

LITE-1 biology motivates specific but contradictory chemical questions. Purified LITE-1 absorbs ultraviolet light unusually strongly, and critical tryptophans are required for photoreception. LITE-1/GUR-3 and peroxiredoxin pathways participate in light- and H2O2-related behaviors, while Cys-linked redox findings support chemical sensitivity. Conversely, exogenous H2O2 can inhibit LITE-1 photocurrents and accelerate deactivation. Therefore “ROS activates LITE-1” is not an adequate mechanistic model. Published radical reaction rates can constrain whether radiogenic species have opportunities to interact with Trp- or thiol-like motifs, but not whether any such encounter opens the channel.

Anatomical scoring is also nontrivial. The visually detailed OpenWorm nervous atlas is composed of overlapping/intersecting neural pieces and its aggregate surface is not a trustworthy closed physical volume. Inserting voxel-repaired nervous meshes into Geant4 previously changed anatomy, produced resolution-dependent inside classifications, and caused neural navigation warnings. A stable architecture instead transports through non-overlapping non-neural physical compartments and treats the original nervous surface as a post-processing atlas. That architecture previously quantified secondary-electron births near nervous anatomy, but birth proximity is not absorbed dose and summed birth kinetic energy is not local deposition.

Here we close those dosimetric gaps using spatial Geant4 energy-deposition steps, a separately validated analysis-only neural union, and body-wall-muscle scoring. Direct 100-million-history simulations target rare neural deposition. Event-level covariance, bootstraps, reconstruction and registration ranges, anatomy-matched surface nulls, and source/environment sensitivities separate statistical from model uncertainty. Local deposited energy drives Geant4-DNA water chemistry, followed by a literature-rate target-opportunity analysis. We ask whether nervous and muscle tissues receive sufficient and prompt radiophysical/radiochemical input under Cannon/Bolding conditions, whether neurons are preferentially targeted, and what mechanistic claim survives explicit falsification.

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

# Results

## High-statistics transport and scoring integrity

The focused and diffuse nominal campaigns each completed 100,000,000 histories. Focused transport produced 19,357,815 positive deposition steps and 3,676,126.968 keV of whole-worm deposited energy; diffuse transport produced 5,205,227 steps and 960,616.414 keV. Saved-step and event totals agreed exactly. Twenty focused steps (6.979 keV; 1.90×10−6 of whole deposition) and 19 diffuse steps (19.541 keV; 2.03×10−5) had authoritative coordinates marginally outside the body and were excluded by the prespecified containment rule. Their negligible energy fraction cannot alter reported regional ratios.

Nonfatal `GeomNav1002` boundary-push incidents occurred 2,264 times focused (2.26×10−5/history) and 435 times diffuse (4.35×10−6/history), chiefly at whole-body/digestive and whole-body/muscle boundaries. Energy conservation and step localization passed. Further geometric erosion would have changed anatomy to eliminate rare boundary diagnostics and was not justified.

## Neural ROI remained stable for mean-dose inference

All 276 selected source objects were nervous-category entries and passed actual-content watertightness, winding, and positive-interior checks. Body-clipped volume varied by 3.94% across 0.25–2 µm pitch. At 0.25 µm, p50, p95, and p99 symmetric surface errors were 0.119, 0.246, and 0.522 µm. Large reference-to-ROI deviations were localized: only 0.257% of 100,000 reference samples exceeded 10 µm and 0.031% exceeded 25 µm, almost entirely at posterior terminal processes. ROI-to-reference maximum deviation was below 0.25 µm.

Exact and 0.25 µm membership exchanged local deposits around thin-process boundaries, but their net numerator difference was only −0.315% focused and −1.509% diffuse. Thus the approximately 31–34 µm localized reference outliers do not materially drive the mean-dose endpoint, although they preclude named-neurite dosimetry.

## Neural and muscle doses were whole-worm order

Focused exact-union neural deposition was 4,254.307 keV from 1,264 independent contributing events. The neural-to-whole-worm dose ratio was 0.9316±0.0339 (Monte Carlo standard error), with covariance-aware 95% interval 0.8651–0.9980 and bootstrap interval 0.8636–0.9993. The energy-weighted effective event count was 753; the largest event contributed 0.43% of neural energy.

Diffuse exact-union neural deposition was 1,041.848 keV from 318 events. The ratio was 0.8730±0.0616, with covariance-aware 95% interval 0.7522–0.9938 and bootstrap interval 0.7594–1.0013. The effective event count was 200 and the largest event contributed 1.01%. Relative standard errors were therefore 3.6% focused and 7.1% diffuse, meeting the prespecified 10% target.

Body-wall-muscle ratios were 1.0600±0.0093 focused and 1.0834±0.0185 diffuse. Their 95% intervals were 1.0417–1.0783 and 1.0473–1.1196. The 10-million- and 100-million-history estimates were mutually consistent for all four endpoints (absolute independent-replicate z≤1.44). The data do not support neural-selective X-ray absorption; muscle received comparable or slightly higher dose.

Voxel-pitch neural ratios were 0.9286, 0.9296, 0.9551, and 0.9870 focused and 0.8599, 0.8700, 0.8428, and 0.9194 diffuse from 0.25 to 2 µm. Registration changed the 0.25 µm numerator by −0.9% to +6.6% focused and 0% to +15.9% diffuse over the stated bracket. These deterministic ranges remained separate from statistical confidence intervals.

## Surface-referenced deposition was substantial but not preferential

Focused shell fractions were 1.386%, 2.444%, 10.400%, 16.999%, 28.400%, 23.891%, and 16.480% from the nearest to farthest nervous-surface bins. Diffuse fractions were 1.328%, 2.508%, 10.551%, 16.544%, 28.353%, 23.512%, and 17.205%. Consequently, 14.230% focused and 14.388% diffuse occurred within 5 µm. The equivalent energy was 6.441×10^6 and 6.477×10^6 keV per modeled whole-worm Gy.

Within 5 µm of the muscle surface, fractions were 14.298% focused and 14.350% diffuse. The near-identical nervous- and muscle-surface fractions show broad exposure of internal anatomical interfaces. On deterministic one-million-history prefixes, the real nervous atlas was compared with 99 identical-surface rigid controls. The diffuse real/null-mean ratio was 1.060 with empirical upper-tail p=0.08. The focused control result is reported in the release table and did not support a claim of preferential neural targeting. Surface proximity is therefore retained as a robust spatial descriptor, not an enrichment claim.

## Experimental exposures map linearly to regional dose

Conditioning reported whole-worm Gy on the transport model, focused 0.2–1 Gy s−1 for 10 s corresponded to 1.86–9.32 neural Gy and 2.12–10.60 muscle Gy. Focused 1 Gy s−1 for 15 s corresponded to 13.97 neural Gy and 15.90 muscle Gy. Diffuse 0.19, 0.38, 0.56, and 0.74 Gy s−1 for 20 s corresponded to 3.32, 6.63, 9.78, and 12.92 neural Gy and 4.12, 8.23, 12.13, and 16.03 muscle Gy. These values inherit a separate 0.5–2 experimental dosimetry multiplier.

## Deposited-energy-weighted radiolysis was prompt

All six 10,000-event chemistry cases completed with recorded seeds. At 1 ps, focused neural G(OH) was 5.026 molecules/100 eV. By approximately 1 µs, focused neural G(OH) and G(H2O2) were about 1.38 and 0.92; muscle values were similar. Diffuse neural and muscle G values were likewise similar, reflecting modest spectral rather than tissue-identity differences. OH, hydrated electron, H radical, and H3O+ appeared on picosecond timescales; H2O2 accumulated during spur evolution. Chemistry is therefore early relative to second-scale behavior, but temporal precedence alone does not establish causality.

At the 2 Gy focused avoidance condition, neural deposited energy yielded 1.44×10^6 OH and 9.65×10^5 H2O2 homogeneous-water molecule equivalents at approximately 1 µs. At 10 Gy, these scaled to 7.19×10^6 and 4.82×10^6. For diffuse 3.8–14.8 Gy, neural equivalents spanned 2.53×10^6–9.87×10^6 OH and 1.72×10^6–6.71×10^6 H2O2. Muscle totals were larger primarily because the muscle scoring mass was much larger; dose and G value, rather than total molecule count, are the appropriate tissue comparison.

## LITE-1-relevant target metrics remained a wide opportunity bracket

Using literature solution rates and the full target/scavenging sweep, the 2 Gy focused neural condition generated approximately 6.6 to 5.85×10^5 Trp-like interaction opportunities and 2.8 to 2.67×10^5 thiol-like opportunities. These ranges scale linearly with deposited energy but span orders of magnitude because target abundance and background scavenging are unknown. Hydrated-electron and H-radical G values were reported, but no protein-relevant neutral-target rate of sufficient directness was used to manufacture an additional LITE-1 metric. The highest supported mechanistic result remained Level 1 chemical opportunity.

# Discussion

## A broadly available radiophysical stimulus is sufficient for the genetic result

The central result is not neural enhancement. Neural tissue, body-wall muscle, and the whole worm receive doses of the same order under both experimental configurations. This negative selectivity result is biologically informative because Cannon et al. showed that ectopic LITE-1 expression in muscle confers X-ray sensitivity. A model in which X-ray transport specifically concentrates energy in neurons would be difficult to reconcile with that sufficiency experiment. In contrast, broadly available deposition and radiochemistry allow LITE-1 expression to determine which tissue responds.

The original secondary-electron birth-proximity result is no longer the primary endpoint. Actual saved energy-deposition steps now support both an analysis-only neural mean dose and mass-independent surface shells. The 100-million-history campaign resolves the former rare-event limitation: the diffuse neural numerator increased from approximately 30 to 318 independent contributors, and its relative Monte Carlo error fell to 7.1%. Event bootstraps, prefix convergence, and independent-run comparisons did not reveal a rare-event instability hidden by the normal approximation.

## What the neural dose means

“Neural absorbed dose” here means mean deposited energy in the exact set union of 276 closed OpenWorm nervous source objects divided by the body-clipped 0.25 µm union mass at an explicit proxy density. It is not single-neuron dose, membrane dose, or histologically measured tissue dose. The source-object union is scientifically preferable to destructive repair of the aggregate nervous STL: it preserves verified source interiors, counts overlaps once, leaves transport unchanged, and supports resolution tests. Volume convergence and the small net exact-versus-voxel dose difference justify same-order mean-dose inference. Fragmentation and localized terminal-process mismatch do not justify neurite-scale inference.

Atlas registration and morphology remain anatomical uncertainties rather than Monte Carlo errors. Focused registration sensitivity narrowed in the high-statistics data; diffuse sensitivity remains larger, consistent with a sparse neural numerator and different spatial sampling. Neither was collapsed into a single Gaussian error bar. An animal-specific fluorescent nervous atlas co-registered to irradiation posture would replace the assumed bracket, whereas more simulation cannot.

## Surface proximity does not imply targeting

Approximately 14% of deposited energy lies within 5 µm of the nervous surface. The same fraction lies near the muscle surface, and geometry-matched nervous-atlas controls do not establish strong enrichment. This directly falsifies an attractive but unsupported interpretation of the earlier proximity statistic. The result is not a failure of radiolytic plausibility: a tissue can be chemically exposed without being preferentially irradiated. The matched-null analysis distinguishes physical availability from anatomical targeting and should prevent the 14% statistic from being overread.

## Radiochemistry and its boundary

Actual local deposited energy, rather than summed secondary-birth kinetic energy, sets the molecule-equivalent budget. Local edep-weighted electron spectra adjust G values modestly, while regional energy itself controls the larger normalization change. The modeled ps–µs appearance of reactive species is temporally compatible with preceding behavioral responses. However, homogeneous liquid water omits oxygen variation, biomolecular scavengers, membranes, repair, diffusion across cells, and continued enzymatic signaling. The outputs are reference molecule equivalents and G values, not surviving intracellular ROS.

LITE-1 biology is not reducible to “ROS activates LITE-1.” Purified LITE-1 absorbs UV and requires critical tryptophans; LITE-1/GUR-3/PRDX pathways participate in light and H2O2 responses; Cys-linked redox findings support chemical sensitivity; yet exogenous H2O2 can also inhibit photocurrents and accelerate deactivation. Free tryptophan and cysteine react rapidly with OH, but a solution-phase encounter does not establish site modification or channel gating. The target/scavenging sweep therefore reports chemical opportunity only. The absence of a gating transfer function is an experimental knowledge gap, not a computational parameter to invent.

## Source, environment, and dosimetry limitations

The source models incorporate target material, endpoint voltage, characteristic lines, filtration brackets, beam footprint, and sample environment, but neither at-sample spectrum was measured for this study. Sensitivity tests show the core same-order exposure conclusion survives soft/hard alternatives. The diffuse M9/glass environment materially changes spatial deposition relative to a worm-only model and was retained. Cannon's approximate factor-of-two dosimetry uncertainty dominates absolute regional Gy and molecule-equivalent budgets; it does not alter the regional-to-whole ratios. Specimen-plane spectroscopy and dosimetry would improve inference more than another nominal Monte Carlo decade.

Low-frequency navigation warnings remain at physical compartment boundaries. They are nonfatal pushes rather than energy-loss failures: saved-step energy equals event energy exactly, the charged step limiter is active, and invalid coordinates are rejected. Removing the warnings by eroding or Boolean-repairing anatomy would trade a measured low-frequency numerical diagnostic for an unmeasured anatomical bias. The final model records the warning frequency and boundary pairs instead.

## Falsification outcome and experimental predictions

The strongest neural-targeting version of the hypothesis was not supported. Neither dose nor surface enrichment identifies neurons as a privileged radiation absorber. The narrower, defensible hypothesis survives: Cannon/Bolding exposures create rapid energy deposition and water-radiolysis opportunity throughout irradiated tissue, while LITE-1 expression can supply biological specificity.

The most discriminating experiments are therefore not additional generic dose–response measurements. First, measure specimen-plane spectra and dose in the exact NGM and M9 geometries. Second, compare LITE-1-dependent neural and ectopic-muscle responses under hydroxyl scavengers, catalase, PRDX-2 manipulation, C44 mutation, and critical-Trp substitutions while holding dose fixed. Third, record rapid redox/calcium/current signals during X-ray exposure with wild type, `lite-1`, and tissue-specific rescue. A hydroxyl-scavenger effect that preserves absorbed dose but suppresses LITE-1-dependent response would support the chemical bridge; unchanged response across well-controlled scavenging would disfavor it.

## Conclusion

Anatomy-resolved Monte Carlo transport predicts that nervous and muscle tissues receive absorbed doses of the same order as whole-worm mean dose under X-ray exposures associated with LITE-1-dependent behavior. Actual local deposited energy produces prompt homogeneous-water radiolysis and a wide, literature-rate range of possible interactions with Trp- and thiol/redox motifs. Transport does not preferentially target neurons, and no such targeting is required by the ectopic-muscle result. The computation supports a broadly available radiophysical/radiochemical stimulus as plausible; it does not establish molecular gating or behavioral causality.

# Figure captions

**Figure 1. Experimental configurations, computation, and mechanistic boundary.** Focused 50 kV tungsten irradiation in NGM and diffuse 20 kV silver irradiation in M9 feed the validated Geant4 transport model. Actual deposited-energy steps are analyzed against neural/muscle anatomy and passed to homogeneous-water chemistry. Solid links are experiment-defined or model-supported; dashed links denote chemical opportunity or an unmodeled transfer. LITE-1 gating and behavior are not predicted.

**Figure 2. Analysis-only neural ROI convergence and localized surface outliers.** Body-clipped union volume, symmetric surface error, and reference-surface samples beyond stated thresholds for 0.25–2 µm pitch reconstructions. The 0.25 µm ROI supports the primary mass. Large deviations are rare and localized to thin terminal structures; they preclude named-neurite dosimetry but contribute less than 1.6% net change to nominal neural energy.

**Figure 3. Neural and body-wall-muscle dose from 100-million-history transport.** Regional-to-whole-worm dose ratios for focused nominal + NGM and diffuse nominal + M9. Bars show event-level estimates with 95% covariance-aware Monte Carlo intervals. Thick black marks show the deterministic neural ROI-pitch range. Unlike uncertainty sources are not combined.

**Figure 4. Actual deposited energy near nervous and muscle surfaces.** Left: whole-worm deposited-energy fractions by unsigned distance shell to the original nervous atlas and physical muscle surface. Right: observed nervous 0–5 µm fraction versus 99 full-surface, anatomy-contained rigid controls on fixed one-million-history prefixes. Stars are the original atlas; boxes summarize controls. Empirical probabilities test enrichment, not exposure.

**Figure 5. Focused and diffuse longitudinal deposited-energy distributions.** Whole-body, nervous-surface-near, and muscle-surface-near deposited energy in 20 µm longitudinal bins, expressed as fraction of total whole-worm energy. Curves distinguish focused spatial localization from broad diffuse illumination.

**Figure 6. Cannon conditions translated to neural and muscle dose.** Reported whole-worm exposures are scaled by nominal regional-to-whole dose ratios. Lines are fluence-linear transport reuse, not independent simulations or biological response fits. Absolute values retain a separate experimental 0.5–2 dosimetry interval.

**Figure 7. Time-resolved homogeneous-water radiolysis from local deposited energy.** G values for OH, H2O2, hydrated electron, H radical, and H3O+ from 1 ps to approximately 1 µs using neural local-edep-weighted electron spectra. Curves are reference water chemistry, not intracellular concentration or survival.

**Figure 8. LITE-1-relevant Level-1 chemical interaction opportunities.** Neural Trp-like and thiol-like opportunity ranges across Cannon exposures. Ranges propagate assumed 1 µM–1 mM effective target concentrations and 10^8–10^10 s−1 background scavenging with published free-solute OH rate constants. Geometric symbols show geometric range midpoints only. Values are neither modification counts nor activation probabilities.

**Figure 9. Neural-dose uncertainty sources kept separate.** Relative Monte Carlo 95% sampling interval, ROI-pitch range, and registration bracket for focused and diffuse neural-to-whole dose. Experimental factor-of-two dosimetry is excluded because it scales absolute regional Gy, not the transport ratio. Bars are not probability-identical and are not quadrature-combined.

# References

1. Cannon KE et al. LITE-1 mediates behavioral responses to X-rays in *Caenorhabditis elegans*. *Front Neurosci.* 2023;17:1210138. [doi:10.3389/fnins.2023.1210138](https://doi.org/10.3389/fnins.2023.1210138).
2. Gong J et al. The C. elegans taste receptor homolog LITE-1 is a photoreceptor. *Cell.* 2016;167:1252–1263.e10. [doi:10.1016/j.cell.2016.10.053](https://doi.org/10.1016/j.cell.2016.10.053).
3. Bhatla N, Horvitz HR. Light and hydrogen peroxide inhibit C. elegans feeding through gustatory receptor orthologs and pharyngeal neurons. *Neuron.* 2015;85:804–818. [doi:10.1016/j.neuron.2014.12.061](https://doi.org/10.1016/j.neuron.2014.12.061).
4. Zhang W et al. Antioxidants and the LITE-1 photoreceptor control C. elegans photosensation. *PLoS Genet.* 2020. [doi:10.1371/journal.pgen.1009257](https://doi.org/10.1371/journal.pgen.1009257).
5. Bair CL et al. LITE-1-dependent ROS foraging and Cys44-linked redox sensitivity. *Redox Biol.* 2023. [doi:10.1016/j.redox.2023.102934](https://doi.org/10.1016/j.redox.2023.102934).
6. Hanson et al. Structure-function analysis of LITE-1 channel and redox coincidence. *Curr Biol.* 2023. [doi:10.1016/j.cub.2023.07.008](https://doi.org/10.1016/j.cub.2023.07.008).
7. Armstrong RC, Swallow AJ. Pulse-radiolysis study of hydroxyl-radical reactions with tryptophan. *Radiat Res.* 1969;40:563–579. [doi:10.2307/3573010](https://doi.org/10.2307/3573010).
8. OH attack at resolved tryptophan ring sites. *Radiat Phys Chem.* 1984. [doi:10.1016/0146-5724(84)90123-7](https://doi.org/10.1016/0146-5724(84)90123-7).
9. Mezyk SP. Rate constant for hydroxyl-radical reaction with cysteine. *Radiat Res.* 1996. [doi:10.2307/3579203](https://doi.org/10.2307/3579203).
10. Peroxiredoxin hydrogen-peroxide kinetics. *Free Radic Biol Med.* [doi:10.1016/j.freeradbiomed.2006.10.042](https://doi.org/10.1016/j.freeradbiomed.2006.10.042).
11. Hall A et al. Peroxiredoxin catalytic kinetics and redox signaling. *J Biol Chem.* 2011. [doi:10.1074/jbc.R111.283432](https://doi.org/10.1074/jbc.R111.283432).
12. Geant4 Collaboration. Geant4 Book for Application Developers: physics processes and Geant4-DNA chemistry. [Official documentation](https://geant4.web.cern.ch/documentation/dev/bfad_html/ForApplicationDevelopers/TrackingAndPhysics/physicsProcess.html).
