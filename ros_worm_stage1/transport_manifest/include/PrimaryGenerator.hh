#ifndef ROS_WORM_MANIFEST_PRIMARY_GENERATOR_HH
#define ROS_WORM_MANIFEST_PRIMARY_GENERATOR_HH

#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4ThreeVector.hh"
#include <vector>

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
  G4double SampleTabulatedEnergy();
  void LoadSpectrum();
  void BeamBasis(G4ThreeVector& u, G4ThreeVector& v, G4ThreeVector& direction) const;
  const DetectorConstruction* fDetector = nullptr;
  G4ParticleGun* fGun = nullptr;
  bool fSpectrumLoaded = false;
  std::vector<G4double> fSpectrumEnergy;
  std::vector<G4double> fSpectrumCdf;
};

#endif
