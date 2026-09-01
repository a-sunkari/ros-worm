# Final radiochemistry audit

## Input and normalization

Six seeded 10,000-event Geant4-DNA cases cover focused/diffuse × neural/muscle/perineural-5µm. Electron spectra are weighted by actual local electron deposited energy. Absolute budgets multiply Geant4-DNA G values by actual all-particle regional deposited energy. Summed secondary-electron birth kinetic energy is retained only as a historical sensitivity and is not the primary exposure normalization.

The preserved chem6-derived lifecycle and IRT timing use Geant4 11.3.2. Input spectra, chemistry seeds, event counts, configs, and hashes are in `validation/final/chemistry/chemistry_run_index.csv`.

## Reported species and time points

Tracked species are H3O+, OH, OH−, hydrated electron, H radical, H2, H2O2, and O. Paper plots emphasize OH, H2O2, hydrated electron, H radical, and H3O+ at 1 ps, 10 ps, 100 ps, 1 ns, 10 ns, 100 ns, and approximately 1 µs. Every plotted species exists in the implemented chemistry.

## Cross-region behavior

Neural and muscle G values are similar within each irradiation because the spectra differ modestly. Total muscle molecule equivalents are much larger primarily because muscle mass/energy is larger. Regional dose and G value, not total molecules, are the equal-basis biological comparison.

## Interpretation and limits

Outputs are homogeneous-liquid-water molecule equivalents and G values. They are not intracellular molecules, concentrations, surviving ROS, or a tissue reaction network. Condensed-history micrometre steps do not contain the individual water ionizations needed for direct nanometre track continuation; the study therefore does not invent track structure.

OH/Trp, OH/Cys, and H2O2/PRDX calculations use literature kinetics and concentration/scavenging sweeps. They are opportunity metrics. Hydrated electron and H radical are reported as water products but excluded from the LITE-1 index without a sufficiently direct protein-relevant target rate. No channel or behavior metric is calibrated.
