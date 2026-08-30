# Scientific context: Bolding/Cannon X-ray neuromodulation

## Why this simulation exists

The ROS-Worm project is intended to provide the physical/radiochemical layer underneath the X-ray neuromodulation work led by Mark Bolding and Kelli Cannon.

The key experimental paper is:

K. E. Cannon et al., **"LITE-1 mediates behavioral responses to X-rays in Caenorhabditis elegans"**, *Frontiers in Neuroscience* 17, 1210138 (2023). DOI: `10.3389/fnins.2023.1210138`. PMID: `37638310`.

The paper reports acute X-ray-evoked behavioral responses in wild-type *C. elegans* that depend on the endogenous UV-sensitive receptor LITE-1. Ectopic LITE-1 expression in muscle produced X-ray-dependent paralysis/egg-ejection phenotypes, supporting the idea that LITE-1 can confer X-ray sensitivity to otherwise insensitive cells.

The project-level question is not merely "how much dose does a worm absorb?" It is:

> Given the experimental X-ray beam, where are low-energy secondary electrons and radiolysis products generated in the worm, especially relative to nervous anatomy, and are their spatial/dose relationships compatible with the rapid LITE-1-dependent responses?

The simulation does **not** by itself prove the molecular activation mechanism of LITE-1.

## Experimental conditions to reproduce

The Cannon/Bolding experiment used a tungsten-target iMOXS-MFR X-ray source with polycapillary focusing. The reported focused beam had an approximately 0.85 mm FWHM spot at the agar surface and was operated at 50 kV. Beam current was varied to change stimulation intensity. The highest focused condition was estimated near 1 Gy/s, while lower current produced roughly 0.2 Gy/s. The paper also reports diffuse dose-rate conditions around 0.19, 0.38, 0.56, and 0.74 Gy/s.

Important modeling consequence: the worm is ~1 mm long and tens of micrometers across, while the focused X-ray spot is on the order of the worm length. Position along the worm and beam placement therefore matter even when material composition differences are modest.

The experimental dose estimates were approximate; the authors note substantial dosimetry uncertainty. Do not overstate simulation precision beyond the experimental input uncertainty.

## Related Bolding X-ray optogenetics literature

Bartley et al., **"Feasibility of cerium-doped LSO particles as a scintillator for X-ray induced optogenetics"**, *Journal of Neural Engineering* 18 (2021) 046036. DOI: `10.1088/1741-2552/abef89`. PMID: `33730704`.

This work demonstrates a separate X-ray-to-neural-activity route: X-rays drive radioluminescence from LSO:Ce particles, which can activate light-sensitive proteins including ChR2/OptoXR. It is relevant because it establishes the broader Bolding lab goal of using deeply penetrating X-rays for spatially targeted neuromodulation, while also emphasizing the need to distinguish direct X-ray effects, radioluminescent intermediates, and downstream cellular responses.

Mantraratnam et al., **"X-ray perception: Animal studies of sensory and behavioral responses to X-rays"**, *Frontiers in Cellular Neuroscience* 16, 917273 (2022). DOI: `10.3389/fncel.2022.917273`.

This review provides historical and biological context for rapid X-ray sensory responses across species and helps frame the *C. elegans* findings as part of a larger X-ray perception/neuromodulation literature.

Kelli Cannon's 2023 UAB dissertation, **"Towards Minimally Invasive Genetically Targeted Control Of Neural Activity Using X-Rays"**, advised by Mark Bolding, is also useful project context. It treats X-genetics as an effort to replace implanted visible-light delivery with X-ray-driven genetically targeted control and discusses LITE-1 as a candidate genetically encoded X-ray receptor.

## What the literature does and does not validate

The Cannon/Bolding *C. elegans* paper directly validates:

- an acute behavioral response to X-rays;
- LITE-1 dependence of that response;
- the ability of ectopic LITE-1 to confer X-ray sensitivity in worm muscle;
- focused 50 kV X-ray stimulation on a scale comparable to the worm.

It does **not** directly provide measured spatial maps of OH, H2O2, hydrated electrons, or neuron-level absorbed dose. Therefore the ROS-Worm simulation should not claim direct agreement with an experimentally measured ROS concentration from that paper.

A defensible comparison is:

1. reproduce beam/dose/exposure conditions;
2. calculate regional energy deposition and secondary-electron spectra;
3. calculate water-radiolysis products with Geant4-DNA under explicitly stated chemistry assumptions;
4. evaluate spatial association with nervous/muscle anatomy;
5. compare dose-response trends and spatial targeting to the phenotypes in the experimental paper;
6. treat the molecular link from radiolysis/direct ionization to LITE-1 activation as a hypothesis unless separately validated.

## Why OpenWorm anatomy matters

For this scientific question, transport-material detail and biological scoring detail are not the same thing. Individual neurons may have nearly the same effective low-energy transport material as surrounding soft tissue/water, yet their **locations** are biologically essential if the endpoint is neural activation. This motivates a two-tier design:

- stable, non-overlapping physical compartments for Geant4 transport;
- high-resolution OpenWorm nervous anatomy retained as a scoring atlas/ROI.

Wu-style *C. elegans* mesh dosimetry is useful as a benchmark that mesh-based worm dosimetry is feasible, but its organ selection was designed for radiation-dose questions, not neuron-level X-genetics. Do not replace the OpenWorm neural atlas with the Wu model.

## Primary references

- Cannon KE et al. 2023. Front Neurosci 17:1210138. DOI `10.3389/fnins.2023.1210138`.
- Bartley AF et al. 2021. J Neural Eng 18:046036. DOI `10.1088/1741-2552/abef89`.
- Mantraratnam V et al. 2022. Front Cell Neurosci 16:917273. DOI `10.3389/fncel.2022.917273`.
- Cannon KE. 2023. UAB dissertation: *Towards Minimally Invasive Genetically Targeted Control Of Neural Activity Using X-Rays*.
