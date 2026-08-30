#ifndef ROS_WORM_MANIFEST_EVENT_ACTION_HH
#define ROS_WORM_MANIFEST_EVENT_ACTION_HH

#include "G4UserEventAction.hh"
#include "globals.hh"
#include <array>

class DetectorConstruction;
class G4Event;
class G4Step;

class EventAction : public G4UserEventAction {
public:
  explicit EventAction(DetectorConstruction* det);
  ~EventAction() override = default;
  void BeginOfEventAction(const G4Event* event) override;
  void EndOfEventAction(const G4Event* event) override;
  void AddStep(const G4Step* step);
private:
  G4double Dose(G4double edep, G4double mass) const;
  DetectorConstruction* fDetector = nullptr;
  G4int fEventID = -1;
  std::array<G4double, 16> fEdep{};
};

#endif
