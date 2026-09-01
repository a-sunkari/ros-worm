# Final LITE-1 mechanistic boundary

## Decision

The final model stops at **Level 1: chemical target-interaction opportunity**. No primary study supplies a validated mapping from radiogenic radical/H2O2 exposure to LITE-1 open probability, calcium response, or behavior. The repository therefore contains no activation probability or behavioral prediction.

## Demonstrated biology

- Cannon et al. established dose-rate-dependent X-ray behavior requiring LITE-1 and showed that ectopic muscle expression can confer X-ray paralysis/egg-ejection sensitivity. They did not measure neural OH, H2O2, channel current during X-ray exposure, or receptor chemistry ([DOI 10.3389/fnins.2023.1210138](https://doi.org/10.3389/fnins.2023.1210138)).
- Gong et al. demonstrated unusual UVA/UVB absorption by purified LITE-1 and critical roles for W77 and W328 ([DOI 10.1016/j.cell.2016.10.053](https://doi.org/10.1016/j.cell.2016.10.053)). This makes Trp motifs relevant; it does not show oxidative activation.
- Bhatla and Horvitz established LITE-1/GUR-3/PRDX-2 participation in light/H2O2 feeding responses ([DOI 10.1016/j.neuron.2014.12.061](https://doi.org/10.1016/j.neuron.2014.12.061)).
- Zhang et al. found 100–500 µM H2O2 suppressed LITE-1-dependent photocurrents and accelerated deactivation, contradicting a monotone “H2O2 activates LITE-1” model ([DOI 10.1371/journal.pgen.1009257](https://doi.org/10.1371/journal.pgen.1009257)).
- Bair et al. linked ROS-dependent foraging to LITE-1 and C44 ([DOI 10.1016/j.redox.2023.102934](https://doi.org/10.1016/j.redox.2023.102934)). Hanson et al. combined structure prediction, mutagenesis, behavior, and electrophysiology into a Cys/PRDX/coincidence model, but not an X-ray-calibrated gating law ([DOI 10.1016/j.cub.2023.07.008](https://doi.org/10.1016/j.cub.2023.07.008)).

## Quantitative chemical inputs

- OH + free tryptophan: `(1.25±0.30)×10^10 M−1 s−1` ([DOI 10.2307/3573010](https://doi.org/10.2307/3573010)); resolved ring components sum consistently with that diffusion-limited scale ([DOI 10.1016/0146-5724(84)90123-7](https://doi.org/10.1016/0146-5724(84)90123-7)).
- OH + free cysteine: `(5.35±0.82)×10^9 M−1 s−1` ([DOI 10.2307/3579203](https://doi.org/10.2307/3579203)).
- Peroxiredoxin/H2O2 family kinetics: bracket `10^5–10^8 M−1 s−1`, including measured thioredoxin-peroxidase rates near `10^7 M−1 s−1` ([DOI 10.1016/j.freeradbiomed.2006.10.042](https://doi.org/10.1016/j.freeradbiomed.2006.10.042); [DOI 10.1074/jbc.R111.283432](https://doi.org/10.1074/jbc.R111.283432)).

Free-solute rates are motif analogues, not protein-bound LITE-1 site rates. Protein accessibility, target abundance, oxygenation, cellular scavenging, PRDX-2 coupling, and downstream fate are unknown. Hydrated electron and H-radical species are plotted because chem6 produces them; they are not added to the target index without a direct, applicable neutral-protein target rate.

## Allowed and prohibited interpretations

Allowed: prompt radiolysis, homogeneous-water molecule equivalent, Trp-like opportunity, thiol/redox opportunity, LITE-1-relevant radiochemical environment. Prohibited: every encounter modifies LITE-1, more H2O2 monotonically activates it, channel open probability, calcium-response probability, or behavioral probability.

The missing transfer function requires targeted experiment. It is not an unimplemented computational feature.
