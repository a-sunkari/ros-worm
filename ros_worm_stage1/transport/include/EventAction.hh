#ifndef EVENT_ACTION_HH
#define EVENT_ACTION_HH

#include "G4UserEventAction.hh"
#include "G4SystemOfUnits.hh"
#include "globals.hh"

class DetectorConstruction;
class G4Event;
class G4Step;

class EventAction : public G4UserEventAction
{
public:
  explicit EventAction(DetectorConstruction* detector);
  ~EventAction() override;

  void BeginOfEventAction(const G4Event* event) override;
  void EndOfEventAction(const G4Event* event) override;

  void AddStep(const G4Step* step);

private:
  G4int RegionIDFromVolumeName(const G4String& name) const;
  G4bool IsWormRegion(G4int regionID) const;
  G4double Dose(G4double edep, G4double mass) const;

  DetectorConstruction* fDetector = nullptr;
  G4int fEventID = -1;

  G4double fEdepWorm = 0.0;
  G4double fEdepHead = 0.0;
  G4double fEdepVNC = 0.0;
  G4double fEdepBodyWall = 0.0;
  G4double fEdepIntestine = 0.0;
  G4double fEdepAgar = 0.0;
};

#endif
