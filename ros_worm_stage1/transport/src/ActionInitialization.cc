#include "ActionInitialization.hh"

#include "DetectorConstruction.hh"
#include "PrimaryGenerator.hh"
#include "RunAction.hh"
#include "EventAction.hh"
#include "SteppingAction.hh"

ActionInitialization::ActionInitialization(DetectorConstruction* detector)
  : fDetector(detector)
{
}

void ActionInitialization::BuildForMaster() const
{
  SetUserAction(new RunAction());
}

void ActionInitialization::Build() const
{
  SetUserAction(new PrimaryGenerator(fDetector));
  SetUserAction(new RunAction());

  auto* eventAction = new EventAction(fDetector);
  SetUserAction(eventAction);
  SetUserAction(new SteppingAction(eventAction));
}
