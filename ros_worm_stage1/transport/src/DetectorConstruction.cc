#include "DetectorConstruction.hh"

#include "G4Box.hh"
#include "G4Tubs.hh"
#include "G4Orb.hh"
#include "G4TessellatedSolid.hh"
#include "G4TriangularFacet.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4NistManager.hh"
#include "G4RotationMatrix.hh"
#include "G4GenericMessenger.hh"
#include "G4UserLimits.hh"
#include "G4VisAttributes.hh"
#include "G4Colour.hh"
#include "G4PhysicalConstants.hh"
#include "G4RunManager.hh"
#include "G4SDManager.hh"
#include "G4Exception.hh"
#include "G4String.hh"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace
{
struct StlTriangle
{
  std::array<G4ThreeVector, 3> v;
};

struct StlMesh
{
  std::vector<StlTriangle> triangles;
  G4ThreeVector min;
  G4ThreeVector max;
};

std::uint32_t ReadUInt32LE(const unsigned char* p)
{
  return static_cast<std::uint32_t>(p[0]) |
         (static_cast<std::uint32_t>(p[1]) << 8) |
         (static_cast<std::uint32_t>(p[2]) << 16) |
         (static_cast<std::uint32_t>(p[3]) << 24);
}

float ReadFloatLE(const unsigned char* p)
{
  std::uint32_t u = ReadUInt32LE(p);
  float f;
  static_assert(sizeof(float) == sizeof(std::uint32_t), "float must be 32-bit");
  std::memcpy(&f, &u, sizeof(float));
  return f;
}

void UpdateBounds(G4ThreeVector& mn, G4ThreeVector& mx, const G4ThreeVector& p)
{
  mn.setX(std::min(mn.x(), p.x()));
  mn.setY(std::min(mn.y(), p.y()));
  mn.setZ(std::min(mn.z(), p.z()));
  mx.setX(std::max(mx.x(), p.x()));
  mx.setY(std::max(mx.y(), p.y()));
  mx.setZ(std::max(mx.z(), p.z()));
}

StlMesh ReadBinaryStl(const std::string& fileName)
{
  std::ifstream in(fileName, std::ios::binary);
  if (!in) {
    G4Exception("DetectorConstruction::ReadBinaryStl", "ROSWORM001", FatalException,
                ("Could not open STL file: " + fileName).c_str());
  }

  in.seekg(0, std::ios::end);
  const auto fileSize = static_cast<std::uint64_t>(in.tellg());
  in.seekg(0, std::ios::beg);

  if (fileSize < 84) {
    G4Exception("DetectorConstruction::ReadBinaryStl", "ROSWORM002", FatalException,
                ("STL file is too small: " + fileName).c_str());
  }

  std::array<unsigned char, 84> header{};
  in.read(reinterpret_cast<char*>(header.data()), header.size());
  const auto nTri = ReadUInt32LE(header.data() + 80);
  const std::uint64_t expectedSize = 84ull + static_cast<std::uint64_t>(nTri) * 50ull;
  if (expectedSize != fileSize) {
    std::ostringstream msg;
    msg << "Only standard binary STL is supported by this first importer. "
        << "File size does not match binary STL triangle count. file=" << fileName
        << " expected=" << expectedSize << " actual=" << fileSize;
    G4Exception("DetectorConstruction::ReadBinaryStl", "ROSWORM003", FatalException,
                msg.str().c_str());
  }

  StlMesh mesh;
  mesh.triangles.reserve(nTri);
  mesh.min = G4ThreeVector( std::numeric_limits<G4double>::max(),
                            std::numeric_limits<G4double>::max(),
                            std::numeric_limits<G4double>::max());
  mesh.max = G4ThreeVector(-std::numeric_limits<G4double>::max(),
                           -std::numeric_limits<G4double>::max(),
                           -std::numeric_limits<G4double>::max());

  std::array<unsigned char, 50> rec{};
  for (std::uint32_t i = 0; i < nTri; ++i) {
    in.read(reinterpret_cast<char*>(rec.data()), rec.size());
    if (!in) {
      G4Exception("DetectorConstruction::ReadBinaryStl", "ROSWORM004", FatalException,
                  ("Unexpected EOF while reading STL file: " + fileName).c_str());
    }

    StlTriangle tri;
    // bytes 0-11 are the stored normal; recompute/use vertices only.
    for (int j = 0; j < 3; ++j) {
      const auto* p = rec.data() + 12 + j*12;
      const auto x = static_cast<G4double>(ReadFloatLE(p + 0));
      const auto y = static_cast<G4double>(ReadFloatLE(p + 4));
      const auto z = static_cast<G4double>(ReadFloatLE(p + 8));
      tri.v[j] = G4ThreeVector(x, y, z);
      UpdateBounds(mesh.min, mesh.max, tri.v[j]);
    }
    mesh.triangles.push_back(tri);
  }

  if (mesh.triangles.empty()) {
    G4Exception("DetectorConstruction::ReadBinaryStl", "ROSWORM005", FatalException,
                ("STL file contains zero triangles: " + fileName).c_str());
  }

  return mesh;
}

G4ThreeVector AxisMappedAndScaled(const G4ThreeVector& raw,
                                  const G4ThreeVector& center,
                                  int longAxis,
                                  G4double scale)
{
  const G4double c[3] = {raw.x() - center.x(), raw.y() - center.y(), raw.z() - center.z()};

  // Map the STL's longest axis to local +z, because the existing analytic worm
  // and proxy ROIs use local z as the worm anterior-posterior axis. The worm
  // logical volume is then rotated local z -> world x, preserving the current
  // source/agar layout.
  if (longAxis == 0) return G4ThreeVector(c[1]*scale, c[2]*scale, c[0]*scale);
  if (longAxis == 1) return G4ThreeVector(c[2]*scale, c[0]*scale, c[1]*scale);
  return G4ThreeVector(c[0]*scale, c[1]*scale, c[2]*scale);
}

G4double TransverseRadius(const G4ThreeVector& p)
{
  return std::sqrt(p.x()*p.x() + p.y()*p.y());
}
}

DetectorConstruction::DetectorConstruction()
{
  fGeometryMessenger = new G4GenericMessenger(this, "/worm/geometry/", "C. elegans geometry controls");

  fGeometryMessenger->DeclareProperty("mode", fGeometryMode,
      "Geometry mode: analytic or mesh. Set before /run/initialize.");
  fGeometryMessenger->DeclarePropertyWithUnit("wormLength", "mm", fWormLength,
      "Cylinder length of the analytic worm surrogate. Set before /run/initialize.");
  fGeometryMessenger->DeclarePropertyWithUnit("wormRadius", "um", fWormRadius,
      "Radius of the analytic worm surrogate. Set before /run/initialize.");
  fGeometryMessenger->DeclareProperty("wormMaterial", fWormMaterialChoice,
      "Worm material: water or soft. Set before /run/initialize.");
  fGeometryMessenger->DeclareProperty("meshFile", fMeshFile,
      "Binary STL file for mesh geometry mode. Path is relative to run directory unless absolute.");
  fGeometryMessenger->DeclarePropertyWithUnit("meshTargetLength", "mm", fMeshTargetLength,
      "Scale mesh longest dimension to this length. Set before /run/initialize.");
  fGeometryMessenger->DeclareProperty("useProxyROIs", fUseProxyROIs,
      "Place analytic head/VNC/body-wall/intestine proxy ROIs inside the worm volume.");
  fGeometryMessenger->DeclareMethodWithUnit("maxStep", "um",
      &DetectorConstruction::SetMaxStep,
      "Maximum step in worm/ROI biological volumes.");

  fSourceMessenger = new G4GenericMessenger(this, "/worm/source/", "X-ray source controls");
  fSourceMessenger->DeclareProperty("type", fSourceType, "focused or diffuse");
  fSourceMessenger->DeclareProperty("spectrum", fSpectrumType, "mono or kramers");
  fSourceMessenger->DeclarePropertyWithUnit("energy", "keV", fMonoEnergy, "Mono photon energy");
  fSourceMessenger->DeclarePropertyWithUnit("sourceZ", "mm", fSourceZ, "Source z position");
  fSourceMessenger->DeclarePropertyWithUnit("spotFWHM", "mm", fSpotFWHM, "Focused beam FWHM at worm plane");
  fSourceMessenger->DeclarePropertyWithUnit("coneHalfAngle", "deg", fConeHalfAngle, "Diffuse source cone half-angle");
  fSourceMessenger->DeclarePropertyWithUnit("kvp", "keV", fKvp, "Kramers spectrum endpoint energy");
  fSourceMessenger->DeclarePropertyWithUnit("minEnergy", "keV", fMinEnergy, "Minimum sampled photon energy");

  fScoringMessenger = new G4GenericMessenger(this, "/worm/scoring/", "Transport scoring controls");
  fScoringMessenger->DeclareProperty("saveSteps", fSaveSteps,
      "Save per-step particle/energy rows for electron spectrum extraction.");
}

DetectorConstruction::~DetectorConstruction()
{
  delete fGeometryMessenger;
  delete fSourceMessenger;
  delete fScoringMessenger;
  delete fBioStepLimit;
}

G4bool DetectorConstruction::UseMeshGeometry() const
{
  return (fGeometryMode == "mesh" || fGeometryMode == "stl" || fGeometryMode == "openworm");
}

void DetectorConstruction::DefineMaterials()
{
  auto* nist = G4NistManager::Instance();

  fWorldMaterial = nist->FindOrBuildMaterial("G4_AIR");
  fWater = nist->FindOrBuildMaterial("G4_WATER");
  fAgarMaterial = fWater; // first-level model: agar/M9 as water-like.

  auto* H = nist->FindOrBuildElement("H");
  auto* C = nist->FindOrBuildElement("C");
  auto* N = nist->FindOrBuildElement("N");
  auto* O = nist->FindOrBuildElement("O");

  // Simple organic soft-tissue proxy. This is intentionally not over-fit to
  // worm biochemistry; it gives a sensitivity check against pure water.
  fSoftTissue = new G4Material("WormSoftTissue", 1.05*g/cm3, 4);
  fSoftTissue->AddElement(H, 10.1*perCent);
  fSoftTissue->AddElement(C, 11.1*perCent);
  fSoftTissue->AddElement(N,  2.6*perCent);
  fSoftTissue->AddElement(O, 76.2*perCent);

  if (fWormMaterialChoice == "soft" || fWormMaterialChoice == "soft_tissue") {
    fWormMaterial = fSoftTissue;
  } else {
    fWormMaterial = fWater;
  }
}

G4VSolid* DetectorConstruction::BuildAnalyticWormSolid()
{
  fEffectiveWormRadius = fWormRadius;
  return new G4Tubs("worm_solid", 0, fWormRadius, 0.5*fWormLength, 0, 360*deg);
}

G4VSolid* DetectorConstruction::BuildMeshWormSolid()
{
  auto mesh = ReadBinaryStl(fMeshFile);

  const auto span = mesh.max - mesh.min;
  const G4double spans[3] = {span.x(), span.y(), span.z()};
  int longAxis = 0;
  if (spans[1] > spans[longAxis]) longAxis = 1;
  if (spans[2] > spans[longAxis]) longAxis = 2;

  const auto longest = spans[longAxis];
  if (longest <= 0.0) {
    G4Exception("DetectorConstruction::BuildMeshWormSolid", "ROSWORM006", FatalException,
                "STL mesh has invalid zero/negative bounding-box length.");
  }

  const auto scale = fMeshTargetLength / longest;
  const auto center = 0.5*(mesh.min + mesh.max);

  auto* solid = new G4TessellatedSolid("openworm_outer_solid");
  G4double maxR = 0.0;

  for (const auto& rawTri : mesh.triangles) {
    const auto a = AxisMappedAndScaled(rawTri.v[0], center, longAxis, scale);
    const auto b = AxisMappedAndScaled(rawTri.v[1], center, longAxis, scale);
    const auto c = AxisMappedAndScaled(rawTri.v[2], center, longAxis, scale);

    maxR = std::max(maxR, TransverseRadius(a));
    maxR = std::max(maxR, TransverseRadius(b));
    maxR = std::max(maxR, TransverseRadius(c));

    solid->AddFacet(new G4TriangularFacet(a, b, c, ABSOLUTE));
  }

  solid->SetSolidClosed(true);

  fWormLength = fMeshTargetLength;
  fEffectiveWormRadius = maxR;

  G4cout << "[ROS-WORM] Geometry mode     = mesh" << G4endl;
  G4cout << "[ROS-WORM] Mesh file         = " << fMeshFile << G4endl;
  G4cout << "[ROS-WORM] Mesh triangles    = " << mesh.triangles.size() << G4endl;
  G4cout << "[ROS-WORM] Raw mesh spans    = (" << span.x() << ", " << span.y() << ", " << span.z() << ") model units" << G4endl;
  G4cout << "[ROS-WORM] Longest raw axis  = " << longAxis << G4endl;
  G4cout << "[ROS-WORM] Mesh scale        = " << scale/mm << " mm/model-unit" << G4endl;
  G4cout << "[ROS-WORM] Target length     = " << fWormLength/mm << " mm" << G4endl;
  G4cout << "[ROS-WORM] Effective radius  = " << fEffectiveWormRadius/um << " um" << G4endl;

  return solid;
}

G4VSolid* DetectorConstruction::BuildWormSolid()
{
  if (UseMeshGeometry()) {
    return BuildMeshWormSolid();
  }

  G4cout << "[ROS-WORM] Geometry mode     = analytic" << G4endl;
  return BuildAnalyticWormSolid();
}

void DetectorConstruction::ComputeMasses(G4VSolid* wormSolid)
{
  const auto rho = fWormMaterial->GetDensity();

  const auto wormVolume = wormSolid ? wormSolid->GetCubicVolume() : pi * fWormRadius * fWormRadius * fWormLength;
  const auto headVolume = fUseProxyROIs ? 4.0*pi*fHeadRadius*fHeadRadius*fHeadRadius/3.0 : 0.0;
  const auto vncVolume = fUseProxyROIs ? pi * fVNCRadius * fVNCRadius * (2.0*fVNCHalfLength) : 0.0;
  const auto bodyWallVolume = fUseProxyROIs ? pi * (fBodyWallOuterR*fBodyWallOuterR - fBodyWallInnerR*fBodyWallInnerR)
                            * (2.0*fBodyWallHalfLength) : 0.0;
  const auto intestineVolume = fUseProxyROIs ? pi * fIntestineRadius * fIntestineRadius * (2.0*fIntestineHalfLength) : 0.0;

  fWormMass = rho * wormVolume;
  fHeadMass = rho * headVolume;
  fVNCMass = rho * vncVolume;
  fBodyWallMass = rho * bodyWallVolume;
  fIntestineMass = rho * intestineVolume;

  G4cout << "[ROS-WORM] Worm material     = " << fWormMaterial->GetName() << G4endl;
  G4cout << "[ROS-WORM] Worm length       = " << fWormLength/mm << " mm" << G4endl;
  G4cout << "[ROS-WORM] Worm radius       = " << fEffectiveWormRadius/um << " um" << G4endl;
  G4cout << "[ROS-WORM] Worm volume       = " << wormVolume/(mm3) << " mm3" << G4endl;
  G4cout << "[ROS-WORM] Worm mass         = " << fWormMass/g << " g" << G4endl;
  G4cout << "[ROS-WORM] Proxy ROIs        = " << (fUseProxyROIs ? "enabled" : "disabled") << G4endl;
}

G4VPhysicalVolume* DetectorConstruction::Construct()
{
  DefineMaterials();

  const G4bool checkOverlaps = true;

  auto* solidWorld = new G4Box("world_solid", 60*mm, 60*mm, 60*mm);
  auto* logicWorld = new G4LogicalVolume(solidWorld, fWorldMaterial, "world_logic");
  auto* physWorld = new G4PVPlacement(nullptr, {}, logicWorld, "world_phys", nullptr, false, 0, checkOverlaps);

  auto* solidAgar = new G4Box("agar_solid", fAgarHalfXY, fAgarHalfXY, fAgarHalfThickness);
  auto* logicAgar = new G4LogicalVolume(solidAgar, fAgarMaterial, "agar_logic");
  new G4PVPlacement(nullptr, G4ThreeVector(0,0,-fAgarHalfThickness), logicAgar,
                    "agar_phys", logicWorld, false, 0, checkOverlaps);

  auto* solidWorm = BuildWormSolid();
  ComputeMasses(solidWorm);
  fLogicWorm = new G4LogicalVolume(solidWorm, fWormMaterial, "worm_logic");

  // The worm logical-volume local z axis is the anatomical long axis. Rotate it
  // onto world x, preserving the original beam/source layout.
  auto* wormRot = new G4RotationMatrix();
  wormRot->rotateY(90*deg);
  new G4PVPlacement(wormRot, G4ThreeVector(0,0,fEffectiveWormRadius), fLogicWorm,
                    "worm_phys", logicWorld, false, 0, checkOverlaps);

  // Internal ROIs as daughter volumes. These remain analytic proxy regions; for
  // mesh geometry they should be considered temporary scoring approximations,
  // not OpenWorm organ meshes. They can be disabled with /worm/geometry/useProxyROIs false.
  if (fUseProxyROIs) {
    auto* solidHead = new G4Orb("head_roi_solid", fHeadRadius);
    fLogicHead = new G4LogicalVolume(solidHead, fWormMaterial, "head_roi_logic");
    new G4PVPlacement(nullptr, G4ThreeVector(0,0,fHeadZ), fLogicHead,
                      "head_roi_phys", fLogicWorm, false, 0, checkOverlaps);

    auto* solidVNC = new G4Tubs("vnc_roi_solid", 0, fVNCRadius, fVNCHalfLength, 0, 360*deg);
    fLogicVNC = new G4LogicalVolume(solidVNC, fWormMaterial, "vnc_roi_logic");
    new G4PVPlacement(nullptr, G4ThreeVector(0,fVNCY,fVNCZ), fLogicVNC,
                      "vnc_roi_phys", fLogicWorm, false, 0, checkOverlaps);

    auto* solidBodyWall = new G4Tubs("body_wall_roi_solid", fBodyWallInnerR, fBodyWallOuterR,
                                     fBodyWallHalfLength, 0, 360*deg);
    fLogicBodyWall = new G4LogicalVolume(solidBodyWall, fWormMaterial, "body_wall_roi_logic");
    new G4PVPlacement(nullptr, G4ThreeVector(0,0,0), fLogicBodyWall,
                      "body_wall_roi_phys", fLogicWorm, false, 0, checkOverlaps);

    auto* solidIntestine = new G4Tubs("intestine_roi_solid", 0, fIntestineRadius,
                                      fIntestineHalfLength, 0, 360*deg);
    fLogicIntestine = new G4LogicalVolume(solidIntestine, fWormMaterial, "intestine_roi_logic");
    new G4PVPlacement(nullptr, G4ThreeVector(0,0,fIntestineZ), fLogicIntestine,
                      "intestine_roi_phys", fLogicWorm, false, 0, checkOverlaps);
  }

  fBioStepLimit = new G4UserLimits(fMaxStep);
  if (fLogicWorm) fLogicWorm->SetUserLimits(fBioStepLimit);
  if (fLogicHead) fLogicHead->SetUserLimits(fBioStepLimit);
  if (fLogicVNC) fLogicVNC->SetUserLimits(fBioStepLimit);
  if (fLogicBodyWall) fLogicBodyWall->SetUserLimits(fBioStepLimit);
  if (fLogicIntestine) fLogicIntestine->SetUserLimits(fBioStepLimit);

  logicWorld->SetVisAttributes(G4VisAttributes::GetInvisible());
  logicAgar->SetVisAttributes(new G4VisAttributes(G4Colour(0.3, 0.6, 1.0, 0.15)));
  if (fLogicWorm) fLogicWorm->SetVisAttributes(new G4VisAttributes(G4Colour(0.9, 0.8, 0.6, 0.55)));
  if (fLogicHead) fLogicHead->SetVisAttributes(new G4VisAttributes(G4Colour(1.0, 0.0, 0.0, 0.85)));
  if (fLogicVNC) fLogicVNC->SetVisAttributes(new G4VisAttributes(G4Colour(0.0, 0.1, 1.0, 0.85)));
  if (fLogicBodyWall) fLogicBodyWall->SetVisAttributes(new G4VisAttributes(G4Colour(0.0, 0.8, 0.0, 0.35)));
  if (fLogicIntestine) fLogicIntestine->SetVisAttributes(new G4VisAttributes(G4Colour(0.6, 0.2, 0.8, 0.45)));

  return physWorld;
}

void DetectorConstruction::ConstructSDandField()
{
  // No explicit sensitive detector is required for first-level scoring.
  // SteppingAction bins dose by physical-volume name. This keeps the geometry
  // simple and avoids custom hit-collection bookkeeping.
}

void DetectorConstruction::SetMaxStep(G4double step)
{
  fMaxStep = step;
  if (fBioStepLimit) {
    fBioStepLimit->SetMaxAllowedStep(fMaxStep);
    G4cout << "[ROS-WORM] Updated biological max step = " << fMaxStep/um << " um" << G4endl;
  }
}
