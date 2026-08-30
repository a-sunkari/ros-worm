#ifndef DETECTOR_CONSTRUCTION_HH
#define DETECTOR_CONSTRUCTION_HH

#include "G4VUserDetectorConstruction.hh"
#include "G4SystemOfUnits.hh"
#include "globals.hh"

class G4LogicalVolume;
class G4VPhysicalVolume;
class G4Material;
class G4GenericMessenger;
class G4UserLimits;
class G4VSolid;

class DetectorConstruction : public G4VUserDetectorConstruction
{
public:
  DetectorConstruction();
  ~DetectorConstruction() override;

  G4VPhysicalVolume* Construct() override;
  void ConstructSDandField() override;

  G4double GetWormMass() const { return fWormMass; }
  G4double GetHeadMass() const { return fHeadMass; }
  G4double GetVNCMass() const { return fVNCMass; }
  G4double GetBodyWallMass() const { return fBodyWallMass; }
  G4double GetIntestineMass() const { return fIntestineMass; }

  G4double GetWormLength() const { return fWormLength; }
  G4double GetWormRadius() const { return fEffectiveWormRadius; }

  // Macro-controlled transport source/scoring settings. These live here so
  // commands exist before /run/initialize in MT mode.
  const G4String& GetSourceType() const { return fSourceType; }
  const G4String& GetSpectrumType() const { return fSpectrumType; }
  G4double GetSourceZ() const { return fSourceZ; }
  G4double GetSpotFWHM() const { return fSpotFWHM; }
  G4double GetConeHalfAngle() const { return fConeHalfAngle; }
  G4double GetMonoEnergy() const { return fMonoEnergy; }
  G4double GetKvp() const { return fKvp; }
  G4double GetMinEnergy() const { return fMinEnergy; }
  G4bool GetSaveSteps() const { return fSaveSteps; }

private:
  void DefineMaterials();
  G4VSolid* BuildWormSolid();
  G4VSolid* BuildAnalyticWormSolid();
  G4VSolid* BuildMeshWormSolid();
  void ComputeMasses(G4VSolid* wormSolid);
  void SetMaxStep(G4double step);
  G4bool UseMeshGeometry() const;

  G4Material* fWorldMaterial = nullptr;
  G4Material* fAgarMaterial = nullptr;
  G4Material* fWormMaterial = nullptr;
  G4Material* fWater = nullptr;
  G4Material* fSoftTissue = nullptr;

  G4LogicalVolume* fLogicWorm = nullptr;
  G4LogicalVolume* fLogicHead = nullptr;
  G4LogicalVolume* fLogicVNC = nullptr;
  G4LogicalVolume* fLogicBodyWall = nullptr;
  G4LogicalVolume* fLogicIntestine = nullptr;

  G4GenericMessenger* fGeometryMessenger = nullptr;
  G4GenericMessenger* fSourceMessenger = nullptr;
  G4GenericMessenger* fScoringMessenger = nullptr;
  G4UserLimits* fBioStepLimit = nullptr;

  G4double fWormLength = 1.0*mm;
  G4double fWormRadius = 40.0*um;
  G4double fEffectiveWormRadius = 40.0*um;
  G4double fAgarHalfThickness = 0.50*mm;
  G4double fAgarHalfXY = 5.0*mm;
  G4double fMaxStep = 2.0*um;
  G4String fWormMaterialChoice = "water";

  // Geometry mode:
  //   analytic = original cylinder surrogate
  //   mesh     = STL-derived OpenWorm/Virtual Worm outer-body tessellated solid
  G4String fGeometryMode = "analytic";
  G4String fMeshFile = "geometry/openworm/worm_outer_openworm.stl";
  G4double fMeshTargetLength = 1.0*mm;
  G4bool fUseProxyROIs = true;

  G4double fHeadRadius = 18.0*um;
  G4double fHeadZ = -0.38*mm;
  G4double fVNCRadius = 3.0*um;
  G4double fVNCHalfLength = 0.30*mm;
  G4double fVNCZ = 0.15*mm;
  G4double fVNCY = -28.0*um;
  G4double fBodyWallInnerR = 34.0*um;
  G4double fBodyWallOuterR = 39.0*um;
  G4double fBodyWallHalfLength = 0.45*mm;
  G4double fIntestineRadius = 15.0*um;
  G4double fIntestineHalfLength = 0.35*mm;
  G4double fIntestineZ = 0.10*mm;

  G4double fWormMass = 0.0;
  G4double fHeadMass = 0.0;
  G4double fVNCMass = 0.0;
  G4double fBodyWallMass = 0.0;
  G4double fIntestineMass = 0.0;

  // Source defaults: focused 50 kVp-like beam through worm center.
  G4String fSourceType = "focused";      // focused or diffuse
  G4String fSpectrumType = "kramers";    // mono or kramers
  G4double fSourceZ = 50.0*mm;
  G4double fSpotFWHM = 0.85*mm;
  G4double fConeHalfAngle = 60.0*deg;
  G4double fMonoEnergy = 30.0*keV;
  G4double fKvp = 50.0*keV;
  G4double fMinEnergy = 1.0*keV;
  G4bool fSaveSteps = true;
};

#endif
