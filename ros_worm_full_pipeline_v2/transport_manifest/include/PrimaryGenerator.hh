#ifndef ROS_WORM_MANIFEST_PRIMARY_GENERATOR_HH
#define ROS_WORM_MANIFEST_PRIMARY_GENERATOR_HH

#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4ThreeVector.hh"

class DetectorConstruction;
class G4Event;
class G4ParticleGun;

class PrimaryGenerator : public G4VUserPrimaryGeneratorAction {
public:
  explicit PrimaryGenerator(const DetectorConstruction* det);
  ~PrimaryGenerator() override;
  void GeneratePrimaries(G4Event* event) override;

private:
  G4double SampleKramersEnergy() const;
  const DetectorConstruction* fDetector = nullptr;
  G4ParticleGun* fGun = nullptr;
};

#endif
