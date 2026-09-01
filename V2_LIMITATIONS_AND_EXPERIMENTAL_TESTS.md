# V2 limitations and discriminating experiments

## Limitations that bound the claims

1. **Source spectra are bracketed, not measured.** The exact iMOXS filter-wheel
   state, polycapillary energy response, and 20 kV Mini-X spectrum at the sample
   were unavailable. Kramers-plus-lines/XCOM ensembles are physically informed
   uncertainty models, not precision reconstructions.

2. **Absolute fluence is dose-normalized.** Diffuse histories are conditioned on
   crossing the target plane. Focused dosimetry is reported in the source paper
   as approximate within a factor of two. Conditional per-Gy quantities should
   not be reverse-interpreted as tube output.

3. **The neural endpoint is surface proximity.** It is neither absorbed dose in
   neurons nor an inside-neuron classification. Earlier voxel solids failed
   resolution convergence and changed anatomy; v2 intentionally keeps the
   original surface atlas.

4. **The matched null is informative but not exhaustive.** It preserves the
   atlas surface and near-body containment under small rigid transforms. It does
   not span every possible surface-area-matched synthetic topology.

5. **The worm anatomy is static and generic.** Individual posture, dimensions,
   internal composition, and exact atlas registration are not animal-specific.
   Equal longitudinal sectors are coordinate labels, not neuron identities.

6. **Medium geometry is simplified.** NGM and M9 are water-equivalent; salt,
   agar, bacteria, meniscus shape, worm height, glass thickness, and exact
   source distance are incompletely known. Diffuse liquid depth materially
   affects results.

7. **Chemistry is homogeneous liquid water.** The model lacks oxygen variation,
   biomolecular scavengers, antioxidants, membranes, pH heterogeneity,
   diffusion barriers, repair, and metabolism. G values are not intracellular
   ROS concentrations. Exposure-level “molecule equivalents” additionally
   assume full local thermalization of the near-neural electron birth-energy
   budget and are not surviving intracellular molecule counts.

8. **No molecular LITE-1 model exists.** The workflow provides a physical and
   radiochemical input. It does not predict receptor activation, membrane
   current, neuronal firing, paralysis, egg ejection, or avoidance probability.

9. **Navigation warnings remain.** Low-frequency `GeomNav1002` incidents arise
   at priority-baked non-neural daughter boundaries. Destructive mesh repair was
   not justified. The warnings are quantified and no invalid eligible
   coordinates were observed, but zero-warning geometry was not achieved.

10. **Dose-rate biology is not simulated.** Transport and G values are scaled
    linearly with fluence. Radical overlap, oxygen depletion, biological
    saturation, and signaling kinetics over 10–20 s exposures are outside the
    model.

## Highest-value experiments

### 1. Measure spectra and dose at the worm plane

Use a detector appropriate for the low-energy range to measure the iMOXS and
Mini-X spectra after the exact optics, filter state, air path, plate/drop, and
substrate. Record beam footprint versus energy and current. This directly tests
the largest source-model assumption and would replace the soft/nominal/hard
ensemble.

Prediction: the v2 qualitative conclusion should survive spectra within the
current brackets. A spectrum substantially softer than the diffuse bracket
would make liquid depth even more influential.

### 2. Control and report liquid depth

Repeat diffuse behavior at fixed absorbed dose with several calibrated M9
depths, ideally using spacers or a microfluidic chamber. Measure the depth over
the worm rather than drop volume alone.

Prediction: at equal incident fluence, deeper liquid strongly suppresses worm
deposition. At equal measured worm dose, deeper liquid hardens the secondary
spectrum and lowers birth count per Gy while increasing mean electron energy.

### 3. Radical-scavenger test at matched dose

Introduce membrane-permeant and impermeant radical scavengers or antioxidant
conditions while verifying that X-ray attenuation/dose is unchanged. Include
vehicle controls and LITE-1-null animals.

Prediction under a radiolysis-intermediate hypothesis: changing radical
lifetime should change LITE-1-dependent behavior without proportionally
changing absorbed dose. A null effect over a verified effective scavenging
range would weaken the hypothesis.

### 4. Oxygenation and deoxygenation series

Control dissolved oxygen in M9 or microfluidic medium and verify worm viability
and baseline locomotion.

Prediction: oxygen-dependent downstream chemistry may alter response magnitude
or latency even when initial electron production is unchanged. The current
oxygen-free reduced chemistry cannot predict direction quantitatively.

### 5. Neural versus muscle expression with matched irradiation

Compare endogenous neuronal LITE-1 and ectopic muscle LITE-1 across the same
beam, dose, medium depth, and time course. Add expression-level quantification.

Prediction: because neural- and muscle-associated physical fields are similar,
major response differences should track expression/cellular physiology rather
than tissue-specific X-ray transport.

### 6. Beam-position map along the worm

Raster a smaller, well-characterized focused beam along head, midbody, and tail
while measuring rapid avoidance and muscle phenotypes. Register animal posture
and beam coordinates.

Prediction: a physical field map should follow beam placement. Phenotypic maps
that are much sharper or shifted relative to modeled deposition would identify
biological circuit localization beyond transport.

### 7. Sub-second latency measurement

Use high-frame-rate behavior or electrophysiology to resolve onset after X-ray
start and recovery after stop.

Prediction: water-radiolysis species arise by picoseconds to microseconds, so
chemistry does not impose a slow lower bound. Millisecond-to-second latency
would reflect receptor, cellular, and circuit kinetics. A response preceding
the physically delivered pulse would falsify the causal timing chain.

### 8. Direct chemical probe with careful controls

Where feasible, use an X-ray-compatible, calibrated radical or peroxide probe
in the same medium geometry. Separate medium signal from intracellular signal,
test probe radiochemistry, and include dose-matched no-worm controls.

Prediction: a dose-dependent water-radiolysis signal should be detectable, but
its magnitude cannot be inferred from the current G values without spatial
energy deposition, scavenging, and probe-response modeling.
