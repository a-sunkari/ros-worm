# LITE-1 mechanistic evidence audit

## Scope and decision

This audit asks which molecular link, if any, may defensibly be placed between
water radiolysis and LITE-1-dependent X-ray behavior. It does not assume that
"ROS activates LITE-1." The highest supported quantitative level is **Level 1:
chemical target-interaction availability**. Current primary literature does
not calibrate radiogenic radical or H2O2 exposure to LITE-1 open probability,
cellular calcium response, or behavior. v2.1 therefore does not calculate any
of those quantities.

## A. Experimentally demonstrated

1. **Cannon/Bolding X-ray phenotype.** Cannon et al. observed a dose-rate-
   dependent locomotory response to a 10 s, 50 kV focused X-ray exposure;
   functional LITE-1 was required, whereas GUR-3 was not. Ectopic body-wall-
   muscle expression of LITE-1 enabled X-ray-induced paralysis/egg ejection.
   The paper establishes genetic dependence and tissue sufficiency; it did not
   measure neuron-level radical concentrations, H2O2, LITE-1 current during
   X-ray exposure, or receptor chemistry. DOI: [10.3389/fnins.2023.1210138](https://doi.org/10.3389/fnins.2023.1210138).

2. **LITE-1 is an unusual direct photoreceptor.** Gong et al. found that
   purified LITE-1 absorbs UVA/UVB unusually strongly and that W77 and W328 are
   critical for photoabsorption/function. This supports tryptophan-containing
   motifs as chemically relevant, but it does not show that oxidizing a
   tryptophan activates LITE-1. DOI: [10.1016/j.cell.2016.10.053](https://doi.org/10.1016/j.cell.2016.10.053)
   (erratum [10.1016/j.cell.2016.12.040](https://doi.org/10.1016/j.cell.2016.12.040)).

3. **H2O2 and light responses can require gustatory-receptor pathways.**
   Bhatla and Horvitz found that light and H2O2 inhibit feeding through LITE-1,
   GUR-3, pharyngeal neurons, and—in the I2 response—PRDX-2. This is organismal
   and circuit evidence for redox participation, not a measured LITE-1/H2O2
   binding or gating constant. DOI: [10.1016/j.neuron.2014.12.061](https://doi.org/10.1016/j.neuron.2014.12.061).

4. **H2O2 can suppress rather than activate photosensation.** Zhang et al.
   showed that 100–500 µM exogenous H2O2 suppressed LITE-1-dependent
   photocurrents and accelerated deactivation, whereas antioxidants promoted
   responses/recovery. Thus, a monotone "more H2O2 means more LITE-1" model is
   contradicted by direct electrophysiology. DOI:
   [10.1371/journal.pgen.1009257](https://doi.org/10.1371/journal.pgen.1009257).

5. **LITE-1 participates in ROS-dependent foraging.** Bair et al. found that
   multiple subthreshold ROS sources combine to influence behavior, that
   LITE-1 is required for responses to ROS-generating conditions, and that C44
   contributes. These data support redox sensitivity and a Cys-linked motif,
   but do not supply a radiochemical dose-to-channel calibration. DOI:
   [10.1016/j.redox.2023.102934](https://doi.org/10.1016/j.redox.2023.102934).

## B. Quantitatively constrained

1. **Aqueous OH + tryptophan.** Pulse radiolysis gives
   `k = (1.25 ± 0.30) × 10^10 M^-1 s^-1` for free tryptophan. This is used as
   the solution-phase Trp-like upper-level motif rate, not a protein-bound
   LITE-1 site rate. Armstrong and Swallow, *Radiation Research* 40, 563–579
   (1969), DOI: [10.2307/3573010](https://doi.org/10.2307/3573010). A later
   resolved multisite study reported pyrrole- and benzene-ring components of
   `7.5 × 10^9` and `5.0 × 10^9 M^-1 s^-1`, respectively, consistent with
   diffusion-limited total attack: [10.1016/0146-5724(84)90123-7](https://doi.org/10.1016/0146-5724(84)90123-7).

2. **Aqueous OH + cysteine.** Mezyk measured
   `k = (5.35 ± 0.82) × 10^9 M^-1 s^-1` for OH reaction with cysteine over the
   relevant acid/base forms. This is not a C44-specific protein rate. DOI:
   [10.2307/3579203](https://doi.org/10.2307/3579203).

3. **H2O2 + peroxiredoxin.** Peroxiredoxin family rates span roughly
   `10^5–10^8 M^-1 s^-1`; specific yeast thioredoxin peroxidases were measured
   near `10^7 M^-1 s^-1` at pH 7.4 and 25 °C. This family bracket is used only
   for an encounter-capacity sweep because no C. elegans PRDX-2/LITE-1 complex
   rate or concentration was found. DOIs:
   [10.1016/j.freeradbiomed.2006.10.042](https://doi.org/10.1016/j.freeradbiomed.2006.10.042),
   [10.1074/jbc.R111.283432](https://doi.org/10.1074/jbc.R111.283432).

4. **Geant4-DNA scope.** Geant4-DNA explicitly supports water radiolysis,
   step-by-step and IRT chemistry, and scavenger processes. The v2.1 decision
   not to add targets directly is evidentiary rather than a software limit:
   target abundance, cellular scavenging, oxygenation, and protein-bound rate
   constants are not measured for this system. Official documentation:
   [Geant4 physics processes / DNA chemistry](https://geant4.web.cern.ch/documentation/dev/bfad_html/ForApplicationDevelopers/TrackingAndPhysics/physicsProcess.html).

## C. Mechanistically plausible

- Radiogenic OH can rapidly attack exposed Trp- and thiol-like motifs.
- Radiogenic H2O2 can be consumed by PRDX-2-like relays on longer spur/cellular
  timescales.
- The 2023 structure-function study combines AlphaFold2/MD, mutagenesis,
  behavior, and electrophysiology to propose a tetrameric light-activated
  channel, a putative chromophore pocket, a critical cysteine, and photon/H2O2
  coincidence. The structural and gating sequence remains a model rather than
  a calibrated X-ray/radical transfer function. DOI:
  [10.1016/j.cub.2023.07.008](https://doi.org/10.1016/j.cub.2023.07.008).
- The muscle gain-of-function phenotype is compatible with LITE-1 expression,
  rather than neural-selective X-ray absorption, supplying tissue specificity.

## D. Speculative or unsupported

- Every OH–Trp or OH–thiol collision activates LITE-1.
- H2O2 is exclusively activating; direct data also show inhibitory/resetting
  behavior.
- A water G value equals intracellular ROS concentration.
- LITE-1 expression level or effective reactive-site concentration is known.
- A free-amino-acid rate constant transfers unchanged to a buried membrane-
  protein residue.
- The current literature supports X-ray-specific receptor open probability.
- Cannon et al. measured neural OH/H2O2 or demonstrated radiolysis as the
  causal intermediate.

## Decision gate

Level 2 would require a quantitative LITE-1-dependent radical/H2O2 response
curve measured in a cellular context comparable to the X-ray experiment and a
validated mapping from modeled local chemistry to that exposure. Level 3 would
require a biochemical/channel gating model with calibrated kinetic parameters.
Neither was found. The repository therefore stops at Level 1 and labels every
computed value an **interaction opportunity**, never an activation probability.
