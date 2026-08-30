#include "PrimaryGeneratorAction.hh"

#include "PrimarySourceConfig.hh"

#include "G4Event.hh"
#include "G4Exception.hh"
#include "G4ParticleDefinition.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4SystemOfUnits.hh"
#include "G4Threading.hh"
#include "Randomize.hh"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <sstream>
#include <string>

namespace
{
std::string Trim(const std::string& s)
{
  auto first = s.begin();
  while (first != s.end() && std::isspace(static_cast<unsigned char>(*first))) ++first;
  if (first == s.end()) return {};

  auto last = s.end();
  do {
    --last;
  } while (last != first && std::isspace(static_cast<unsigned char>(*last)));

  if (std::isspace(static_cast<unsigned char>(*last))) return {};
  return std::string(first, last + 1);
}

std::string NormalizeSeparators(std::string line)
{
  for (auto& c : line) {
    if (c == ',' || c == ';' || c == '\t') c = ' ';
  }
  return line;
}
}  // namespace

PrimaryGeneratorAction::PrimaryGeneratorAction(const PrimarySourceConfig* sourceConfig)
  : G4VUserPrimaryGeneratorAction(), fSourceConfig(sourceConfig)
{
  fParticleGun = new G4ParticleGun(1);

  auto* particleTable = G4ParticleTable::GetParticleTable();
  auto* particle = particleTable->FindParticle("e-");
  fParticleGun->SetParticleDefinition(particle);
  fParticleGun->SetParticlePosition(G4ThreeVector(0., 0., 0.));
  fParticleGun->SetParticleEnergy(100 * keV);
  fParticleGun->SetParticleMomentumDirection(G4ThreeVector(0., 0., 1.));
}

PrimaryGeneratorAction::~PrimaryGeneratorAction()
{
  delete fParticleGun;
}

void PrimaryGeneratorAction::LoadSpectrumIfNeeded()
{
  if (!fSourceConfig || fSourceConfig->GetMode() != "spectrum") return;

  const auto& filename = fSourceConfig->GetSpectrumFile();
  if (fSpectrumLoaded && fLoadedSpectrumFile == filename) return;

  std::ifstream in(filename.c_str());
  if (!in) {
    G4ExceptionDescription desc;
    desc << "Could not open spectrum file '" << filename << "'.\n"
         << "Expected CSV format: energy_keV,weight";
    G4Exception("PrimaryGeneratorAction::LoadSpectrumIfNeeded", "ROSWORMCHEM001",
                FatalException, desc);
  }

  std::vector<G4double> energies;
  std::vector<G4double> weights;

  std::string line;
  G4int lineNo = 0;
  while (std::getline(in, line)) {
    ++lineNo;
    line = Trim(line);
    if (line.empty() || line[0] == '#') continue;

    line = NormalizeSeparators(line);
    std::istringstream iss(line);
    G4double e_keV = 0.0;
    G4double weight = 0.0;
    if (!(iss >> e_keV >> weight)) {
      G4ExceptionDescription desc;
      desc << "Bad spectrum line " << lineNo << " in '" << filename << "': " << line;
      G4Exception("PrimaryGeneratorAction::LoadSpectrumIfNeeded", "ROSWORMCHEM002",
                  FatalException, desc);
    }
    if (e_keV <= 0.0 || weight <= 0.0) continue;
    energies.push_back(e_keV * keV);
    weights.push_back(weight);
  }

  if (energies.empty()) {
    G4ExceptionDescription desc;
    desc << "Spectrum file '" << filename << "' did not contain any positive energy/weight rows.";
    G4Exception("PrimaryGeneratorAction::LoadSpectrumIfNeeded", "ROSWORMCHEM003",
                FatalException, desc);
  }

  G4double total = 0.0;
  for (auto w : weights) total += w;
  if (total <= 0.0) {
    G4Exception("PrimaryGeneratorAction::LoadSpectrumIfNeeded", "ROSWORMCHEM004",
                FatalException, "Spectrum weights sum to zero.");
  }

  fSpectrumEnergy = energies;
  fSpectrumCdf.clear();
  fSpectrumCdf.reserve(weights.size());
  G4double running = 0.0;
  for (auto w : weights) {
    running += w / total;
    fSpectrumCdf.push_back(running);
  }
  fSpectrumCdf.back() = 1.0;
  fLoadedSpectrumFile = filename;
  fSpectrumLoaded = true;

  if (fSourceConfig->GetVerbose()) {
    G4cout << "[ROS-WORM-CHEM] Worker " << G4Threading::G4GetThreadId()
           << " loaded " << fSpectrumEnergy.size() << " spectrum bins from "
           << filename << G4endl;
  }
}

G4double PrimaryGeneratorAction::SampleSpectrumEnergy() const
{
  const G4double u = G4UniformRand();
  auto it = std::lower_bound(fSpectrumCdf.begin(), fSpectrumCdf.end(), u);
  const auto idx = static_cast<std::size_t>(std::distance(fSpectrumCdf.begin(), it));
  return fSpectrumEnergy[std::min(idx, fSpectrumEnergy.size() - 1)];
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* anEvent)
{
  if (fSourceConfig && fSourceConfig->GetMode() == "spectrum") {
    LoadSpectrumIfNeeded();
    fParticleGun->SetParticleEnergy(SampleSpectrumEnergy());
  }

  fParticleGun->GeneratePrimaryVertex(anEvent);
}
