#include "PrimaryGenerator.hh"
#include "DetectorConstruction.hh"
#include "G4Event.hh"
#include "G4Gamma.hh"
#include "G4ParticleGun.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"
#include <algorithm>
#include <cmath>

PrimaryGenerator::PrimaryGenerator(const DetectorConstruction* det) : fDetector(det)
{
  fGun = new G4ParticleGun(1);
  fGun->SetParticleDefinition(G4Gamma::GammaDefinition());
}
PrimaryGenerator::~PrimaryGenerator() { delete fGun; }

G4double PrimaryGenerator::SampleKramersEnergy() const
{
  const auto e0 = fDetector->GetKvp();
  const auto emin = std::max(0.1*keV, fDetector->GetMinEnergy());
  for (;;) {
    const G4double e = emin + (e0 - emin)*G4UniformRand();
    const G4double y = ((e0 - e)/e) / ((e0 - emin)/emin);
    if (G4UniformRand() < y) return e;
  }
}

void PrimaryGenerator::GeneratePrimaries(G4Event* event)
{
  const auto energy = (fDetector->GetSpectrumType() == "mono") ? fDetector->GetMonoEnergy() : SampleKramersEnergy();
  fGun->SetParticleEnergy(energy);

  const auto y0 = fDetector->GetSourceY();
  G4double x = 0.0, z = 0.0;
  if (fDetector->GetSourceType() == "diffuse") {
    x = (2.0*G4UniformRand() - 1.0)*fDetector->GetHalfX();
    z = (2.0*G4UniformRand() - 1.0)*fDetector->GetHalfZ();
  } else {
    const auto sigma = fDetector->GetSpotFWHM()/2.354820045;
    x = G4RandGauss::shoot(0.0, sigma);
    z = G4RandGauss::shoot(0.0, sigma);
  }
  fGun->SetParticlePosition(G4ThreeVector(x, y0, z));
  fGun->SetParticleMomentumDirection(G4ThreeVector(0, 1, 0));
  fGun->GeneratePrimaryVertex(event);
}
