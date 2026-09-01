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
