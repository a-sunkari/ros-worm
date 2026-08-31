# Results: thesis v2 physical-plausibility study

## Production transport

| Quantity | Focused nominal + NGM | Diffuse nominal + M9 |
|---|---:|---:|
| Histories | 10,000,000 | 10,000,000 |
| Energy deposition (keV/history) | 0.03665 | 0.009443 |
| Eligible electron births/history | 0.006561 | 0.001640 |
| Eligible births | 65,612 | 16,396 |
| Births within 5 µm | 9,311 | 2,440 |
| Within-5-µm fraction | 14.191% | 14.882% |
| Conditional within-5-µm births/whole-worm Gy | 1.150 × 10⁶ | 1.170 × 10⁶ |
| Mean within-5-µm birth energy | 5.429 keV | 5.619 keV |
| Nonfinite/out-of-body eligible records | 0 | 0 |

Across three independent 1M replicates, the conditional within-5-µm rate was
(1.176 ± 0.032) × 10⁶/Gy focused and (1.138 ± 0.082) × 10⁶/Gy diffuse (mean ±
sample standard deviation). Corresponding within-5-µm fractions were 14.42 ±
0.50% and 14.45 ± 0.91%.

## Physical-compartment energy deposition

Production energy fractions were similar between source conditions. In the
focused run, the residual body, body-wall muscle, digestive, and reproductive
compartments received 90.10%, 2.38%, 4.91%, and 2.60% of scored energy. Diffuse
fractions were 89.76%, 2.51%, 5.14%, and 2.59%. Nervous and excretory rows are
zero by design because they are post-processing atlases rather than physical
volumes. The complete per-run regional table is
`validation/v2/all_regional_transport.csv`.

## Distance resolution

The focused production fractions by shell were 1.37%, 2.52%, 10.30%, 16.89%,
28.39%, 24.03%, and 16.50% from the nearest to the ≥50 µm shell. Diffuse values
were 1.45%, 2.37%, 11.06%, 16.61%, 28.71%, 23.74%, and 16.06%. The two
distance distributions are therefore similar after their different source and
medium conditions.

## Neural matched-null result

The real focused atlas had 14.191% of births within 5 µm; the mean across 12
accepted matched rigid perturbations was 14.121% (ratio 1.005, empirical
upper-tail p=0.154). Diffuse values were 14.882% real and 14.524% null (ratio
1.025, empirical p=0.077).

This falsifies a strong neural-specific enrichment claim for the tested null
family. The neural atlas provides an anatomically meaningful coordinate system,
but proximity mostly reflects how a large internal neural surface occupies the
small worm. No neuron-selective transport mechanism is demonstrated.

## Muscle comparison

Focused within-5-µm rates were 1.150 × 10⁶/Gy for nervous surface and
1.128 × 10⁶/Gy for body-wall muscle surface. Diffuse values were 1.170 ×
10⁶/Gy and 1.157 × 10⁶/Gy. Births physically inside the body-wall compartment
were about 0.195 × 10⁶/Gy focused and 0.192 × 10⁶/Gy diffuse.

Thus both neural and muscle-associated tissues experience a comparable
secondary-electron environment. This is consistent with the Cannon observation
that ectopic muscle LITE-1 confers X-ray sensitivity: the genetic sensitivity
element need not rely on a tissue-specific X-ray transport enhancement.

## Experimental environment and source sensitivity

Paired 1M comparisons identified medium geometry as the strongest tested
physical input. Removing the focused downstream agar/dish changed conditional
near-neural births/Gy by only +0.3%. Removing the diffuse overlying M9/glass
increased the rate by 41.2% and reduced mean near-neural electron energy by
37.2%. A shallower M9 layer likewise increased the rate. The diffuse drop
therefore cannot be omitted.

Paired 1M soft/hard spectra changed the focused conditional rate by +5.1% and
−11.2% relative to nominal. Diffuse changes were −1.5% and +1.5%. Paired 1M
focused beam offsets of −0.2/+0.2 mm changed the rate by −2.8/+4.8%; FWHM
0.65/1.05 mm changed it by −4.0/−1.3%. The nominal physical-plausibility result
survived these brackets. Exact source spectra and liquid depth remain the most
valuable measurements for reducing model uncertainty.

## Dose-series scaling

Because the model is fluence-linear, the conditional physical driver scales
monotonically through every reported exposure. Using the 1M replicate means,
diffuse 20 s exposures correspond to approximately 4.33, 8.65, 12.75, and
16.85 million near-neural births at 0.19, 0.38, 0.56, and 0.74 Gy/s. Focused
10 s exposures span about 2.35 to 11.76 million over 0.2–1 Gy/s, and the 15 Gy
egg-ejection condition corresponds to about 17.65 million.

This monotonicity is expected from linear transport and is compatible with,
but does not explain, the behavioral trend. It is not a fit and is not evidence
of causality or a biological threshold.

## Time-resolved water radiolysis

At 1 ps, focused/diffuse G(•OH) values were 5.035/5.040 and G(H₂O₂) values
0.0516/0.0508 molecules/100 eV. By approximately 1 µs, G(•OH) decreased to
1.463/1.485 while G(H₂O₂) increased to 0.889/0.885. Hydrated-electron G values
decreased from about 4.08 at 1 ps to 1.47–1.49 at 1 µs.

Radiochemical products therefore arise orders of magnitude before behavioral
responses, satisfying a necessary timing condition for plausibility. The near
identity of focused and diffuse G curves shows that, after conditioning on the
secondary spectrum, total delivered energy and spatial distribution matter
more than modest spectral differences for this homogeneous-water chemistry.

As an explicitly conditional energy-budget calculation, full local
thermalization of the near-neural birth-energy sum would correspond at ~1 µs
to 0.19–0.95 billion •OH molecule equivalents over the 2–10 Gy focused
avoidance bracket, 1.42 billion for the 15 Gy focused egg-ejection condition,
and 0.35–1.36 billion across the 3.8–14.8 Gy diffuse series. Corresponding
H₂O₂ equivalents are 0.12–0.58, 0.86, and 0.21–0.81 billion. These are neither
local concentrations nor predicted surviving intracellular molecule counts;
they are homogeneous-water G-value conversions of a birth-energy budget.

## Navigation and coordinate audit

The 10M runs produced 220 focused and 42 diffuse `GeomNav1002` incidents (22.0
and 4.2 per million). They involved WholeBodyEnvelope boundaries with digestive,
body-wall, or reproductive daughters. No fatal navigation failures occurred.
The incident frequency varied across seeds but did not generate nonfinite or
out-of-body eligible electron records. Shrinking or destructively repairing the
anatomy was rejected because the warnings are rare and the scientific cost was
not justified. They remain a quantified limitation.

All 10M eligible coordinates lay within the verified body bounds, and the v2
scorer independently requires finite coordinates, recorded in-body status, and
geometric body containment. The prior extreme-coordinate failure mode is
therefore excluded explicitly rather than assumed absent.
