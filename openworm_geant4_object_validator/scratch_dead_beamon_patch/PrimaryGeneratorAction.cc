#include "PrimaryGeneratorAction.hh"

#include <G4Event.hh>
#include <G4ParticleTable.hh>
#include <G4ParticleDefinition.hh>
#include <G4SystemOfUnits.hh>
#include <G4ios.hh>
#include <stdexcept>

PrimaryGeneratorAction::PrimaryGeneratorAction(const ValidatorConfig& cfg)
    : cfg_(cfg)
{
    gun_ = new G4ParticleGun(1);

    auto* table = G4ParticleTable::GetParticleTable();
    auto* particle = table->FindParticle(cfg_.particleName);

    if (!particle) {
        throw std::runtime_error("Unknown particle name for --particle: " + cfg_.particleName);
    }

    G4ThreeVector dir = cfg_.sourceDir;
    if (dir.mag2() == 0.0) {
        throw std::runtime_error("--dir vector cannot be zero");
    }
    dir = dir.unit();

    gun_->SetParticleDefinition(particle);
    gun_->SetParticleEnergy(cfg_.energyMeV * MeV);
    gun_->SetParticlePosition(cfg_.sourcePosMM * mm);
    gun_->SetParticleMomentumDirection(dir);

    G4cout << "[OPENWORM-VALIDATOR][PRIMARY]"
           << " particle=" << cfg_.particleName
           << " energyMeV=" << cfg_.energyMeV
           << " src_mm=" << cfg_.sourcePosMM
           << " dir=" << dir
           << G4endl;
}

PrimaryGeneratorAction::~PrimaryGeneratorAction() {
    delete gun_;
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event) {
    gun_->GeneratePrimaryVertex(event);
}
