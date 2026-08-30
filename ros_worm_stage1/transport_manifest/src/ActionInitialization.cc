#include "ActionInitialization.hh"
#include "DetectorConstruction.hh"
#include "PrimaryGenerator.hh"
#include "RunAction.hh"
#include "EventAction.hh"
#include "SteppingAction.hh"

void ActionInitialization::BuildForMaster() const
{
  SetUserAction(new RunAction(fDetector));
}

void ActionInitialization::Build() const
{
  SetUserAction(new PrimaryGenerator(fDetector));
  SetUserAction(new RunAction(fDetector));
  auto* eventAction = new EventAction(fDetector);
  SetUserAction(eventAction);
  SetUserAction(new SteppingAction(eventAction));
}
