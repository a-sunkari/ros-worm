#ifndef ROS_WORM_MANIFEST_DETECTOR_CONSTRUCTION_HH
#define ROS_WORM_MANIFEST_DETECTOR_CONSTRUCTION_HH

#include "G4VUserDetectorConstruction.hh"
#include "G4SystemOfUnits.hh"
#include "globals.hh"
#include "G4ThreeVector.hh"
#include "RegionInfo.hh"

#include <map>
#include <vector>

class G4GenericMessenger;
class G4LogicalVolume;
class G4Material;
class G4UserLimits;
class G4VPhysicalVolume;
class G4VSolid;

class DetectorConstruction : public G4VUserDetectorConstruction {
public:
  DetectorConstruction();
  ~DetectorConstruction() override;

  G4VPhysicalVolume* Construct() override;

  const G4String& GetManifestPath() const { return fManifestPath; }
  G4double GetMmPerUnit() const { return fMmPerUnit; }
  G4bool GetSaveSteps() const { return fSaveSteps; }

  const G4String& GetSourceType() const { return fSourceType; }
  const G4String& GetSpectrumType() const { return fSpectrumType; }
  G4double GetMonoEnergy() const { return fMonoEnergy; }
  G4double GetKvp() const { return fKvp; }
  G4double GetMinEnergy() const { return fMinEnergy; }
  G4double GetSpotFWHM() const { return fSpotFWHM; }
  G4double GetSourceY() const { return fSourceY; }
  G4double GetHalfX() const { return fHalfX; }
  G4double GetHalfZ() const { return fHalfZ; }
  const G4String& GetSpectrumFile() const { return fSpectrumFile; }
  G4ThreeVector GetSourcePosition() const { return {fSourceX, fSourceY, fSourceZ}; }
  G4ThreeVector GetSourceDirection() const { return {fDirectionX, fDirectionY, fDirectionZ}; }
  G4ThreeVector GetTargetPosition() const { return {fTargetX, fTargetY, fTargetZ}; }

  G4int RegionIdFromPhysicalName(const G4String& physName) const;
  G4String RegionKey(G4int id) const;
  G4double RegionMass(G4int id) const;
  const std::vector<RegionInfo>& Regions() const { return fRegions; }
  G4String RegionMaterialName(G4int id) const;
  G4bool IsInsideBody(const G4ThreeVector& position) const;

private:
  void DefineMaterials();
  void LoadManifest();
  void LoadMaterialMap();
  G4Material* MaterialForRegion(G4int regionId) const;
  G4VSolid* BuildTessellatedSolid(const G4String& name, const G4String& stlPath, const G4ThreeVector& centerModel) const;
  G4int CategoryToRegionId(const G4String& category, const G4String& safeName) const;
  G4String RegionKeyFromId(G4int id) const;

  G4GenericMessenger* fMessenger = nullptr;
  G4Material* fWorldMaterial = nullptr;
  G4Material* fWater = nullptr;
  std::map<G4int,G4Material*> fRegionMaterials;
  std::map<G4int,G4String> fRegionMaterialNames;
  G4UserLimits* fStepLimit = nullptr;
  G4VSolid* fBodySolid = nullptr;

  struct ManifestRow {
    G4String objectName;
    G4String safeName;
    G4String category;
    G4String stlPath;
    G4double minX=0, minY=0, minZ=0, maxX=0, maxY=0, maxZ=0;
    G4int regionId=0;
  };

  std::vector<ManifestRow> fRows;
  std::vector<RegionInfo> fRegions;
  std::map<G4String,G4int> fPhysicalNameToRegionId;

  G4String fManifestPath;
  G4String fMaterialsPath;
  G4double fMmPerUnit = 0.1;
  G4double fWorldMargin = 1.0*mm;
  G4double fMaxStep = 2.0*um;
  G4bool fSaveSteps = true;

  G4String fSourceType = "focused";
  G4String fSpectrumType = "kramers";
  G4String fSpectrumFile = "";
  G4double fMonoEnergy = 30.0*keV;
  G4double fKvp = 50.0*keV;
  G4double fMinEnergy = 1.0*keV;
  G4double fSpotFWHM = 0.85*mm;
  G4double fSourceY = -2.0*mm;
  G4double fSourceX = 0.0*mm;
  G4double fSourceZ = 0.0*mm;
  G4double fDirectionX = 0.0;
  G4double fDirectionY = 1.0;
  G4double fDirectionZ = 0.0;
  G4double fTargetX = 0.0*mm;
  G4double fTargetY = 0.0*mm;
  G4double fTargetZ = 0.0*mm;
  G4double fHalfX = 0.6*mm;
  G4double fHalfZ = 0.6*mm;

  G4String fEnvironmentMode = "none"; // none, slab, or immersion
  G4String fEnvironmentMaterial = "G4_WATER";
  G4double fEnvironmentHalfX = 2.0*mm;
  G4double fEnvironmentHalfY = 2.0*mm;
  G4double fEnvironmentAbove = 0.0*mm;
  G4double fEnvironmentBelow = 0.0*mm;
  G4String fSubstrateMaterial = "none";
  G4double fSubstrateThickness = 0.0*mm;
};

#endif
