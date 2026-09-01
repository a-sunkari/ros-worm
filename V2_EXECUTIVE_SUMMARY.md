# ROS-Worm v2 executive summary

## Bottom line

The completed v2 study supports a bounded physical-plausibility conclusion:
under source and sample conditions approximating Cannon et al., Geant4 predicts
rapid production of low-energy secondary electrons throughout the worm and in
close spatial association with both nervous and body-wall muscle anatomy.
Those spectra produce water-radiolysis products from picoseconds onward in the
preserved Geant4-DNA chemistry model. The physical/radiochemical input scales
monotonically across the behavioral exposure range and remains present across
the tested source, beam, material, and geometry brackets.

The study does **not** show preferential neural targeting. In 10M-history runs,
14.19% (focused) and 14.88% (diffuse) of eligible in-body electron births were
within 5 µm of the nervous surface. Matched perturbations of the identical
atlas gave 14.12% and 14.52%. Enrichment ratios of 1.005 and 1.025 are not
compelling evidence that the real neural geometry receives more proximity than
a geometry-matched internal surface.

## Most informative quantitative results

- Focused nominal + NGM: 65,612 eligible electron births; 9,311 within 5 µm;
  conditional rate 1.150 × 10⁶ near-neural births per whole-worm Gy.
- Diffuse nominal + M9: 16,396 eligible births; 2,440 within 5 µm; conditional
  rate 1.170 × 10⁶/Gy.
- Neural and muscle surface-proximity rates were nearly equal in both sources.
  This is physically consistent with ectopic muscle LITE-1 sensitivity and
  argues that tissue specificity need not arise from special X-ray transport.
- At ~1 µs, focused/diffuse homogeneous-water G values were 1.463/1.485 for
  •OH and 0.889/0.885 for H₂O₂ molecules per 100 eV.
- Matched muscle-proximity chemistry differed by <0.3% from neural-proximity
  chemistry for ~1 µs •OH and H₂O₂, within the 10k chemistry uncertainty.
- Conditional homogeneous-water energy-budget equivalents scale from about
  0.19 to 1.42 billion •OH molecules across the focused exposure set and 0.35
  to 1.36 billion across the diffuse set. These are not intracellular counts
  or concentrations.
- The diffuse M9 layer was the dominant tested environment effect: removing it
  increased conditional near-neural births/Gy by 41% and substantially softened
  the electron spectrum. Focused downstream agar/dish had <1% effect.
- Soft/hard source brackets changed the focused primary endpoint by +5%/−11%
  and diffuse by about ±1.5% in paired 1M tests.
- No eligible 10M record was nonfinite or outside the body. Residual Geant4
  boundary warnings were 22.0/million focused and 4.2/million diffuse and are
  reported rather than concealed.

## Interpretation for Dr. Bolding

Radiolytic chemistry is physically plausible as an intermediate because the
required electron field and water chemistry arise rapidly at the experimental
doses, in both neural and muscle-associated regions. The simulation does not
identify a neural transport hotspot and does not connect any modeled species to
LITE-1 molecular activation. The strongest reading is therefore that X-rays
provide a broadly available physical/radiochemical stimulus, while LITE-1
expression supplies biological sensitivity and tissue specificity.

The most decisive next measurements are an at-sample source spectrum, liquid
depth over each worm, and experiments that alter radical lifetime or scavenging
without changing absorbed dose.

## Where to look

- Full report: `docs/v2/THESIS_REPORT.md`
- Methods: `docs/v2/METHODS.md`
- Results: `docs/v2/RESULTS.md`
- Reproduction: `docs/v2/REPRODUCIBILITY.md`
- Figures/tables: `ros_worm_stage1/validation/v2/`
- Requirement/evidence map: `docs/v2/COMPLETION_MATRIX.md`
- Experimental tests: `V2_LIMITATIONS_AND_EXPERIMENTAL_TESTS.md`
