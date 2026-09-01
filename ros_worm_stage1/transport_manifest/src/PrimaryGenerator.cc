#include "PrimaryGenerator.hh"
#include "DetectorConstruction.hh"
#include "G4Event.hh"
#include "G4Gamma.hh"
#include "G4ParticleGun.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <sstream>
#include <stdexcept>

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

void PrimaryGenerator::LoadSpectrum()
{
  if (fSpectrumLoaded) return;
  std::ifstream input(fDetector->GetSpectrumFile());
  if (!input) G4Exception("PrimaryGenerator::LoadSpectrum","ROSWORM_SPECTRUM_OPEN",FatalException,
                          ("Cannot open spectrum: "+fDetector->GetSpectrumFile()).c_str());
  std::vector<G4double> weights; std::string line;
  while (std::getline(input,line)) {
    if (line.empty() || line[0]=='#') continue;
    std::replace(line.begin(),line.end(),',',' ');
    std::istringstream row(line); G4double energy=0, weight=0;
    if (!(row>>energy>>weight)) continue; // permits a text header
    if (energy>0 && weight>0) { fSpectrumEnergy.push_back(energy*keV); weights.push_back(weight); }
  }
  if (weights.empty()) G4Exception("PrimaryGenerator::LoadSpectrum","ROSWORM_SPECTRUM_EMPTY",FatalException,
                                   "No positive energy/weight rows");
  G4double total=0; for (auto weight:weights) total+=weight;
  G4double cumulative=0; for (auto weight:weights) { cumulative+=weight/total; fSpectrumCdf.push_back(cumulative); }
  fSpectrumCdf.back()=1.0; fSpectrumLoaded=true;
  G4cout << "[ROS-WORM][SOURCE] loaded_spectrum=" << fDetector->GetSpectrumFile()
         << " bins=" << fSpectrumEnergy.size() << G4endl;
}

G4double PrimaryGenerator::SampleTabulatedEnergy()
{
  LoadSpectrum(); const auto value=G4UniformRand();
  auto it=std::lower_bound(fSpectrumCdf.begin(),fSpectrumCdf.end(),value);
  return fSpectrumEnergy[std::min<std::size_t>(std::distance(fSpectrumCdf.begin(),it),fSpectrumEnergy.size()-1)];
}

void PrimaryGenerator::BeamBasis(G4ThreeVector& u, G4ThreeVector& v, G4ThreeVector& direction) const
{
  direction=fDetector->GetSourceDirection();
  if (direction.mag2()==0) G4Exception("PrimaryGenerator::BeamBasis","ROSWORM_DIRECTION",FatalException,"Zero beam direction");
  direction=direction.unit();
  const G4ThreeVector helper=std::abs(direction.z())<0.9 ? G4ThreeVector(0,0,1) : G4ThreeVector(0,1,0);
  u=direction.cross(helper).unit(); v=direction.cross(u).unit();
}

void PrimaryGenerator::GeneratePrimaries(G4Event* event)
{
  G4double energy=SampleKramersEnergy();
  if (fDetector->GetSpectrumType()=="mono") energy=fDetector->GetMonoEnergy();
  else if (fDetector->GetSpectrumType()=="tabulated") energy=SampleTabulatedEnergy();
  fGun->SetParticleEnergy(energy);

  G4ThreeVector u,v,direction; BeamBasis(u,v,direction);
  G4ThreeVector position=fDetector->GetSourcePosition();
  if (fDetector->GetSourceType()=="targeted_cone") {
    const auto target=fDetector->GetTargetPosition()
      +(2.0*G4UniformRand()-1.0)*fDetector->GetHalfX()*u
      +(2.0*G4UniformRand()-1.0)*fDetector->GetHalfZ()*v;
    direction=(target-position).unit();
  } else if (fDetector->GetSourceType() == "diffuse" || fDetector->GetSourceType()=="uniform_parallel") {
    position+=(2.0*G4UniformRand()-1.0)*fDetector->GetHalfX()*u
             +(2.0*G4UniformRand()-1.0)*fDetector->GetHalfZ()*v;
  } else {
    const auto sigma = fDetector->GetSpotFWHM()/2.354820045;
    position+=G4RandGauss::shoot(0.0,sigma)*u+G4RandGauss::shoot(0.0,sigma)*v;
  }
  fGun->SetParticlePosition(position);
  fGun->SetParticleMomentumDirection(direction);
  fGun->GeneratePrimaryVertex(event);
}
