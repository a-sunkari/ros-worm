#include "RunAction.hh"
#include "DetectorConstruction.hh"
#include "G4AnalysisManager.hh"
#include "G4Run.hh"
#include "G4SystemOfUnits.hh"
#include <sstream>

RunAction::RunAction(DetectorConstruction* det) : fDetector(det)
{
  auto* man = G4AnalysisManager::Instance();
  man->SetVerboseLevel(1);
  man->SetNtupleMerging(true);
  man->CreateH1("Edep_total_keV", "Total edep in all worm compartments per event", 200, 0., 200.);
  man->CreateH1("Electron_Epre_keV", "Pre-step electron kinetic energy in worm compartments", 300, 0., 100.);
  man->CreateH1("Gamma_Epre_keV", "Pre-step gamma kinetic energy in worm compartments", 300, 0., 100.);

  man->CreateNtuple("event", "Per-event compartment edep");
  man->CreateNtupleIColumn("eventID");
  man->CreateNtupleDColumn("Edep_body_keV");
  man->CreateNtupleDColumn("Edep_nervous_keV");
  man->CreateNtupleDColumn("Edep_bodywall_keV");
  man->CreateNtupleDColumn("Edep_digestive_keV");
  man->CreateNtupleDColumn("Edep_reproductive_keV");
  man->CreateNtupleDColumn("Edep_excretory_keV");
  man->CreateNtupleDColumn("Edep_total_worm_keV");
  man->FinishNtuple(0);

  man->CreateNtuple("steps", "Per-step edep rows in worm compartments");
  man->CreateNtupleIColumn("eventID");
  man->CreateNtupleIColumn("regionID");
  man->CreateNtupleIColumn("pdg");
  man->CreateNtupleIColumn("trackID");
  man->CreateNtupleIColumn("parentID");
  man->CreateNtupleDColumn("edep_keV");
  man->CreateNtupleDColumn("ekin_pre_keV");
  man->CreateNtupleDColumn("step_um");
  man->CreateNtupleDColumn("x_um");
  man->CreateNtupleDColumn("y_um");
  man->CreateNtupleDColumn("z_um");
  // x/y/z above are retained as the historical pre-step position.  v2.1
  // appends explicit pre/mid/post coordinates rather than changing that
  // established schema.  The midpoint is the authoritative location for
  // post-transport deposited-energy scoring.
  man->CreateNtupleDColumn("preX_um");
  man->CreateNtupleDColumn("preY_um");
  man->CreateNtupleDColumn("preZ_um");
  man->CreateNtupleDColumn("midX_um");
  man->CreateNtupleDColumn("midY_um");
  man->CreateNtupleDColumn("midZ_um");
  man->CreateNtupleDColumn("postX_um");
  man->CreateNtupleDColumn("postY_um");
  man->CreateNtupleDColumn("postZ_um");
  man->CreateNtupleIColumn("insideBodyPre");
  man->CreateNtupleIColumn("insideBodyMid");
  man->CreateNtupleIColumn("insideBodyPost");
  man->CreateNtupleIColumn("processType");
  man->CreateNtupleIColumn("processSubtype");
  man->CreateNtupleIColumn("creatorProcessType");
  man->CreateNtupleIColumn("creatorProcessSubtype");
  man->FinishNtuple(1);

  man->CreateNtuple("secondaries", "Secondary particle source terms by parent region");
  man->CreateNtupleIColumn("eventID");
  man->CreateNtupleIColumn("regionID");
  man->CreateNtupleIColumn("parentPDG");
  man->CreateNtupleIColumn("secondaryPDG");
  man->CreateNtupleDColumn("ekin_keV");
  man->CreateNtupleDColumn("x_um");
  man->CreateNtupleDColumn("y_um");
  man->CreateNtupleDColumn("z_um");
  man->CreateNtupleIColumn("insideBody");
  man->CreateNtupleDColumn("parentStep_um");
  man->CreateNtupleDColumn("parentPreX_um");
  man->CreateNtupleDColumn("parentPreY_um");
  man->CreateNtupleDColumn("parentPreZ_um");
  man->CreateNtupleDColumn("parentPostX_um");
  man->CreateNtupleDColumn("parentPostY_um");
  man->CreateNtupleDColumn("parentPostZ_um");
  man->FinishNtuple(2);
}

void RunAction::BeginOfRunAction(const G4Run* run)
{
  auto* man = G4AnalysisManager::Instance();
  std::stringstream name; name << "output" << run->GetRunID() << ".root";
  man->OpenFile(name.str());
}
void RunAction::EndOfRunAction(const G4Run*)
{
  auto* man = G4AnalysisManager::Instance();
  man->Write();
  man->CloseFile();
}
