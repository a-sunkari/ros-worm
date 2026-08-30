# ROS-Worm chemistry app

This directory starts from the Geant4-DNA `chem6` example because that example is already known to work on the target Geant4 11.3.2 install in multithreaded mode.

Preserved from `chem6`:

- `ActionInitialization` chemistry setup,
- `StackingAction::NewStage()` handoff to `G4DNAChemistryManager::Instance()->Run()`,
- `G4MoleculeCounter` use for Geant4 11.3.x,
- `ScoreSpecies`, `ScoreLET`, and `PrimaryKiller` scorer structure,
- water world geometry and chemistry reaction setup.

ROS-Worm additions:

- `PrimarySourceConfig` exposes `/ros/source/...` commands.
- `PrimaryGeneratorAction` can use normal `/gun` settings or sample electron energies from CSV.
- `ros_spectrum.in` demonstrates the CSV source mode.

The CSV file must look like:

```text
# energy_keV,weight
0.3224375,7368
0.9473125,2508
...
```

The chemistry application intentionally remains water-radiolysis-only.  It represents the local aqueous phase of tissue, not a complete tissue biochemical model.
