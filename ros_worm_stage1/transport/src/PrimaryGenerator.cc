#include "PrimaryGenerator.hh"
#include "DetectorConstruction.hh"

#include "G4ParticleGun.hh"
#include "G4Gamma.hh"
#include "G4Event.hh"
#include "G4PhysicalConstants.hh"
#include "Randomize.hh"

#include <cmath>
#include <algorithm>

PrimaryGenerator::PrimaryGenerator(const DetectorConstruction* detector)
  : fDetector(detector)
{
  fParticleGun = new G4ParticleGun(1);
  fParticleGun->SetParticleDefinition(G4Gamma::GammaDefinition());
}

PrimaryGenerator::~PrimaryGenerator()
{
  delete fParticleGun;
}

G4double PrimaryGenerator::SampleKramersEnergy() const
{
  const auto kvp = fDetector->GetKvp();
  const auto emin = fDetector->GetMinEnergy();

  // Rejection sample rough Kramers fluence shape: N(E) ~ (E0 - E)/E.
  // This is a placeholder until measured/vendor/SpekPy spectra are used.
  for (;;) {
    const G4double e = emin + (kvp - emin)*G4UniformRand();
    const G4double y = ((kvp - e)/e) / ((kvp - emin)/emin);
    if (G4UniformRand() < y) return e;
  }
}

G4ThreeVector PrimaryGenerator::SampleDirectionInCone() const
{
  const auto halfAngle = fDetector->GetConeHalfAngle();
  const G4double cosMin = std::cos(halfAngle);
  const G4double cosTheta = 1.0 - (1.0 - cosMin)*G4UniformRand();
  const G4double sinTheta = std::sqrt(std::max(0.0, 1.0 - cosTheta*cosTheta));
  const G4double phi = twopi * G4UniformRand();
  return G4ThreeVector(sinTheta*std::cos(phi), sinTheta*std::sin(phi), -cosTheta).unit();
}

void PrimaryGenerator::GeneratePrimaries(G4Event* event)
{
  const G4double energy = (fDetector->GetSpectrumType() == "mono")
                        ? fDetector->GetMonoEnergy()
                        : SampleKramersEnergy();
  fParticleGun->SetParticleEnergy(energy);

  if (fDetector->GetSourceType() == "diffuse") {
    fParticleGun->SetParticlePosition(G4ThreeVector(0, 0, fDetector->GetSourceZ()));
    fParticleGun->SetParticleMomentumDirection(SampleDirectionInCone());
  } else {
    // Focused approximation: sample a Gaussian beam spot at the worm plane and
    // aim from source z toward that point.
    const G4double sigma = fDetector->GetSpotFWHM() / 2.354820045;
    const G4double x = G4RandGauss::shoot(0.0, sigma);
    const G4double y = G4RandGauss::shoot(0.0, sigma);
    const G4ThreeVector src(0, 0, fDetector->GetSourceZ());
    const G4ThreeVector target(x, y, fDetector->GetWormRadius());
    fParticleGun->SetParticlePosition(src);
    fParticleGun->SetParticleMomentumDirection((target - src).unit());
  }

  fParticleGun->GeneratePrimaryVertex(event);
}
