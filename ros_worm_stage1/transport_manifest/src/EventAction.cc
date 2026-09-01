#include "EventAction.hh"
#include "DetectorConstruction.hh"
#include "G4AnalysisManager.hh"
#include "G4Event.hh"
#include "G4Step.hh"
#include "G4Track.hh"
#include "G4VPhysicalVolume.hh"
#include "G4VProcess.hh"
#include "G4ParticleDefinition.hh"
#include "G4SystemOfUnits.hh"
#include <cmath>

EventAction::EventAction(DetectorConstruction* det) : fDetector(det) {}

G4double EventAction::Dose(G4double edep, G4double mass) const
{
  return mass > 0.0 ? (edep/mass)/gray : 0.0;
}

void EventAction::BeginOfEventAction(const G4Event* event)
{
  fEventID = event->GetEventID();
  fEdep.fill(0.0);
}

void EventAction::AddStep(const G4Step* step)
{
  auto* pre = step->GetPreStepPoint();
  auto* vol = pre->GetTouchableHandle()->GetVolume();
  if (!vol) return;
  const auto regionID = fDetector->RegionIdFromPhysicalName(vol->GetName());
  if (regionID <= 0 || regionID >= static_cast<G4int>(fEdep.size())) return;

  const auto edep = step->GetTotalEnergyDeposit();
  fEdep[regionID] += edep;

  auto* man = G4AnalysisManager::Instance();
  auto* track = step->GetTrack();
  const auto* particle = track->GetParticleDefinition();
  const auto pdg = particle->GetPDGEncoding();
  const auto ekin = pre->GetKineticEnergy();

  if (std::abs(pdg) == 11) man->FillH1(1, ekin/keV);
  if (pdg == 22) man->FillH1(2, ekin/keV);

  const auto prePos = pre->GetPosition();
  if (fDetector->GetSaveSteps() && edep > 0.0) {
    const auto* post = step->GetPostStepPoint();
    const auto postPos = post->GetPosition();
    const auto midPos = 0.5 * (prePos + postPos);
    const auto* process = post->GetProcessDefinedStep();
    const auto* creatorProcess = track->GetCreatorProcess();
    man->FillNtupleIColumn(1, 0, fEventID);
    man->FillNtupleIColumn(1, 1, regionID);
    man->FillNtupleIColumn(1, 2, pdg);
    man->FillNtupleIColumn(1, 3, track->GetTrackID());
    man->FillNtupleIColumn(1, 4, track->GetParentID());
    man->FillNtupleDColumn(1, 5, edep/keV);
    man->FillNtupleDColumn(1, 6, ekin/keV);
    man->FillNtupleDColumn(1, 7, step->GetStepLength()/um);
    man->FillNtupleDColumn(1, 8, prePos.x()/um);
    man->FillNtupleDColumn(1, 9, prePos.y()/um);
    man->FillNtupleDColumn(1, 10, prePos.z()/um);
    man->FillNtupleDColumn(1, 11, prePos.x()/um);
    man->FillNtupleDColumn(1, 12, prePos.y()/um);
    man->FillNtupleDColumn(1, 13, prePos.z()/um);
    man->FillNtupleDColumn(1, 14, midPos.x()/um);
    man->FillNtupleDColumn(1, 15, midPos.y()/um);
    man->FillNtupleDColumn(1, 16, midPos.z()/um);
    man->FillNtupleDColumn(1, 17, postPos.x()/um);
    man->FillNtupleDColumn(1, 18, postPos.y()/um);
    man->FillNtupleDColumn(1, 19, postPos.z()/um);
    man->FillNtupleIColumn(1, 20, fDetector->IsInsideBody(prePos) ? 1 : 0);
    man->FillNtupleIColumn(1, 21, fDetector->IsInsideBody(midPos) ? 1 : 0);
    man->FillNtupleIColumn(1, 22, fDetector->IsInsideBody(postPos) ? 1 : 0);
    man->FillNtupleIColumn(1, 23, process ? process->GetProcessType() : -1);
    man->FillNtupleIColumn(1, 24, process ? process->GetProcessSubType() : -1);
    man->FillNtupleIColumn(1, 25, creatorProcess ? creatorProcess->GetProcessType() : -1);
    man->FillNtupleIColumn(1, 26, creatorProcess ? creatorProcess->GetProcessSubType() : -1);
    man->AddNtupleRow(1);
  }

  const auto* secs = step->GetSecondaryInCurrentStep();
  if (secs) {
    for (const auto* sec : *secs) {
      const auto* sd = sec->GetParticleDefinition();
      const auto spdg = sd->GetPDGEncoding();
      const auto spos = sec->GetPosition();
      const auto postPos = step->GetPostStepPoint()->GetPosition();
      const auto insideBody = fDetector->IsInsideBody(spos);
      man->FillNtupleIColumn(2, 0, fEventID);
      man->FillNtupleIColumn(2, 1, regionID);
      man->FillNtupleIColumn(2, 2, pdg);
      man->FillNtupleIColumn(2, 3, spdg);
      man->FillNtupleDColumn(2, 4, sec->GetKineticEnergy()/keV);
      man->FillNtupleDColumn(2, 5, spos.x()/um);
      man->FillNtupleDColumn(2, 6, spos.y()/um);
      man->FillNtupleDColumn(2, 7, spos.z()/um);
      man->FillNtupleIColumn(2, 8, insideBody ? 1 : 0);
      man->FillNtupleDColumn(2, 9, step->GetStepLength()/um);
      man->FillNtupleDColumn(2, 10, prePos.x()/um);
      man->FillNtupleDColumn(2, 11, prePos.y()/um);
      man->FillNtupleDColumn(2, 12, prePos.z()/um);
      man->FillNtupleDColumn(2, 13, postPos.x()/um);
      man->FillNtupleDColumn(2, 14, postPos.y()/um);
      man->FillNtupleDColumn(2, 15, postPos.z()/um);
      man->AddNtupleRow(2);
    }
  }
}

void EventAction::EndOfEventAction(const G4Event* event)
{
  G4double total = 0.0;
  for (G4int i=1;i<=6;++i) total += fEdep[i];
  auto* man = G4AnalysisManager::Instance();
  man->FillH1(0, total/keV);
  man->FillNtupleIColumn(0, 0, event->GetEventID());
  man->FillNtupleDColumn(0, 1, fEdep[1]/keV);
  man->FillNtupleDColumn(0, 2, fEdep[2]/keV);
  man->FillNtupleDColumn(0, 3, fEdep[3]/keV);
  man->FillNtupleDColumn(0, 4, fEdep[4]/keV);
  man->FillNtupleDColumn(0, 5, fEdep[5]/keV);
  man->FillNtupleDColumn(0, 6, fEdep[6]/keV);
  man->FillNtupleDColumn(0, 7, total/keV);
  man->AddNtupleRow(0);
}
