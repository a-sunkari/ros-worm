# Anatomy-resolved X-ray dosimetry and water radiolysis in *Caenorhabditis elegans* during LITE-1-dependent responses

## Abstract

X-rays have been shown to evoke rapid LITE-1-dependent behavioral responses in *Caenorhabditis elegans*. Indeed, ectopic expression of LITE-1 in body wall muscle confers X-ray sensitivity within that tissue. However, the physical and chemical interactions accompanying these responses are poorly characterized. Because X-ray energy in tissue is deposited largely through secondary electrons that initiate water radiolysis, and because LITE-1 gating is sensitive to redox chemistry, radiation-generated reactive species are a plausible intermediate between irradiation and receptor-dependent signaling. We reconstructed the focused 50 kV tungsten and diffuse 20 kV silver irradiation experiments reported by Cannon et al. in an antomically resolved Geant4 model of *C. elegans* and coupled regional energy deposition to  radiolysis simulations. During foucsed irradation, mean nervous system and body wall muscle doses were 0.932 and 1.060 times the whole-worm dose, respectively; during diffuse irradiation, the corresponding ratios were 0.873 and 1.083. Approximately 14% of whole-worm deposited energy occurred within 5 µm of the nervous system or body wall muscle surfaces, and deposition around the native nervous system was similar to that around displaced copies of the same anatomy. Geant4-DNA simulations further showed substantial production of early radiolysis products. For a nominal 2 Gy focused exposure, energy deposited in the nervous system yielded approximately 1.44 × 10⁶ hydroxyl radicals and 9.65 × 10⁵ hydrogen peroxide molecules within 1 µs in liquid water. These results define the regional dosimetry and early radiochemistry associated with X-ray exposure in LITE-1-responsive tissues and motivate direct tests of hydroxyl-radical and peroxide-sensitive mechanisms of LITE-1 activation.

## Introduction

Optical control of excitable cells is a powerful approach to neuromodulation that offers high spatial and temporal precision. Yet, the limited penetration of visible and ultraviolet (UV) light through tissue prevents optical stimulation of deeper targets [2,3]. X-rays can penetrate tissue much more deeply than visible or UV light and have attracted interest as a means of stimulating targets beyond the reach of typical optical methods. Cannon et al. demonstrated that the photoreceptor LITE-1 mediates rapid responses to X-rays in *Caenorhabditis elegans*. Focused irradiation evoked LITE-1-dependent avoidance, while ectopic expression of LITE-1 in body wall muscle conferred X-ray sensitivity to the tissue, producing contraction, paralysis, and egg ejection [1]. The response could begin within approximately two seconds. However, how X-ray photons produce a LITE-1-dependent cellular response remains unknown.

LITE-1 is an invertebrate gustatory receptor homolog that functions as a photoreceptor. Its ultraviolet sensitivity depends strongly on two tryptophan residues, W77 and W328 [4], and recent structural and electrophysiological studies implicate an aromatic network and redox-sensitive cysteines in channel gating [8]. However, direct absorption of X-ray photons, similar to that of UV radiation, is unlikely to explain the observed response. Cannon et al. estimated that a protein the size of LITE-1 would only absorb about one X-ray photon per 50 million molecules per gray [1]. 

In aqueous tissue, X-ray interactions generate energetic secondary electrons that ionize and excite surrounding molecules. Furthermore, they can initiate water radiolysis [Might need citation?]. Importantly, LITE-1 function is also sensitive to cellular redox chemistry. LITE-1 and its paralog GUR-3 contribute to behavioral responses to hydrogen peroxide, and the peroxiredoxin PRDX-2 is required for peroxide sensing in several *C. elegans* sensory neurons [5,9]. Reactive oxygen species can also evoke LITE-1-dependent avoidance through the redox modification of Cys44 [7]. Hydrogen peroxide can also supress some LITE-1-mediated photoresponses [6], suggeseting that its effects depend on the cellular and signaling context.

Here, we developed Monte Carlo simulations of the focused and diffuse X-ray experiments performed by Cannon et al. in an anatomically resolved Geant4 model of C. elegans built from OpenWorm [10–12]. We calculated absorbed dose in the nervous system and body wall muscle, mapped energy deposition relative to these tissues, and used the resulting electron spectra to model early water radiolysis with Geant4-DNA [13–15]. We then examined hydroxyl-radical reactions with tryptophan and cysteine and peroxide chemistry relevant to known features of LITE-1 signaling.

![Figure 1. Experimental and computational framework.](../ros_worm_stage1/validation/publication_figures/main/Figure1_framework.png)

**Figure 1. Experimental configurations and computational framework.** **a**, Focused 50 kV tungsten configuration with a 0.85 mm FWHM footprint over the NGM/agar and polystyrene preparation. **b**, Diffuse 20 kV silver configuration with a 120° emission cone over the M9 and glass preparation. Vertical dimensions are compressed in both schematics. **c**, Nominal photon energy probability distributions with soft and hard spectral brackets. **d**, OpenWorm-derived body wall muscle and nervous system anatomy used for regional and surface-based analysis.

## Materials and Methods

### Experimental irradiation conditions

We modeled the irradiation setup for the focused avoidance, focused muscle/egg ejection, and diffuse muscle paralysis experiments peformed by Cannon et al. [1]. Table 1 summarizes the irradiation conditions used in the simulations.

| Experimental condition | Source | Tube voltage | Irradiation geometry | Reported dose rate | Exposure |
|---|---|---:|---|---:|---:|
| Focused avoidance | iMOXS-MFR, W target | 50 kV | ~0.85 mm FWHM focused spot on NGM agar | ~0.2, 0.5, 0.7, 1.0 Gy s⁻¹ | 10 s |
| Focused muscle/egg ejection | iMOXS-MFR, W target | 50 kV | ~0.85 mm FWHM focused spot on NGM agar | ~1.0 Gy s⁻¹ | 15 s |
| Diffuse muscle paralysis | Amptek Mini-X, Ag target | 20 kV | 120° cone; worm in 5 µL M9 on glass | 0.19, 0.38, 0.56, 0.74 Gy s⁻¹ | 20 s |

In the focused experiments, the agar surface was approximately 5 cm from the polycapillary outlet. The maximum absorbed dose rate was estimated at approximately 1 Gy s⁻¹ by radiochromic dosimetry, with an uncertainty of roughly a factor of two [1]. The worm was centered under the Gaussian beam throughout each simulated exposure. Animal motion during the avoidance assay was not modeled.

For the diffuse experiments, the Mini-X nozzle and filters were removed and the source was operated at 20 kV. Cannon et al. measured the absorbed dose rate at the worm position (approximately 1 cm from the focal spot) with a RadCal 9010 dosimeter and 10 × 6 ionization chamber. Dose rates of 0, 0.19, 0.38, 0.56, and 0.74 Gy s⁻¹ corresponded to tube currents of 0, 50, 100, 150, and 198 µA, respectively [1]. Worms were immersed in 5 µL of M9 on glass with a maximum liquid depth of approximately 0.5 mm and remained within the broad irradiation field for 20 s.

### X-ray spectra and sample geometry

We modeled nominal, softer, and harder source spectra variants for each X-ray system. Bremsstrahlung was modeled using a Kramers photon spectrum with target-specific characteristic emission. Attenuation through beryllium and aluminum filtration was calculated using NIST XCOM mass attenuation coefficients [16].

For the 50 kV tungsten source, the nominal spectrum used a 0.10 mm Be window and 0.10 mm Al filtration, with W L-line emission near 8–11 keV. The nominal mean photon energy was 12.83 keV. The softer and harder spectral variants had mean energies of 10.47 and 14.58 keV, respectively. For the 20 kV silver source, the nominal spectrum used a 0.125 mm Be window with Ag L-line emission near 3 keV. The nominal mean photon energy was 6.09 keV. The softer and harder spectral variants had mean energies of 5.53 and 7.57 keV, respectively. Ag K-shell emission was excluded because the tube voltage was below the Ag K-edge.

For the focused experiment simulations, the worm geometry was placed on a 3 mm water-equivalent NGM agar layer above a 1 mm polystyrene substrate. For the diffuse experiment simulations, the worm geometry was placed in a water-equivalent M9 layer above 1 mm of glass, with 0.405 mm of liquid above the worm and 0.010 mm below it in the nominal model. These dimensions were systematically varied in sensitivity calculations.

Focused photons originated 50 mm above the sample and propagated predominantly along the negative *z* axis with a Gaussian lateral distribution corresponding to the reported 0.85 mm full width at half maximum (FWHM) spot. Diffuse photons originated 10 mm above the sample and were sampled from particle trajectories intersecting a 1.2 × 1.2 mm plane surrounding the worm. Simulated energy deposition was normalized to the experimentally reported absorbed dose.

### Anatomical transport model

The transport geometry was derived from OpenWorm anatomical meshes [11]. The reconstructed worm model measured approximately 0.83 mm in width, 0.88 mm in length, and 0.19 mm in thickness. Body wall muscle, digestive, and reproductive tissues were represented as mutually exclusive internal compartments within the body volume. Residual body tissue was assigned ICRU four-component soft tissue at 1.00 g cm⁻³, body wall muscle was assigned ICRP skeletal muscle at 1.05 g cm⁻³, digestive tissue was assigned an ICRP soft tissue composition at 1.00 g cm⁻³, and reproductive tissue was assigned an ICRP testes composition at 1.04 g cm⁻³.

The nervous system was represented as a scoring region rather than as a separate Geant4 material compartment. This allowed the high-resolution OpenWorm neural anatomy to be retained for regional dose calculations without assigning a distinct bulk material composition to the nervous system. Energy deposition coordinates from the Monte Carlo transport simulation were classified against the neural geometry during post-processing.

### Neural Region of Interest (ROI)

The OpenWorm nervous system comprised 276 closed surface meshes. After duplicate facet vertices were merged, all 276 surfaces were verified to be closed, consistently oriented, and of positive volume. Their union, clipped to the body volume, defined the neural region of interest (ROI), with overlapping volumes counted once.

We generated voxelized representations of the ROI at isotropic pitches of 0.25, 0.5, 1, and 2 µm to evaluate geometric convergence and estimate neural mass. The 0.25 µm reconstruction had a volume of 8,663 µm³. Using a density of 1.04 g cm⁻³, the resulting neural ROI mass was 9.01 × 10⁻¹² kg. A density of 1.00 g cm⁻³ was evaluated separately in sensitivity calculations. Energy deposition in the neural ROI was classified using the exact union of the 276 meshes, whereas the voxelized reconstructions were used to estimate mass and assess geometric sensitivity.

The original nervous system surface mesh was retained for distance calculations. Fidelity of the reconstructed ROI was evaluated from ROI volume, surface agreement, and resulting neural dose ratios across voxel resolutions.

![Figure 2. Neural scoring volume and geometric convergence.](../ros_worm_stage1/validation/publication_figures/main/Figure2_neural_ROI.png)

**Figure 2. Neural ROI and geometric convergence.** **a**, Original high-resolution nervous-system surface overlaid with the 0.25 µm body-clipped ROI in whole-animal coordinates. **b**, Anterior detail. **c**, Body-clipped neural volume across 0.25–2 µm voxel pitch. **d**, Median, 95th-percentile, and 99th-percentile symmetric surface error relative to the original atlas. **e**, Neural-to-whole-worm dose ratio obtained with each voxel reconstruction; dotted colored lines show the exact-union numerator paired with each voxel-derived mass.

### Geant4 transport and energy-deposition scoring

Transport was performed with Geant4 11.3.2 using `G4EmLivermorePhysics` for low-energy electromagnetic interactions [12]. A 100 nm production cut was applied within the biological geometry, and `G4StepLimiterPhysics` limited charged particle steps to a maximum of 0.5 µm in biological volumes.

For each energy-deposition step within the worm, we recorded the primary history, anatomical region, particle and track identifiers, interaction process, deposited energy, pre-step kinetic energy, step length, and spatial coordinates. Charged particle energy deposition was assigned to the midpoint of the step, whereas energy deposited during neutral discrete interactions was assigned to the post-interaction position.

The nominal focused and diffuse simulations each used 100 million primary photon histories. Independent simulations of 10 million histories were used to assess reproducibility and convergence. Energy deposition coordinates falling outside the validated body geometry because of numerical boundary effects were excluded from regional analyses.

### Regional absorbed dose

Deposited energy was summed by primary history for the whole worm, neural ROI, and body wall muscle. Whole-worm absorbed dose was calculated from total deposited energy divided by the combined mass of the physical tissue compartments. Neural dose was calculated from energy deposited within the exact 276-object union and the mass of the 0.25 µm neural reconstruction. Muscle dose was calculated from energy deposited in the body wall muscle compartment and its Geant4 mass.

Regional dose ratios were calculated as

$$
R_r = \frac{D_r}{D_{\mathrm{worm}}}.
$$

Experimental regional doses were obtained by multiplying the reported whole-worm dose by the corresponding simulated dose ratio.

### Distance to neural and muscle surfaces

The minimum distance from each valid energy deposition point to the original neural surface was calculated using a VTK static cell locator. Deposited energy was grouped into distance intervals of 0–1, 1–2, 2–5, 5–10, 10–25, 25–50, and ≥50 µm. The same analysis was performed for the body wall muscle surface.

Spatial deposition around the native neural anatomy was compared with 99 displaced copies of the same surface for each irradiation condition. Each copy was generated by rigid translation and rotation while maintaining comparable containment within the body. The displaced surfaces therefore preserved neural morphology and surface area while sampling nearby locations. This analysis used a fixed subset of 1 million primary histories from each production simulation. Longitudinal energy-deposition profiles were calculated in 20 µm bins along the body axis.

### Statistical analysis and sensitivity calculations

The primary photon history was considered the independent sampling unit. Energy deposition was aggregated by history before calculating regional means, dose ratios, and statistical uncertainties. Standard errors of regional dose ratios were estimated by first-order propagation including the covariance between regional and whole-worm energy deposition. Estimates were also compared with 2,000 Poisson(1)-weighted bootstrap replicates. Convergence was evaluated using subsets of 1, 2, 5, 10, 20, 50, and 100 million histories.

Sensitivity calculations examined neural ROI resolution, neural atlas position, source spectrum, tissue composition, and sample geometry. Neural ROI resolution was evaluated at voxel pitches of 0.25, 0.5, 1, and 2 µm. Atlas position was varied by ±2 µm transversely, ±5 µm longitudinally, and ±3° about the longitudinal axis. Additional 1-million-history simulations evaluated the softer and harder source spectra, simplified worm-only geometry, water-equivalent tissue composition, and independent random seeds. Experimental dose uncertainty was treated separately from Monte Carlo and geometric uncertainty.

### Geant4-DNA water radiolysis

Water radiolysis was simulated using Geant4-DNA `chem6` configuration with the independent reaction time method [13–15]. Separate electron spectra were generated for the neural ROI, the region within 5 µm of the neural surface, and body wall muscle under focused and diffuse irradiation. Electron pre-step kinetic energies were weighted by the energy deposited locally by each electron. Six radiolysis simulations were performed, each using 10,000 chemistry events.

G values were scored at 1 ps, 10 ps, 100 ps, 1 ns, 10 ns, 100 ns, and approximately 1 µs for $\mathrm{OH}^{\bullet}$, $e_{\mathrm{aq}}^{-}$, $\mathrm{H}^{\bullet}$, $\mathrm{H_2O_2}$, $\mathrm{H_3O^+}$, $\mathrm{H_2}$, $\mathrm{OH^-}$, and atomic oxygen. Absolute species yields were scaled with the total all-particle deposited energy in the corresponding region:

$$
N_s(t) = \frac{E_{\mathrm{dep,local}}}{100\,\mathrm{eV}}\,G_s(t),
$$

where $G_s(t)$ is the yield of species $s$ per 100 eV at time $t$. The electron spectrum determined the simulated G value, while the total regional deposited energy determined the absolute species yield. All chemistry simulations used homogeneous liquid water.

### Hydroxyl radical and peroxide reaction kinetics

The calculated radical yields were compared with solution-phase kinetics for chemical groups implicated in LITE-1 function; namely hydroxyl radicals and peroxide reaction rates. The hydroxyl-radical rate constant for free tryptophan was

$$
k_{\mathrm{OH+Trp}} = (1.25 \pm 0.30) \times 10^{10}\,\mathrm{M^{-1}\,s^{-1}}
$$

[17], and that for cysteine was

$$
k_{\mathrm{OH+Cys}} = (5.35 \pm 0.82) \times 10^{9}\,\mathrm{M^{-1}\,s^{-1}}
$$

[18]. For an effective target concentration $C$, bimolecular rate constant $k$, and competing pseudo-first-order scavenging rate $k_{\mathrm{bg}}$, the fraction of hydroxyl radicals reactingn with the target was estimated as

$$
f = \frac{kC}{kC + k_{\mathrm{bg}}}.
$$

Target concentrations from 1 µM to 1 mM and competing backgroudn scavenging rates from 10⁸ to 10¹⁰ s⁻¹ were evaluated. H₂O₂/peroxiredoxin reactions were examined separately by integrating the modeled H₂O₂ abundance from 1 ps to 1 µs and applying peroxiredoxin rate constants spanning 10⁵–10⁸ M⁻¹ s⁻¹ [19].

### Reproducibility

Simulation macros, source definitions, geometry files, random seeds, software versions, analysis scripts, and processed result tables were maintained under version control. SHA-256 hashes were recorded for the two 100-million-history ROOT files and the neural ROI used in the final analyses.

## Results

### Neural ROI reconstruction and geometry sensitivity

The reconstructed neural volume varied by 3.94% across voxel pitches from 0.25 to 2 µm. At 0.25 µm resolution, the median surface deviation from the original nervous system atlas was 0.119 µm, with the 95th and 99th percentiles at 0.246 and 0.522 µm. Larger deviations were confined mainly to a small number of thin posterior processes. Of 100,000 sampled reference points, 0.257% differed by more than 10 µm and 0.031% by more than 25 µm.

Using the exact union of the 276 neural meshes instead of the 0.25 µm voxel representation changed the neural energy deposition numerator by 0.32% during focused irradiation and 1.51% during diffuse irradiation. Across voxel pitches of 0.25, 0.5, 1, and 2 µm, focused neural/whole-worm dose ratios were 0.929, 0.930, 0.955, and 0.987, respectively. Diffuse ratios were 0.860, 0.870, 0.843, and 0.919, respectively (Fig. 2).

Energy deposition which was excluded because of numerical boundary effects accounted for 1.90 × 10⁻⁶ of total worm deposition in the focused simulation and 2.03 × 10⁻⁵ in the diffuse simulation.

### Neural and muscle tissue doses were comparable with whole-worm mean dose

During focused irradiation, the mean nervous system dose was 0.932 times the whole-worm mean dose (95% Monte Carlo interval, 0.865–0.998). The corresponding body wall muscle ratio was 1.060 (1.042–1.078). During diffuse irradiation, the nervous system and body wall muscle ratios were 0.873 (0.752–0.994) and 1.083 (1.047–1.120), respectively (Table 2; Fig. 3a).

Energy deposition within the neural ROI occurred in 1,264 primary histories during focused irradiation and 318 primary histories during diffuse irradiation. The relative Monte Carlo standard errors of the neural dose estimates were 3.6% and 7.1%, respectively. Poisson-weighted bootstrap intervals closely matched the covariance-based intervals, and independent 10 million-history simulations gave similar regional dose estimates.

| Irradiation | Neural/whole-worm dose ratio | 95% MC interval | Muscle/whole-worm dose ratio | 95% MC interval |
|---|---:|---:|---:|---:|
| Focused 50 kV + NGM | 0.932 | 0.865–0.998 | 1.060 | 1.042–1.078 |
| Diffuse 20 kV + M9 | 0.873 | 0.752–0.994 | 1.083 | 1.047–1.120 |

![Figure 3. Regional dose and energy deposition around anatomical surfaces.](../ros_worm_stage1/validation/publication_figures/main/Figure3_dose_and_surface.png)

**Figure 3. Regional dose and energy deposition around anatomical surfaces.** **a**, Nervous system and body wall muscle dose relative to whole-worm mean dose in the 100 million-history focused and diffuse simulations. Whiskers show covariance-based 95% Monte Carlo intervals; pale purple segments show the range obtained across neural ROI reconstructions. **b,c**, Cumulative whole-worm deposited energy as a function of distance from the nervous system and body wall muscle surfaces. **d**, Fraction of deposited energy within 5 µm of the native nervous system surface compared with 99 displaced copies of the same anatomy using fixed subsets of 1 million primary histories.

### Spatial distribution of energy deposition around neural and muscle surfaces

During focused irradiation, 14.230% of whole-worm deposited energy occured within 5 µm of the nervous system surface. The corresponding fraction during diffuse irradiation was 14.388%. Energy deposition around the body wall muscle surface was similar, with 14.298% and 14.350% of whole-worm deposition occurring within 5 µm during focused and diffuse irradiation, respectively (Fig. 3b,c).

The native neural surface was also compared with 99 displaced copies of the same anatomy. Using fixed subsets of 1 million primary histories, the fraction of deposited energy within 5 µm of the native surface was 1.016 times the mean of the displaced surfaces during focused irradiation (*p* = 0.29) and 1.060 times the displaced-surface mean during diffuse irradiation (*p* = 0.08) (Fig. 3d).
Longitudinal energy deposition followed the irradiation geometry. Focused irradiation produced a central maximum corresponding to the beam footprint, whereas diffuse irradiation produced a broader distribution along the body axis. Profiles near the nervous system and body wall muscle followed the corresponding whole-worm distributions (Supplementary Fig. S1).

### Regional dose estimates for the experimental irradiation conditions

Applying the simulated regional dose ratios to the irradiation conditions reported by Cannon et al. gave nervous system and body wall muscle doses on the same scale as the nominal whole-worm dose (Table 3; Fig. 4). Across the focused exposures, estimated nervous system dose ranged from 1.86 to 13.97 Gy and body wall muscle dose from 2.12 to 15.90 Gy. Across the diffuse exposures, the corresponding ranges were 3.32–12.92 Gy and 4.12–16.03 Gy.

| Cannon condition | Nominal whole-worm dose | Neural dose | Muscle dose |
|---|---:|---:|---:|
| Focused 0.2 Gy s⁻¹ × 10 s | 2.0 Gy | 1.86 Gy | 2.12 Gy |
| Focused 0.5 Gy s⁻¹ × 10 s | 5.0 Gy | 4.66 Gy | 5.30 Gy |
| Focused 0.7 Gy s⁻¹ × 10 s | 7.0 Gy | 6.52 Gy | 7.42 Gy |
| Focused 1.0 Gy s⁻¹ × 10 s | 10.0 Gy | 9.32 Gy | 10.60 Gy |
| Focused 1.0 Gy s⁻¹ × 15 s | 15.0 Gy | 13.97 Gy | 15.90 Gy |
| Diffuse 0.19 Gy s⁻¹ × 20 s | 3.8 Gy | 3.32 Gy | 4.12 Gy |
| Diffuse 0.38 Gy s⁻¹ × 20 s | 7.6 Gy | 6.64 Gy | 8.23 Gy |
| Diffuse 0.56 Gy s⁻¹ × 20 s | 11.2 Gy | 9.78 Gy | 12.13 Gy |
| Diffuse 0.74 Gy s⁻¹ × 20 s | 14.8 Gy | 12.92 Gy | 16.03 Gy |

![Figure 4. Experimental exposure conditions mapped to regional dose.](../ros_worm_stage1/validation/publication_figures/main/Figure4_Cannon_exposures.png)

**Figure 4. Neural and muscle dose across the Cannon exposure series.** **a**, Focused 50 kV tungsten exposures on NGM, including the 15 s egg-ejection condition. **b**, Diffuse 20 kV silver exposures in M9. Open circles show reported whole-worm dose; diamonds and squares show the corresponding neural and muscle estimates. Pale horizontal segments indicate the 0.5–2× experimental dosimetry range. Focused estimates assume a centered animal receiving the nominal pulse.

### Source and geometry sensitivity preserved the regional dose scale

Monte Carlo sampling, neural reconstruction, and atlas registration contributed distinct uncertainties to neural dose. During focused irradiation, the 95% Monte Carlo interval was 0.865–0.998, the four-pitch reconstruction range was 0.929–0.987, and the registration bracket was 0.924–0.993. During diffuse irradiation, the corresponding ranges were 0.752–0.994, 0.843–0.919, and 0.873–1.012.

The low-energy sample environment had its largest effect in the diffuse configuration. In the 1-million-history sensitivity set, 14.73% of diffuse whole-worm energy was deposited within 5 µm of the nervous surface in the nominal M9/glass geometry; removing the surrounding medium and substrate reduced this fraction to 12.98%. Soft and hard diffuse spectra gave 14.32% and 15.04%, respectively. For focused irradiation, the nominal near-neural fraction was 14.32%, compared with 14.80% in the worm-only geometry and 13.41–13.98% across the soft and hard spectral variants. History convergence and the separate uncertainty components are shown in Supplementary Figure S2.

### Water radiolysis developed from picoseconds to microseconds

Geant4-DNA predicted prompt radiolysis for both irradiation conditions. For the focused neural spectrum, the $\mathrm{OH}^{\bullet}$ G value was 5.026 molecules per 100 eV at 1 ps. As spur chemistry proceeded, the hydroxyl-radical yield decreased and molecular products accumulated. By approximately 1 µs, focused neural G($\mathrm{OH}^{\bullet}$) was approximately 1.38 molecules per 100 eV and G(H₂O₂) approximately 0.92 molecules per 100 eV. Hydrated electrons, hydrogen radicals, and H₃O⁺ were present from the earliest simulated time points. Neural and muscle spectra produced closely similar G-value trajectories.

Scaling the G values by regional deposited energy gave exposure-level liquid-water yields. At the nominal 2 Gy focused avoidance condition, neural deposition corresponded to approximately 1.44 × 10⁶ hydroxyl radicals and 9.65 × 10⁵ H₂O₂ molecules at approximately 1 µs. At 10 Gy focused exposure, the corresponding values were 7.19 × 10⁶ and 4.82 × 10⁶. Across the diffuse 3.8–14.8 Gy series, neural yields ranged from approximately 2.53 × 10⁶ to 9.87 × 10⁶ hydroxyl radicals and from 1.72 × 10⁶ to 6.71 × 10⁶ H₂O₂ molecules.

![Figure 5. Time-resolved water-radiolysis yields.](../ros_worm_stage1/validation/publication_figures/main/Figure5_radiolysis.png)

**Figure 5. Time-resolved Geant4-DNA water radiolysis for the neural ROI.** **a**, Hydroxyl radical, hydrated electron, and hydrogen radical. **b**, H₂O₂, H₂, and H₃O⁺. G values are shown from 1 ps to approximately 1 µs for focused and diffuse neural electron spectra weighted by local deposited energy.

### Hydroxyl-radical kinetics support reactions with LITE-1-relevant chemical motifs

Combining the modeled 1 ps hydroxyl-radical yield with published solution-phase rate constants produced a wide range of conditional target-capture estimates. For the 2 Gy focused neural condition, the tryptophan sweep ranged from approximately 6.6 to 5.85 × 10⁵ captured-radical equivalents, while the cysteine/thiol sweep ranged from approximately 2.8 to 2.67 × 10⁵. The range arose primarily from the three orders of magnitude assigned to effective target concentration and the two orders of magnitude assigned to competing scavenging.

The modeled H₂O₂ trajectory also overlapped the kinetic range of peroxiredoxin reactions [19]. Because effective target abundance, accessibility, and intracellular scavenging are not known for the irradiated cells, these calculations define plausible chemical regimes rather than receptor-specific modification yields.

![Figure 6. Conditional radical-capture estimates for LITE-1-relevant target classes.](../ros_worm_stage1/validation/publication_figures/main/Figure6_target_chemistry.png)

**Figure 6. Conditional hydroxyl-radical capture by LITE-1-relevant target classes.** **a,b**, Tryptophan and thiol capture estimates for the nominal 2 Gy focused neural exposure across effective target concentrations of 1 µM–1 mM and competing scavenging rates of 10⁸–10¹⁰ s⁻¹. **c**, Corresponding ranges across the modeled Cannon exposure conditions. Estimates use the liquid-water radical yield and published free-solute rate constants.

## Discussion

The simulations resolve a simple physical result: neither the nervous system nor body-wall muscle occupies a uniquely intense X-ray field. Neural mean dose was approximately 93% of whole-worm mean dose during focused irradiation and 87% during diffuse irradiation, whereas muscle received approximately 106% and 108%, respectively. About 14% of whole-worm deposited energy occurred within 5 µm of either anatomical surface, and modest displacement of the neural atlas did not reveal strong enrichment around its native position. The tissues that exhibit LITE-1-dependent phenotypes therefore differ much more in receptor expression than in modeled radiation exposure.

This comparison is especially relevant to the ectopic-muscle experiments of Cannon et al. [1]. Expression of LITE-1 in body-wall muscle changed the acute response to X-rays without requiring an unusual muscle radiation field. The transport results are consistent with a broadly distributed physical stimulus followed by tissue-specific biological transduction. They also fit the observed dose scale: wild-type worms showed little change in locomotion at the highest diffuse exposure, while *pmyo-3::lite-1* animals became strongly paralyzed [1]. This is difficult to explain as generalized motor toxicity alone, particularly given the relative radioresistance of *C. elegans* reported in earlier radiation studies [20–22].

Radiation chemistry occurs on a timescale compatible with such a sequence. Ionization and electron slowing precede the behavioral response by many orders of magnitude, and the Geant4-DNA calculations place hydroxyl radicals, hydrated electrons, and hydrogen radicals in the system within picoseconds. Molecular products including H₂O₂ develop over nanoseconds to microseconds. At the nominal 2 Gy focused condition, the neural energy deposition corresponded to approximately 1.44 × 10⁶ hydroxyl radicals and 9.65 × 10⁵ H₂O₂ molecules by approximately 1 µs in homogeneous liquid water. These numbers set the scale of the initial radiochemical source; their intracellular fate will depend on scavenging, oxygenation, protein accessibility, and enzymatic redox chemistry.

Two experimentally separable routes are suggested by the LITE-1 literature. The first is radical chemistry involving aromatic residues. W77 and W328 are required for ultraviolet sensitivity [4], and free tryptophan reacts with hydroxyl radicals near the diffusion-controlled limit, largely through addition to the indole ring [17]. The conditional capture calculations show that this chemistry is kinetically feasible over a broad range of target concentrations and competing scavenging rates. A residue within the folded receptor will not behave identically to free tryptophan, but the basic reaction is fast enough to warrant direct experimental testing.

The second route is peroxide/thiol signaling. GUR-3-dependent H₂O₂ sensing requires PRDX-2 [5], and PHA neurons use LITE-1 and PRDX-2 to respond to micromolar H₂O₂ [9]. Bischer et al. showed that reactive oxygen species can drive LITE-1-dependent avoidance and identified Cys44 as important for this response [7]. Hanson et al. provided structural and electrophysiological evidence for redox-sensitive gating and a possible PRDX-2 interaction site [8]. At the same time, Zhang et al. found that H₂O₂ can suppress LITE-1 photoresponses [6]. Radiation-generated redox chemistry could therefore influence activation, sensitization, deactivation, or associated signaling; the direction cannot be inferred from H₂O₂ production alone.

The largest physical uncertainty is the photon field at the specimen. The reconstructed spectra incorporate tube voltage, target identity, characteristic lines, and available window and filtration information, but the specimen-plane spectra were not measured in the original experiments. The diffuse M9/glass environment also affected near-neural deposition in sensitivity calculations, showing that low-energy transport depends on the immediate sample geometry. In the focused avoidance assay, animal motion adds a separate uncertainty because the dose mapping assumes a centered worm receiving the full pulse. Direct specimen-plane spectroscopy and dosimetry, together with frame-by-frame tracking of beam overlap, would tighten the absolute regional dose estimates.

Anatomical and chemical uncertainties occur at a different level. The 276-object neural ROI was stable enough for a whole-system mean-dose estimate, but it represents a single OpenWorm anatomy and uses a tissue-density proxy rather than subject-specific histology. The Geant4-DNA calculation represents homogeneous liquid water; intracellular oxygen, glutathione, thioredoxin, peroxiredoxins, proteins, membranes, and other scavengers will alter radical survival and molecular products. These limitations matter most when moving from a radiochemical source term to receptor chemistry, not when comparing the physical dose received by neural and muscle tissue.

The most informative next experiments are therefore those that perturb chemistry while preserving the radiation field. Measurement of the focused and diffuse spectra and dose at the specimen plane would first improve the absolute physical model. Hydroxyl-radical scavengers, catalase, or PRDX-2 manipulation could then probe distinct points in the chemical pathway. Mutations at W77/W328, C44, and other redox-sensitive residues would help distinguish aromatic-radical chemistry from peroxide/thiol signaling. Simultaneous calcium, current, or redox measurements during irradiation could connect these perturbations to receptor-dependent cellular activity before the behavioral response develops.

In summary, the Cannon/Bolding irradiation conditions place the *C. elegans* nervous system and body-wall muscle at similar dose scales and generate prompt water-radiolysis chemistry throughout both tissues. The model does not identify a neuron-specific radiation hotspot. Instead, it supports a physical picture in which X-ray energy deposition is broadly available, while LITE-1 expression supplies biological specificity. The remaining mechanistic question is experimental: which component of the early radiation chemistry, if any, is coupled to LITE-1-dependent signaling?

## Bibliography

1. Cannon KE, Ranasinghe M, Millhouse PW, Roychowdhury A, Dobrunz LE, Foulger SH, Gauntt DM, Anker JN, Bolding M. LITE-1 mediates behavioral responses to X-rays in *Caenorhabditis elegans*. *Frontiers in Neuroscience*. 2023;17:1210138. doi:10.3389/fnins.2023.1210138.

2. Mantraratnam V, Bonnet J, Rowe C, Janko D, Bolding M. X-ray perception: animal studies of sensory and behavioral responses to X-rays. *Frontiers in Cellular Neuroscience*. 2022;16:917273. doi:10.3389/fncel.2022.917273.

3. Bartley AF, Fischer M, Bagley ME, Barnes JA, Burdette MK, Cannon KE, Bolding MS, Foulger SH, McMahon LL, Weick JP, Dobrunz LE. Feasibility of cerium-doped LSO particles as a scintillator for X-ray induced optogenetics. *Journal of Neural Engineering*. 2021;18(4). doi:10.1088/1741-2552/abef89.

4. Gong J, Yuan Y, Ward A, Kang L, Zhang B, Wu Z, Peng J, Feng Z, Liu J, Xu XZS. The *C. elegans* taste receptor homolog LITE-1 is a photoreceptor. *Cell*. 2016;167(5):1252–1263.e10. doi:10.1016/j.cell.2016.10.053.

5. Bhatla N, Horvitz HR. Light and hydrogen peroxide inhibit *C. elegans* feeding through gustatory receptor orthologs and pharyngeal neurons. *Neuron*. 2015;85(4):804–818. doi:10.1016/j.neuron.2014.12.061.

6. Zhang W, He F, Ronan EA, Liu H, Gong J, Liu J, Xu XZS. Regulation of photosensation by hydrogen peroxide and antioxidants in *C. elegans*. *PLoS Genetics*. 2020;16(12):e1009257. doi:10.1371/journal.pgen.1009257.

7. Bischer AP, Baran TM, Wojtovich AP. Reactive oxygen species drive foraging decisions in *Caenorhabditis elegans*. *Redox Biology*. 2023;67:102934. doi:10.1016/j.redox.2023.102934.

8. Hanson SM, Scholüke J, Liewald J, Sharma R, Ruse C, Engel M, Schüler C, Klaus A, Arghittu S, Baumbach F, Seidenthal M, Dill H, Hummer G, Gottschalk A. Structure-function analysis suggests that the photoreceptor LITE-1 is a light-activated ion channel. *Current Biology*. 2023;33(16):3423–3435.e5. doi:10.1016/j.cub.2023.07.008.

9. Quintin S, Aspert T, Ye T, Charvin G. Distinct mechanisms underlie H2O2 sensing in *C. elegans* head and tail. *PLoS ONE*. 2022;17(9):e0274226. doi:10.1371/journal.pone.0274226.

10. White JG, Southgate E, Thomson JN, Brenner S. The structure of the nervous system of the nematode *Caenorhabditis elegans*. *Philosophical Transactions of the Royal Society of London B*. 1986;314(1165):1–340. doi:10.1098/rstb.1986.0056.

11. Szigeti B, Gleeson P, Vella M, Khayrulin S, Palyanov A, Hokanson J, Currie M, Cantarelli M, Idili G, Larson S. OpenWorm: an open-science approach to modeling *Caenorhabditis elegans*. *Frontiers in Computational Neuroscience*. 2014;8:137. doi:10.3389/fncom.2014.00137.

12. Agostinelli S, Allison J, Amako K, et al. Geant4—a simulation toolkit. *Nuclear Instruments and Methods in Physics Research Section A*. 2003;506(3):250–303. doi:10.1016/S0168-9002(03)01368-8.

13. Bernal MA, Bordage MC, Brown JMC, et al. Track structure modeling in liquid water: a review of the Geant4-DNA very low energy extension of the Geant4 Monte Carlo simulation toolkit. *Physica Medica*. 2015;31(8):861–874. doi:10.1016/j.ejmp.2015.10.087.

14. Shin WG, Ramos-Méndez J, Tran NH, Okada S, Perrot Y, Villagrasa C, Incerti S. Geant4-DNA simulation of the pre-chemical stage of water radiolysis and its impact on initial radiochemical yields. *Physica Medica*. 2021;88:86–90. doi:10.1016/j.ejmp.2021.05.029.

15. Tran HN, Archer J, Baldacchino G, et al. Review of chemical models and applications in Geant4-DNA: report from the ESA BioRad III Project. *Medical Physics*. 2024;51(9):5873–5889. doi:10.1002/mp.17256.

16. Berger MJ, Hubbell JH, Seltzer SM, Chang J, Coursey JS, Sukumar R, Zucker DS, Olsen K. XCOM: Photon Cross Sections Database, NIST Standard Reference Database 8. National Institute of Standards and Technology. doi:10.18434/T48G6X.

17. Armstrong RC, Swallow AJ. Pulse- and gamma-radiolysis of aqueous solutions of tryptophan. *Radiation Research*. 1969;40(3):563–579. doi:10.2307/3573010.

18. Mezyk SP. Determination of the rate constant for the reaction of hydroxyl and oxide radicals with cysteine in aqueous solution. *Radiation Research*. 1996;145(1):102–106. doi:10.2307/3579203.

19. Ogusucu R, Rettori D, Munhoz DC, Netto LES, Augusto O. Reactions of yeast thioredoxin peroxidases I and II with hydrogen peroxide and peroxynitrite: rate constants by competitive kinetics. *Free Radical Biology and Medicine*. 2007;42(3):326–334. doi:10.1016/j.freeradbiomed.2006.10.042.

20. Sakashita T, Takanami T, Yanase S, Hamada N, Suzuki M, Kimura T, Kobayashi Y, Ishii N, Higashitani A. Radiation biology of *Caenorhabditis elegans*: germ cell response, aging and behavior. *Journal of Radiation Research*. 2010;51(2):107–121. doi:10.1269/jrr.09100.

21. Johnson TE, Hartman PS. Radiation effects on life span in *Caenorhabditis elegans*. *Journal of Gerontology*. 1988;43(5):B137–B141. doi:10.1093/geronj/43.5.B137.

22. Sakashita T, Hamada N, Ikeda DD, Suzuki M, Yanase S, Ishii N, Kobayashi Y. Locomotion-learning behavior relationship in *Caenorhabditis elegans* following gamma-ray irradiation. *Journal of Radiation Research*. 2008;49(3):285–291. doi:10.1269/jrr.07102.
