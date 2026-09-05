# ROS-Worm publication figure style guide

## Purpose

This is the authoritative visual specification for the manuscript figures. It is implemented in `ros_worm_stage1/scripts/publication_style.py`; individual figure scripts must not redefine fonts, semantic colors, line weights, or export settings.

The style is intentionally technical and restrained. The design goal is rapid reading at journal size, not presentation-scale impact. Figure titles live in captions. Panels communicate one result each, and non-data ink is kept subordinate to the measurements.

## Publisher guidance used

The implementation follows the overlapping practical requirements of major publishers:

- Nature accepts figures at approximately 90 mm (single column) or 180 mm (double column), asks for editable vector artwork where possible, and recommends Arial or Helvetica with approximately 5–7 pt final text. Sources: [Nature initial submissions](https://www.nature.com/nature/for-authors/initial-submission) and [Nature research figure specifications](https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/).
- Nature's manuscript checklist specifies 89 or 183 mm widths, 6–8 pt labels, and lines no thinner than 0.5 pt: [Nature manuscript checklist](https://www.nature.com/documents/nature-manuscript-checklist-research.pdf).
- PLOS asks for readable 8–12 pt text where practical, at least 0.2 mm line weight, captions outside the artwork, and 300–600 dpi for raster or combined artwork: [PLOS Biology figure guidance](https://journals.plos.org/plosbiology/s/figures).
- Elsevier recommends vector formats for line art, consistent lettering, and sizing at intended publication dimensions: [Elsevier artwork overview](https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-overview).

Representative article figures were reviewed in addition to publisher rules. Recent Geant4-DNA work uses compact technical schematics, aligned quantitative panels, logarithmic chemistry time axes, and direct comparisons on common scales (Shin et al., *Scientific Reports*, 2024, [doi:10.1038/s41598-024-76769-0](https://www.nature.com/articles/s41598-024-76769-0)). A recent computational-biology study makes model choices and their impact explicit rather than hiding them behind a single preferred output (Yu and Bagheri, *PLOS Computational Biology*, 2024, [doi:10.1371/journal.pcbi.1011917](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1011917)). A Geant4 spatial-dose study uses shared axes and restrained aligned profiles to compare irradiation configurations (Reaz et al., *Scientific Reports*, 2024, [doi:10.1038/s41598-024-55104-7](https://www.nature.com/articles/s41598-024-55104-7)). The Cannon/Bolding experimental paper was reviewed to ensure the visual mapping retains the actual focused/diffuse exposure structure rather than inventing a continuous simulated response (Cannon et al., *Frontiers in Neuroscience*, 2023, [doi:10.3389/fnins.2023.1210138](https://doi.org/10.3389/fnins.2023.1210138)).

Publisher requirements differ slightly. ROS-Worm therefore uses the conservative intersection: 182 mm maximum width, 7 pt base type, 0.55 pt axes, editable vector text, and 600 dpi PNG fallbacks. Final resizing for a selected journal should preserve the aspect ratio and never reduce labels below that journal's minimum.

## Page geometry and typography

- Main and supplementary figures are 7.15 in (approximately 182 mm) wide unless a later journal layout calls for an explicitly tested single-column version.
- The base font is Liberation Sans, with Arial and Helvetica as fallbacks. The SVG retains text objects; PDF text is embedded as TrueType.
- Base labels are 7 pt; tick labels 6.5 pt; legends 6.3 pt; panel letters 9 pt bold lowercase.
- Panel titles are short scientific descriptors, aligned left. The overall figure title is never repeated inside the figure.
- Axis lines are 0.55 pt and data lines generally 0.85–1.25 pt. Top and right spines are removed unless a matrix image requires a bounded frame.
- Major grid lines are thin, pale gray, and shown only on the axis that assists quantitative comparison.
- Panel letters occupy consistent upper-left positions and do not collide with axes or titles.

## Semantic visual encoding

| Meaning | Color | Additional encoding |
|---|---|---|
| Focused irradiation | `#0072B2` blue | circles; solid line |
| Diffuse irradiation | `#D55E00` vermillion | squares; dashed line when overlaid |
| Nervous-system quantity | `#6A51A3` purple | circle/diamond depending on context |
| Body-wall muscle | `#1B9E77` blue-green | square |
| Whole-worm reference | `#202124` dark neutral | open circle or dashed reference line |
| Null/control | `#B8BDC3` light gray | small points or pale band |
| Trp-like chemistry | `#3B6FB6` muted blue | circle |
| Thiol-like chemistry | `#C98B17` ochre | square |

Focused/diffuse color denotes irradiation only; neural/muscle color denotes anatomy only. When both concepts occur in one panel, shape and line style carry the second distinction. No scientific comparison relies on hue alone. The palette was selected for common red-green color-vision deficiencies, and a grayscale contact sheet is generated for every release.

## Statistical graphics

- Ratios use points and intervals, not filled bars. A reference line at 1.0 shows equality with whole-worm mean dose.
- Monte Carlo sampling intervals and deterministic model ranges use different marks and are never visually pooled into one Gaussian error bar.
- Null experiments show every retained null realization. The native atlas is a prominent marker on the same scale; empirical probabilities are annotated without implying parametric significance.
- Fluence-linear exposure mappings are displayed as discrete experimental conditions. Connecting lines are avoided because the transport was not independently re-simulated at each nominal dose.
- Log axes are used only where the underlying quantity spans orders of magnitude. Zero and reference baselines are retained whenever scientifically meaningful.
- Smoothing is not applied to noisy transport profiles. Raw bins and tracked machine-readable inputs remain authoritative.

## Composition rules

- Each main figure must advance one manuscript claim that can be identified in roughly five seconds.
- Related evidence is combined only when a shared visual comparison strengthens the conclusion. Detailed diagnostics move to supplementary material.
- Legends occupy structured empty space; direct curve labels are preferred for chemistry time courses.
- Explanatory prose inside panels is limited to definitions of marks or assumptions that would otherwise be ambiguous. Full interpretation belongs in the caption.
- Anatomy/scenario diagrams use flat technical geometry, real source parameters, and measured dimensions. Decorative icons, gradients, shadows, pseudo-3D elements, and dashboard boxes are prohibited.

## Export and quality control

`make_publication_figures_final.py` writes PDF, SVG, and 600 dpi PNG files. Line plots remain vector. Dense anatomy points may be rasterized inside a vector container to keep files usable; labels and axes remain editable.

Every release must pass all of the following:

1. Render at the intended 182 mm width.
2. Inspect the color and grayscale contact sheets at approximately actual page size.
3. Confirm labels, units, panel letters, line styles, and markers remain legible.
4. Confirm no legend covers data and no annotation is clipped.
5. Verify every PNG is exactly 600 dpi at its declared dimensions.
6. Verify SVG contains live text and PDF uses embedded fonts.
7. Verify file hashes and all input hashes against the tracked manifest.
8. Regenerate twice and confirm deterministic artifact hashes.

Run:

```bash
MPLCONFIGDIR=/tmp/mpl-pub /home/asunkari/miniconda3/envs/ros/bin/python \
  ros_worm_stage1/scripts/make_publication_figures_final.py \
  --repo . --outdir ros_worm_stage1/validation/publication_figures

/home/asunkari/miniconda3/envs/ros/bin/python \
  ros_worm_stage1/scripts/audit_publication_figures.py \
  --repo . --figure-root ros_worm_stage1/validation/publication_figures
```
