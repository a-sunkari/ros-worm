# ROS-Worm post-processing summary

Processed `7` full two-stage runs.

## Output tables

- `tables/key_species_scaled_summary.csv`
- `tables/regional_chemistry_species_scaled_summary.csv`
- `tables/regional_transport_scaled_summary.csv`
- `tables/run_index.csv`
- `tables/secondary_electron_summary_by_region.csv`
- `tables/secondary_electrons_all_runs.csv`

## Output plots

- `plots/regional_deposited_energy_fraction.html`
- `plots/regional_radiolysis_g_values_key_species.html`
- `plots/scaled_hydroxyl_yield_heatmap.html`
- `plots/scaled_oh_h2o2_yields_by_condition.html`
- `plots/scaled_regional_dose_contributions.html`
- `plots/secondary_electron_counts_by_region.html`
- `plots/secondary_electron_energy_distributions.html`

## Notes

- Stage 1 uses heterogeneous tissue-equivalent transport materials.
- Stage 2 uses Geant4-DNA liquid-water chemistry driven by each region's secondary electron spectrum.
- `scaled_energy_fraction_equivalent_Gy` distributes the requested experimental dose by the Monte Carlo deposited-energy fraction.
- `scaled_region_dose_Gy_mass_normalized` additionally divides scaled deposited energy by compartment mass; interpret carefully because anatomical compartment masses and residual-body nesting remain model assumptions.
- Low-stat compartments, especially excretory and sometimes reproductive, should not be overinterpreted without higher-history runs.
