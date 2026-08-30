#include "SteppingAction.hh"
#include "EventAction.hh"
#include "G4Step.hh"
void SteppingAction::UserSteppingAction(const G4Step* step) { fEventAction->AddStep(step); }
