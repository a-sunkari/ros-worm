#include "RunAction.hh"

#include "G4AnalysisManager.hh"
#include "G4Run.hh"
#include "G4SystemOfUnits.hh"
#include "G4UnitsTable.hh"

#include <sstream>

RunAction::RunAction()
{
  auto* man = G4AnalysisManager::Instance();
  man->SetVerboseLevel(1);
  man->SetNtupleMerging(true); // ROOT ntuple merge in MT mode.

  man->CreateH1("Edep_worm_keV", "Energy deposited in total worm per event", 200, 0., 50.);
  man->CreateH1("Dose_worm_Gy", "Dose to total worm per incident photon", 200, 0., 1e-10);
  man->CreateH1("Electron_Epre_worm_keV", "Pre-step kinetic energy of e-/e+ steps in worm regions", 250, 0., 50.);
  man->CreateH1("Gamma_Epre_worm_keV", "Pre-step kinetic energy of gamma steps in worm regions", 250, 0., 50.);

  man->CreateNtuple("event", "Per-primary worm regional dose and transport source term");
  man->CreateNtupleIColumn("eventID");
  man->CreateNtupleDColumn("Edep_worm_keV");
  man->CreateNtupleDColumn("Edep_head_keV");
  man->CreateNtupleDColumn("Edep_vnc_keV");
  man->CreateNtupleDColumn("Edep_bodywall_keV");
  man->CreateNtupleDColumn("Edep_intestine_keV");
  man->CreateNtupleDColumn("Edep_agar_keV");
  man->CreateNtupleDColumn("Dose_worm_Gy_per_primary");
  man->CreateNtupleDColumn("Dose_head_Gy_per_primary");
  man->CreateNtupleDColumn("Dose_vnc_Gy_per_primary");
  man->CreateNtupleDColumn("Dose_bodywall_Gy_per_primary");
  man->CreateNtupleDColumn("Dose_intestine_Gy_per_primary");
  man->FinishNtuple(0);

  man->CreateNtuple("steps", "Optional per-step debug rows in worm/ROI volumes");
  man->CreateNtupleIColumn("eventID");
  man->CreateNtupleIColumn("regionID");
  man->CreateNtupleIColumn("pdg");
  man->CreateNtupleDColumn("edep_keV");
  man->CreateNtupleDColumn("ekin_pre_keV");
  man->CreateNtupleDColumn("x_um");
  man->CreateNtupleDColumn("y_um");
  man->CreateNtupleDColumn("z_um");
  man->FinishNtuple(1);
}

void RunAction::BeginOfRunAction(const G4Run* run)
{
  auto* man = G4AnalysisManager::Instance();

  std::stringstream name;
  name << "output" << run->GetRunID() << ".root";
  man->OpenFile(name.str());
}

void RunAction::EndOfRunAction(const G4Run*)
{
  auto* man = G4AnalysisManager::Instance();
  man->Write();
  man->CloseFile();
}
