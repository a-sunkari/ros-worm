#include "SmokeActionInitialization.hh"

#include <G4Event.hh>
#include <G4ParticleDefinition.hh>
#include <G4ParticleGun.hh>
#include <G4ParticleTable.hh>
#include <G4Run.hh>
#include <G4UserRunAction.hh>
#include <G4VUserPrimaryGeneratorAction.hh>
#include <G4UserSteppingAction.hh>
#include <G4Step.hh>
#include <G4SystemOfUnits.hh>
#include <G4ThreeVector.hh>
#include <G4VPhysicalVolume.hh>
#include <G4ios.hh>

#include <map>
#include <random>
#include <string>

namespace {

struct SmokeStats {
    std::map<std::string, long long> stepCounts;
    std::map<std::string, double> edepKeV;
    long long totalSteps = 0;
    double totalEdepKeV = 0.0;

    void Reset() {
        stepCounts.clear();
        edepKeV.clear();
        totalSteps = 0;
        totalEdepKeV = 0.0;
    }
};

SmokeStats gSmokeStats;

class SmokePrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction {
public:
    explicit SmokePrimaryGeneratorAction(const ValidatorConfig& cfg)
        : cfg_(cfg), rng_(cfg.smokeSeed) {
        gun_ = new G4ParticleGun(1);

        auto* table = G4ParticleTable::GetParticleTable();
        auto* particle = table->FindParticle(cfg_.smokeParticle);
        if (!particle) {
            G4cout << "[OPENWORM-VALIDATOR][SMOKE_WARN] unknown particle '"
                   << cfg_.smokeParticle << "', falling back to gamma" << G4endl;
            particle = table->FindParticle("gamma");
        }

        gun_->SetParticleDefinition(particle);
        gun_->SetParticleEnergy(cfg_.smokeEnergyKeV * keV);

        G4cout << "[OPENWORM-VALIDATOR][SMOKE_SOURCE] "
               << "particle=" << particle->GetParticleName()
               << " energy_keV=" << cfg_.smokeEnergyKeV
               << " source_y_um=" << cfg_.smokeSourceYUm
               << " half_x_um=" << cfg_.smokeHalfXUm
               << " half_z_um=" << cfg_.smokeHalfZUm
               << " seed=" << cfg_.smokeSeed
               << G4endl;
    }

    ~SmokePrimaryGeneratorAction() override {
        delete gun_;
    }

    void GeneratePrimaries(G4Event* event) override {
        std::uniform_real_distribution<double> ux(-cfg_.smokeHalfXUm, cfg_.smokeHalfXUm);
        std::uniform_real_distribution<double> uz(-cfg_.smokeHalfZUm, cfg_.smokeHalfZUm);

        const double x = ux(rng_) * 0.001 * mm; // um -> mm
        const double y = cfg_.smokeSourceYUm * 0.001 * mm;
        const double z = uz(rng_) * 0.001 * mm;

        gun_->SetParticlePosition(G4ThreeVector(x, y, z));
        gun_->SetParticleMomentumDirection(G4ThreeVector(0.0, 1.0, 0.0));
        gun_->GeneratePrimaryVertex(event);
    }

private:
    ValidatorConfig cfg_;
    G4ParticleGun* gun_ = nullptr;
    std::mt19937 rng_;
};

class SmokeRunAction : public G4UserRunAction {
public:
    explicit SmokeRunAction(const ValidatorConfig& cfg) : cfg_(cfg) {}

    void BeginOfRunAction(const G4Run* run) override {
        gSmokeStats.Reset();
        G4cout << "[OPENWORM-VALIDATOR][SMOKE_RUN_BEGIN] "
               << "runID=" << run->GetRunID()
               << " events=" << cfg_.smokeRunCount
               << G4endl;
    }

    void EndOfRunAction(const G4Run* run) override {
        G4cout << "[OPENWORM-VALIDATOR][SMOKE_RUN_END] "
               << "runID=" << run->GetRunID()
               << " events=" << run->GetNumberOfEvent()
               << " totalSteps=" << gSmokeStats.totalSteps
               << " totalEdep_keV=" << gSmokeStats.totalEdepKeV
               << G4endl;

        G4cout << "[OPENWORM-VALIDATOR][SMOKE_STEP_VOLUME_COUNTS]" << G4endl;
        for (const auto& kv : gSmokeStats.stepCounts) {
            G4cout << "  " << kv.first << " " << kv.second << G4endl;
        }

        G4cout << "[OPENWORM-VALIDATOR][SMOKE_EDEP_BY_VOLUME_KEV]" << G4endl;
        for (const auto& kv : gSmokeStats.edepKeV) {
            G4cout << "  " << kv.first << " " << kv.second << G4endl;
        }
    }

private:
    ValidatorConfig cfg_;
};

class SmokeSteppingAction : public G4UserSteppingAction {
public:
    void UserSteppingAction(const G4Step* step) override {
        auto* pre = step->GetPreStepPoint();
        if (!pre) return;

        std::string volName = "UNKNOWN";
        auto* volume = pre->GetPhysicalVolume();
        if (volume) {
            volName = volume->GetName();
        }

        const double edep = step->GetTotalEnergyDeposit() / keV;

        gSmokeStats.totalSteps++;
        gSmokeStats.stepCounts[volName]++;

        if (edep > 0.0) {
            gSmokeStats.totalEdepKeV += edep;
            gSmokeStats.edepKeV[volName] += edep;
        }
    }
};

} // namespace

SmokeActionInitialization::SmokeActionInitialization(const ValidatorConfig& cfg)
    : cfg_(cfg) {}

void SmokeActionInitialization::Build() const {
    SetUserAction(new SmokePrimaryGeneratorAction(cfg_));
    SetUserAction(new SmokeRunAction(cfg_));
    SetUserAction(new SmokeSteppingAction());
}
