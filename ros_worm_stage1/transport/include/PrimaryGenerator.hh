#ifndef PRIMARY_GENERATOR_HH
#define PRIMARY_GENERATOR_HH

#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4SystemOfUnits.hh"
#include "globals.hh"
#include "G4ThreeVector.hh"

class G4ParticleGun;
class G4Event;
class DetectorConstruction;

class PrimaryGenerator : public G4VUserPrimaryGeneratorAction
{
public:
  explicit PrimaryGenerator(const DetectorConstruction* detector);
  ~PrimaryGenerator() override;

  void GeneratePrimaries(G4Event* event) override;

private:
  G4double SampleKramersEnergy() const;
  G4ThreeVector SampleDirectionInCone() const;

  const DetectorConstruction* fDetector = nullptr;
  G4ParticleGun* fParticleGun = nullptr;
};

#endif
