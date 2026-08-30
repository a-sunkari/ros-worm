#pragma once

#include <G4UserSteppingAction.hh>
#include <map>

class G4Step;

class TrackingSmokeSteppingAction : public G4UserSteppingAction {
public:
    void UserSteppingAction(const G4Step* step) override;

private:
    std::map<int, int> stepCountByTrack_;
};
