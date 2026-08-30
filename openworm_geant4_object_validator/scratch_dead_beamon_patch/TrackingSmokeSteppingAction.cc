#include "TrackingSmokeSteppingAction.hh"

#include <G4Step.hh>
#include <G4Track.hh>
#include <G4VPhysicalVolume.hh>
#include <G4ios.hh>
#include <G4SystemOfUnits.hh>

void TrackingSmokeSteppingAction::UserSteppingAction(const G4Step* step) {
    const auto* track = step->GetTrack();
    const int tid = track->GetTrackID();

    int& n = stepCountByTrack_[tid];
    n++;

    const double stepLen = step->GetStepLength();

    if (n == 1) {
        auto* vol = track->GetVolume();
        G4cout << "[OPENWORM-VALIDATOR][TRACK_START]"
               << " track=" << tid
               << " particle=" << track->GetParticleDefinition()->GetParticleName()
               << " volume=" << (vol ? vol->GetName() : "NULL")
               << G4endl;
    }

    if (n % 10000 == 0 || stepLen == 0.0) {
        auto pre = step->GetPreStepPoint();
        auto post = step->GetPostStepPoint();
        auto* preVol = pre && pre->GetPhysicalVolume() ? pre->GetPhysicalVolume() : nullptr;
        auto* postVol = post && post->GetPhysicalVolume() ? post->GetPhysicalVolume() : nullptr;

        G4cout << "[OPENWORM-VALIDATOR][STEP_DIAG]"
               << " track=" << tid
               << " nstep=" << n
               << " stepLen_mm=" << stepLen/mm
               << " preVol=" << (preVol ? preVol->GetName() : "NULL")
               << " postVol=" << (postVol ? postVol->GetName() : "NULL")
               << " pos_mm=" << track->GetPosition()/mm
               << G4endl;
    }

    if (n > 200000) {
        G4cout << "[OPENWORM-VALIDATOR][KILL_TRACK_TOO_MANY_STEPS]"
               << " track=" << tid
               << " nstep=" << n
               << " pos_mm=" << track->GetPosition()/mm
               << G4endl;
        const_cast<G4Track*>(track)->SetTrackStatus(fStopAndKill);
    }
}
