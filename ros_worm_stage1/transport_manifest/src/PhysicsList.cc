#include "PhysicsList.hh"
#include "G4DecayPhysics.hh"
#include "G4EmLivermorePhysics.hh"
#include "G4StepLimiterPhysics.hh"
#include "G4SystemOfUnits.hh"
#include "G4LossTableManager.hh"

PhysicsList::PhysicsList()
{
  SetDefaultCutValue(100*nm);
  RegisterPhysics(new G4DecayPhysics());
  RegisterPhysics(new G4EmLivermorePhysics());
  // G4UserLimits has no effect unless a step-limiter process is registered.
  // This limits charged-particle continuous-loss steps in biological volumes;
  // neutral discrete interactions are located at their post-step point.
  RegisterPhysics(new G4StepLimiterPhysics());
}
