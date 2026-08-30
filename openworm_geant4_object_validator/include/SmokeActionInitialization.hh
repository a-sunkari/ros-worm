#pragma once

#include "DetectorConstruction.hh"

#include <G4VUserActionInitialization.hh>

class SmokeActionInitialization : public G4VUserActionInitialization {
public:
    explicit SmokeActionInitialization(const ValidatorConfig& cfg);
    ~SmokeActionInitialization() override = default;

    void Build() const override;

private:
    ValidatorConfig cfg_;
};
