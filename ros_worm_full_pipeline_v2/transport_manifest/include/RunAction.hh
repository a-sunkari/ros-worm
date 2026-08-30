#ifndef ROS_WORM_MANIFEST_RUN_ACTION_HH
#define ROS_WORM_MANIFEST_RUN_ACTION_HH

#include "G4UserRunAction.hh"
class DetectorConstruction;
class G4Run;

class RunAction : public G4UserRunAction {
public:
  explicit RunAction(DetectorConstruction* det);
  ~RunAction() override = default;
  void BeginOfRunAction(const G4Run* run) override;
  void EndOfRunAction(const G4Run* run) override;
private:
  DetectorConstruction* fDetector = nullptr;
};

#endif
