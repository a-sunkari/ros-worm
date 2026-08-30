#ifndef CHEM6_PrimaryGeneratorAction_h
#define CHEM6_PrimaryGeneratorAction_h 1

#include "G4ParticleGun.hh"
#include "G4VUserPrimaryGeneratorAction.hh"
#include "globals.hh"

#include <vector>

class G4ParticleGun;
class G4Event;
class PrimarySourceConfig;

// Primary generator for the chemistry stage.
// Default behavior is unchanged from chem6: use the ordinary Geant4 /gun UI.
// Optional ROS-Worm mode samples electron energies from a CSV spectrum while
// keeping the same Geant4-DNA chemistry/scoring lifecycle.
class PrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction
{
public:
  explicit PrimaryGeneratorAction(const PrimarySourceConfig* sourceConfig = nullptr);
  ~PrimaryGeneratorAction() override;

  void GeneratePrimaries(G4Event*) override;
  const G4ParticleGun* GetParticleGun() const { return fParticleGun; }

private:
  void LoadSpectrumIfNeeded();
  G4double SampleSpectrumEnergy() const;

  G4ParticleGun* fParticleGun = nullptr;
  const PrimarySourceConfig* fSourceConfig = nullptr;

  G4bool fSpectrumLoaded = false;
  G4String fLoadedSpectrumFile;
  std::vector<G4double> fSpectrumEnergy;  // internal Geant4 energy units
  std::vector<G4double> fSpectrumCdf;     // cumulative normalized weights
};

#endif
