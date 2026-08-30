#include "PhysicsList.hh"

#include "G4SystemOfUnits.hh"
#include "G4EmLivermorePhysics.hh"
#include "G4DecayPhysics.hh"
#include "G4StepLimiterPhysics.hh"
#include "G4LossTableManager.hh"
#include "G4ProductionCutsTable.hh"

PhysicsList::PhysicsList()
{
  // Low-energy X-ray/photon/electron transport. Livermore handles photoelectric,
  // Rayleigh, Compton, bremsstrahlung, ionisation etc. with low-energy data.
  defaultCutValue = 1.0*um;

  RegisterPhysics(new G4EmLivermorePhysics());
  RegisterPhysics(new G4DecayPhysics());
  RegisterPhysics(new G4StepLimiterPhysics());
}

void PhysicsList::SetCuts()
{
  SetDefaultCutValue(defaultCutValue);
  SetCutsWithDefault();

  G4ProductionCutsTable::GetProductionCutsTable()->SetEnergyRange(100*eV, 100*GeV);
}
