# Final neural ROI and surface-scoring audit

## Membership provenance

The anatomical manifest contains 588 objects across compartments. Exactly 276 selected entries are labeled NervousSystem. After proper duplicate-vertex merging, all 276 actual meshes are watertight, consistently wound, and positive signed volume. Interior membership is a logical OR, so overlapping source objects are counted once. Body clipping is applied before volume/mass calculation.

The primary 0.25 µm union has volume 8,663 µm3 and mass 9.00952×10−12 kg at 1,040 kg m−3. The conversion is `8663×10−18×1040 kg`. The density is an explicit proxy.

## Convergence and morphology

Body-clipped volume varies only 3.94% across 0.25, 0.5, 1, and 2 µm pitch. The primary p50/p95/p99 symmetric errors are 0.119/0.246/0.522 µm. Connectivity fragments as thin processes fall between voxel centers; exact member-union membership supplies the primary numerator, not voxel connected components.

The large sampled reference-to-ROI outlier is localized rather than global. More than 10 µm disagreement occurs for 0.257% of reference samples and more than 25 µm for 0.031%, primarily at posterior terminal/process geometry. The reciprocal ROI-to-reference maximum is below the voxel pitch. Exact-only and voxel-only depositions exchange around boundaries, but the net 0.25 µm numerator difference is −0.315% focused and −1.509% diffuse. These outliers do not materially drive mean dose; they invalidate uniform submicrometre or individual-neurite claims.

## Dose stability

Focused voxel ratios range 0.9286–0.9870 and diffuse 0.8428–0.9194. The exact-union numerator with finest-grid mass yields 0.9316 and 0.8730. Registration brackets are −0.9% to +6.6% focused and 0 to +15.9% diffuse around the 0.25 µm baseline. The reconstruction and registration ranges are reported separately from Monte Carlo confidence intervals.

## Surface endpoint and null

The original 1.36-million-triangle nervous surface remains authoritative for unsigned distance. The surface endpoint does not use ROI mass and therefore remains co-primary. Identical full-surface rigid controls preserve triangle content and surface area. Ninety-nine accepted controls per configuration provide 0.01 empirical p-value resolution. The final result does not establish preferential neural deposition.

Conclusion: analysis-only mean neural dose is defensible with explicit anatomical assumptions; individual-neuron, named-neurite, membrane, and histological dose are not.
