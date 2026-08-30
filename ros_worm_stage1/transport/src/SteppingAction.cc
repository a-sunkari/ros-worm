#include "SteppingAction.hh"
#include "EventAction.hh"
#include "G4Step.hh"

SteppingAction::SteppingAction(EventAction* eventAction)
  : fEventAction(eventAction)
{
}

void SteppingAction::UserSteppingAction(const G4Step* step)
{
  fEventAction->AddStep(step);
}
