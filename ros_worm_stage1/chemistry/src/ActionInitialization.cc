//
// This file intentionally preserves the working Geant4-DNA chem6 chemistry
// lifecycle.  The only ROS-Worm addition is a macro-owned source config object
// passed read-only to worker-local PrimaryGeneratorAction instances.
//

#include "ActionInitialization.hh"

#include "PrimaryGeneratorAction.hh"
#include "PrimarySourceConfig.hh"
#include "RunAction.hh"
#include "StackingAction.hh"
#include "TimeStepAction.hh"

#include "G4DNAChemistryManager.hh"
#include "G4H2O.hh"
#include "G4MoleculeCounter.hh"
#include "G4Scheduler.hh"
#include "G4Threading.hh"

ActionInitialization::ActionInitialization()
  : G4VUserActionInitialization(), fSourceConfig(new PrimarySourceConfig())
{}

ActionInitialization::~ActionInitialization()
{
  delete fSourceConfig;
}

void ActionInitialization::BuildForMaster() const
{
  SetUserAction(new RunAction());
  G4DNAChemistryManager::Instance()->ResetCounterWhenRunEnds(false);
}

void ActionInitialization::Build() const
{
  G4MoleculeCounter::Instance()->Use();
  G4MoleculeCounter::Instance()->DontRegister(G4H2O::Definition());

  // Same Geant4 11.3 chem6 behavior: in sequential mode the counter must not
  // be reset at run end before ScoreSpecies has read it.
  if (G4Threading::IsMultithreadedApplication() == false) {
    G4DNAChemistryManager::Instance()->ResetCounterWhenRunEnds(false);
  }

  SetUserAction(new PrimaryGeneratorAction(fSourceConfig));
  SetUserAction(new RunAction());
  SetUserAction(new StackingAction());
  G4Scheduler::Instance()->SetUserAction(new TimeStepAction());
}
