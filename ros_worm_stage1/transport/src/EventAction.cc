#include "EventAction.hh"

#include "DetectorConstruction.hh"

#include "G4AnalysisManager.hh"
#include "G4Event.hh"
#include "G4Step.hh"
#include "G4VPhysicalVolume.hh"
#include "G4Track.hh"
#include "G4ParticleDefinition.hh"
#include "G4SystemOfUnits.hh"
#include <cmath>

EventAction::EventAction(DetectorConstruction* detector)
  : fDetector(detector)
{

}

EventAction::~EventAction()
{}

void EventAction::BeginOfEventAction(const G4Event* event)
{
  fEventID = event->GetEventID();
  fEdepWorm = 0.0;
  fEdepHead = 0.0;
  fEdepVNC = 0.0;
  fEdepBodyWall = 0.0;
  fEdepIntestine = 0.0;
  fEdepAgar = 0.0;
}

G4int EventAction::RegionIDFromVolumeName(const G4String& name) const
{
  if (name == "worm_phys") return 1;
  if (name == "head_roi_phys") return 2;
  if (name == "vnc_roi_phys") return 3;
  if (name == "body_wall_roi_phys") return 4;
  if (name == "intestine_roi_phys") return 5;
  if (name == "agar_phys") return 6;
  return 0;
}

G4bool EventAction::IsWormRegion(G4int regionID) const
{
  return (regionID >= 1 && regionID <= 5);
}

G4double EventAction::Dose(G4double edep, G4double mass) const
{
  if (mass <= 0.0) return 0.0;
  return (edep / mass) / gray;
}

void EventAction::AddStep(const G4Step* step)
{
  auto* pre = step->GetPreStepPoint();
  auto* volume = pre->GetTouchableHandle()->GetVolume();
  if (!volume) return;

  const auto regionID = RegionIDFromVolumeName(volume->GetName());
  if (regionID == 0) return;

  const auto edep = step->GetTotalEnergyDeposit();

  if (regionID == 1) fEdepWorm += edep;
  if (regionID == 2) fEdepHead += edep;
  if (regionID == 3) fEdepVNC += edep;
  if (regionID == 4) fEdepBodyWall += edep;
  if (regionID == 5) fEdepIntestine += edep;
  if (regionID == 6) fEdepAgar += edep;

  // Daughter ROI volumes replace the mother material, so include their edep in
  // total worm edep as well.
  if (regionID >= 2 && regionID <= 5) fEdepWorm += edep;

  auto* man = G4AnalysisManager::Instance();
  const auto* particle = step->GetTrack()->GetParticleDefinition();
  const auto pdg = particle->GetPDGEncoding();
  const auto ekin = pre->GetKineticEnergy();

  if (IsWormRegion(regionID)) {
    if (std::abs(pdg) == 11) man->FillH1(2, ekin/keV);
    if (pdg == 22) man->FillH1(3, ekin/keV);
  }

  if (fDetector->GetSaveSteps() && IsWormRegion(regionID) && edep > 0.0) {
    const auto pos = pre->GetPosition();
    man->FillNtupleIColumn(1, 0, fEventID);
    man->FillNtupleIColumn(1, 1, regionID);
    man->FillNtupleIColumn(1, 2, pdg);
    man->FillNtupleDColumn(1, 3, edep/keV);
    man->FillNtupleDColumn(1, 4, ekin/keV);
    man->FillNtupleDColumn(1, 5, pos.x()/um);
    man->FillNtupleDColumn(1, 6, pos.y()/um);
    man->FillNtupleDColumn(1, 7, pos.z()/um);
    man->AddNtupleRow(1);
  }
}

void EventAction::EndOfEventAction(const G4Event* event)
{
  auto* man = G4AnalysisManager::Instance();

  const auto doseWorm = Dose(fEdepWorm, fDetector->GetWormMass());
  const auto doseHead = Dose(fEdepHead, fDetector->GetHeadMass());
  const auto doseVNC = Dose(fEdepVNC, fDetector->GetVNCMass());
  const auto doseBodyWall = Dose(fEdepBodyWall, fDetector->GetBodyWallMass());
  const auto doseIntestine = Dose(fEdepIntestine, fDetector->GetIntestineMass());

  man->FillH1(0, fEdepWorm/keV);
  man->FillH1(1, doseWorm);

  man->FillNtupleIColumn(0, 0, event->GetEventID());
  man->FillNtupleDColumn(0, 1, fEdepWorm/keV);
  man->FillNtupleDColumn(0, 2, fEdepHead/keV);
  man->FillNtupleDColumn(0, 3, fEdepVNC/keV);
  man->FillNtupleDColumn(0, 4, fEdepBodyWall/keV);
  man->FillNtupleDColumn(0, 5, fEdepIntestine/keV);
  man->FillNtupleDColumn(0, 6, fEdepAgar/keV);
  man->FillNtupleDColumn(0, 7, doseWorm);
  man->FillNtupleDColumn(0, 8, doseHead);
  man->FillNtupleDColumn(0, 9, doseVNC);
  man->FillNtupleDColumn(0, 10, doseBodyWall);
  man->FillNtupleDColumn(0, 11, doseIntestine);
  man->AddNtupleRow(0);
}
