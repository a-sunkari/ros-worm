#include "PrimarySourceConfig.hh"

#include "G4GenericMessenger.hh"

PrimarySourceConfig::PrimarySourceConfig()
{
  fMessenger = new G4GenericMessenger(this, "/ros/source/",
                                      "ROS Worm chemistry source controls");
  fMessenger->DeclareProperty("mode", fMode,
      "Primary source mode: 'gun' keeps the standard /gun settings; 'spectrum' samples electron_spectrum.csv.");
  fMessenger->DeclareProperty("spectrumFile", fSpectrumFile,
      "CSV spectrum file with columns energy_keV,weight. Used only when /ros/source/mode spectrum.");
  fMessenger->DeclareProperty("verbose", fVerbose,
      "Print source-loading information from worker primary generators.");
}

PrimarySourceConfig::~PrimarySourceConfig()
{
  delete fMessenger;
}
