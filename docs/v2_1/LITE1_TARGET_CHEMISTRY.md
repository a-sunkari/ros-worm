# LITE-1-relevant target chemistry

## Implemented endpoint

v2.1 implements a **LITE-1-relevant redox interaction-opportunity sweep**. It
answers: given the modeled homogeneous-water radical yield and an assumed
effective concentration of a Trp- or thiol-like target, what fraction of those
radicals could be captured by that target before generic cellular scavenging?
It does not answer whether the modified residue belongs to LITE-1, whether the
modification has the correct stereochemistry, or whether a channel opens.

The authoritative configuration is
`ros_worm_stage1/config/v2_1/lite1_target_chemistry.yaml`. It records values,
uncertainties, DOIs, and the evidence-level decision.

## Energy normalization

For region `r`, experimental condition `c`, species `s`, and chemistry time
`t`, the molecule-equivalent budget is

`N(r,c,s,t) = Edep(r,c) / (100 eV) × G(r,s,t)`.

`Edep(r,c)` is actual Geant4 deposited energy scored in the analysis-only
neural ROI, physical body-wall muscle, or nervous-surface distance shell. The
primary `G` is calculated using a Geant4-DNA source spectrum weighted by local
electron deposited energy in pre-step kinetic-energy bins. This replaces v2's
birth-kinetic-energy budget as the primary normalization.

The old birth-count spectrum is retained as a sensitivity comparison. At 1 ps
the initial OH G value changes by less than approximately 0.1% for the focused
neural spectrum; at 1 µs the main OH/H2O2 differences are several percent.
This establishes that local edep normalization, not the spectrum substitution,
drives the large change in exposure-level molecule budgets.

## Radical competition model

For a target reaction with second-order rate `k`, effective target
concentration `C`, and all other radical removal represented by a first-order
rate `k_bg`, the target capture fraction is

`f_target = k C / (k C + k_bg)`.

The interaction opportunity is `N_radical(1 ps) × f_target`. v2.1 sweeps:

- effective target concentration: 1 µM, 10 µM, 100 µM, 1 mM;
- background scavenging: `10^8`, `10^9`, `10^10 s^-1`;
- OH + free Trp: `(1.25 ± 0.30) × 10^10 M^-1 s^-1`;
- OH + free cysteine: `(5.35 ± 0.82) × 10^9 M^-1 s^-1`.

The sweep deliberately spans several orders of magnitude because neither
effective LITE-1 target concentration nor the local cellular scavenging rate is
measured. Its lower and upper values are uncertainty bounds under stated
assumptions, not a confidence interval.

## H2O2/PRDX-like metric

The code integrates the no-sink H2O2 molecule-equivalent curve from 1 ps to
approximately 1 µs and multiplies the molecule-time integral by `k C` for a
PRDX-like target. The rate is bracketed from `10^5` to `10^8 M^-1 s^-1`, with
`10^7 M^-1 s^-1` retained as a family-representative diagnostic. This output is
an encounter capacity over spur time. It excludes biological clearance,
continued production over the 10–20 s exposure, diffusion across cells,
thioredoxin recycling, and LITE-1 gating.

## Why targets were not added directly to Geant4-DNA

Geant4-DNA can define chemical reactions and scavengers. Direct insertion of
`Trp_target`, `Cys_target`, or `PRDX_target` would nevertheless require the same
unknown target concentrations, diffusion coefficients, cellular scavenger
composition, oxygenation, and protein-specific reaction rates. Embedding one
arbitrary parameter set in the track chemistry would make the result appear
more mechanistic without adding evidence. A transparent post-chemistry
competition sweep is therefore the more falsifiable primary analysis.

Direct nanometre track continuation was also rejected: the validated transport
stage uses condensed-history electron physics and records micrometre-bounded
deposition steps, not the individual ionizations/excitations required to seed
a faithful Geant4-DNA chemical track. Replaying the full step energy as a
single local electron would invent track structure. The implemented
deposited-energy-weighted spectrum is consequently an approximation and is
reported as such.

## Interpretation rules

- Say **homogeneous-water molecule equivalent**, not intracellular molecule
  count or measured ROS.
- Say **Trp-like/thiol-like interaction opportunity**, not LITE-1 hit.
- Say **PRDX-like encounter capacity**, not redox-relay activation.
- Do not add the Trp and thiol metrics: the same radical population can be
  counted in both alternative target scenarios.
- Do not infer a monotone receptor response from H2O2; published work supports
  both coincidence/redox participation and inhibition/deactivation.

Machine-readable outputs are under
`ros_worm_stage1/validation/v2_1/chemistry/`, including all target and
background-scavenger assumptions for every row.
