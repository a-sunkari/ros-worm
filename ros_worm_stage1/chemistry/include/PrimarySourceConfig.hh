#ifndef ROS_WORM_PRIMARY_SOURCE_CONFIG_HH
#define ROS_WORM_PRIMARY_SOURCE_CONFIG_HH

#include "globals.hh"

class G4GenericMessenger;

// Macro-owned source settings for the chemistry application.
// This object is created by ActionInitialization, so these commands exist
// before /run/initialize and are safe in MT mode. Worker-local primary
// generators only read this object during GeneratePrimaries().
class PrimarySourceConfig
{
public:
  PrimarySourceConfig();
  ~PrimarySourceConfig();

  const G4String& GetMode() const { return fMode; }
  const G4String& GetSpectrumFile() const { return fSpectrumFile; }
  G4bool GetVerbose() const { return fVerbose; }

private:
  G4GenericMessenger* fMessenger = nullptr;
  G4String fMode = "gun";  // gun or spectrum
  G4String fSpectrumFile = "electron_spectrum.csv";
  G4bool fVerbose = false;
};

#endif
