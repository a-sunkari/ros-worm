#ifndef ROS_WORM_MANIFEST_PHYSICS_LIST_HH
#define ROS_WORM_MANIFEST_PHYSICS_LIST_HH
#include "G4VModularPhysicsList.hh"
class PhysicsList : public G4VModularPhysicsList {
public:
  PhysicsList();
  ~PhysicsList() override = default;
};
#endif
