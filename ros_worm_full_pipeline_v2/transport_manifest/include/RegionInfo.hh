#ifndef ROS_WORM_REGION_INFO_HH
#define ROS_WORM_REGION_INFO_HH

#include "globals.hh"
#include <map>
#include <string>

struct RegionInfo {
  G4int id = 0;
  G4String key;
  G4String safeName;
  G4String physicalName;
  G4String materialName;
  G4double density = 0.0;
  G4double mass = 0.0;
};

#endif
