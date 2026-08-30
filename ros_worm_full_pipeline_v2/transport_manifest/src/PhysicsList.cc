#include "PhysicsList.hh"
#include "G4DecayPhysics.hh"
#include "G4EmLivermorePhysics.hh"
#include "G4SystemOfUnits.hh"
#include "G4LossTableManager.hh"

PhysicsList::PhysicsList()
{
  SetDefaultCutValue(100*nm);
  RegisterPhysics(new G4DecayPhysics());
  RegisterPhysics(new G4EmLivermorePhysics());
}
