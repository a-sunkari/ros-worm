#include "DetectorConstruction.hh"

#include "G4Box.hh"
#include "G4TessellatedSolid.hh"
#include "G4TriangularFacet.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4NistManager.hh"
#include "G4GenericMessenger.hh"
#include "G4UserLimits.hh"
#include "G4VisAttributes.hh"
#include "G4Colour.hh"
#include "G4SystemOfUnits.hh"
#include "G4Exception.hh"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
struct Tri { std::array<G4ThreeVector,3> v; };

std::uint32_t ReadU32(const unsigned char* p) {
  return (std::uint32_t)p[0] | ((std::uint32_t)p[1]<<8) | ((std::uint32_t)p[2]<<16) | ((std::uint32_t)p[3]<<24);
}
float ReadF32(const unsigned char* p) {
  std::uint32_t u = ReadU32(p); float f; std::memcpy(&f,&u,sizeof(float)); return f;
}
std::vector<std::string> SplitCsv(const std::string& line) {
  std::vector<std::string> out; std::string cur; bool quote=false;
  for (char c: line) {
    if (c=='"') { quote=!quote; continue; }
    if (c==',' && !quote) { out.push_back(cur); cur.clear(); }
    else cur.push_back(c);
  }
  out.push_back(cur); return out;
}
std::string Trim(std::string s) {
  auto notws=[](unsigned char c){return !std::isspace(c);};
  s.erase(s.begin(), std::find_if(s.begin(), s.end(), notws));
  s.erase(std::find_if(s.rbegin(), s.rend(), notws).base(), s.end());
  return s;
}
std::vector<Tri> ReadBinaryStl(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) G4Exception("ReadBinaryStl", "ROSWORM_STL_OPEN", FatalException, ("Cannot open "+path).c_str());
  in.seekg(0,std::ios::end); auto size=(std::uint64_t)in.tellg(); in.seekg(0,std::ios::beg);
  if (size < 84) G4Exception("ReadBinaryStl", "ROSWORM_STL_SMALL", FatalException, path.c_str());
  std::array<unsigned char,84> h{}; in.read((char*)h.data(), h.size());
  auto n = ReadU32(h.data()+80);
  auto expected = 84ull + (std::uint64_t)n*50ull;
  if (expected != size) {
    std::ostringstream msg; msg << "Expected binary STL size " << expected << " but got " << size << " file=" << path;
    G4Exception("ReadBinaryStl", "ROSWORM_STL_FORMAT", FatalException, msg.str().c_str());
  }
  std::vector<Tri> tris; tris.reserve(n); std::array<unsigned char,50> rec{};
  for (std::uint32_t i=0;i<n;++i) {
    in.read((char*)rec.data(), rec.size());
    Tri t;
    for (int j=0;j<3;++j) {
      const auto* p = rec.data()+12+j*12;
      t.v[j]=G4ThreeVector((G4double)ReadF32(p),(G4double)ReadF32(p+4),(G4double)ReadF32(p+8));
    }
    tris.push_back(t);
  }
  return tris;
}
}

DetectorConstruction::DetectorConstruction()
{
  fMessenger = new G4GenericMessenger(this, "/rosworm/", "ROS-Worm manifest transport controls");
  fMessenger->DeclareProperty("manifest", fManifestPath, "CSV manifest with safe_name/category_guess/stl_path/bounds");
  fMessenger->DeclareProperty("materials", fMaterialsPath, "CSV region_id/material_name map for Stage-1 transport materials");
  fMessenger->DeclareProperty("mmPerUnit", fMmPerUnit, "Scale factor: STL model unit to mm");
  fMessenger->DeclareProperty("maxStep_um", fMaxStep, "Maximum biological step length").SetUnit("um");
  fMessenger->DeclareProperty("saveSteps", fSaveSteps, "Write per-step edep ntuple rows");
  fMessenger->DeclareProperty("sourceType", fSourceType, "focused or diffuse");
  fMessenger->DeclareProperty("spectrumType", fSpectrumType, "mono or kramers");
  fMessenger->DeclareProperty("monoEnergy", fMonoEnergy, "Mono energy").SetUnit("keV");
  fMessenger->DeclareProperty("kvp", fKvp, "Kramers endpoint energy").SetUnit("keV");
  fMessenger->DeclareProperty("minEnergy", fMinEnergy, "Kramers minimum sampled energy").SetUnit("keV");
  fMessenger->DeclareProperty("spotFWHM", fSpotFWHM, "Focused beam FWHM").SetUnit("mm");
  fMessenger->DeclareProperty("sourceY", fSourceY, "Source plane y position").SetUnit("mm");
  fMessenger->DeclareProperty("halfX", fHalfX, "Diffuse source half-size x").SetUnit("mm");
  fMessenger->DeclareProperty("halfZ", fHalfZ, "Diffuse source half-size z").SetUnit("mm");
}
DetectorConstruction::~DetectorConstruction(){ delete fMessenger; }

void DetectorConstruction::DefineMaterials()
{
  auto* nist = G4NistManager::Instance();
  fWorldMaterial = nist->FindOrBuildMaterial("G4_AIR");
  fWater = nist->FindOrBuildMaterial("G4_WATER");

  // Default region-specific biological transport materials. These are macroscopic
  // condensed-history materials for Stage 1 only. Stage 2 remains Geant4-DNA
  // liquid-water radiolysis chemistry.
  const std::map<G4int,G4String> defaults = {
    {1, "G4_TISSUE_SOFT_ICRU-4"},
    {2, "G4_BRAIN_ICRP"},
    {3, "G4_MUSCLE_SKELETAL_ICRP"},
    {4, "G4_TISSUE_SOFT_ICRP"},
    {5, "G4_TESTIS_ICRP"},
    {6, "G4_TISSUE_SOFT_ICRU-4"}
  };
  for (const auto& kv : defaults) {
    auto* mat = nist->FindOrBuildMaterial(kv.second, false);
    if (!mat) {
      std::ostringstream msg; msg << "Could not build default NIST material " << kv.second << " for region " << kv.first;
      G4Exception("DefineMaterials", "ROSWORM_MATERIAL_DEFAULT", FatalException, msg.str().c_str());
    }
    fRegionMaterials[kv.first] = mat;
    fRegionMaterialNames[kv.first] = kv.second;
  }
}

void DetectorConstruction::LoadMaterialMap()
{
  std::ifstream in(fMaterialsPath);
  if (!in) {
    G4cout << "[ROS-WORM][MATERIALS] No material CSV found at " << fMaterialsPath
           << "; using built-in biological transport material defaults." << G4endl;
    return;
  }
  std::string header; std::getline(in, header); auto heads = SplitCsv(header);
  std::map<std::string,int> idx; for (int i=0;i<(int)heads.size();++i) idx[Trim(heads[i])]=i;
  auto need=[&](const std::string& c){ if(!idx.count(c)) G4Exception("LoadMaterialMap","ROSWORM_MATERIAL_COL",FatalException,("Missing column "+c).c_str()); return idx[c];};
  const int iRegion=need("region_id"), iMat=need("material_name");
  auto* nist = G4NistManager::Instance();
  std::string line;
  while (std::getline(in,line)) {
    if (Trim(line).empty()) continue;
    auto v=SplitCsv(line);
    if ((int)v.size() <= std::max(iRegion,iMat)) continue;
    const G4int regionId = std::stoi(Trim(v[iRegion]));
    const G4String matName = Trim(v[iMat]);
    if (matName.empty()) continue;
    auto* mat = nist->FindOrBuildMaterial(matName, false);
    if (!mat) {
      std::ostringstream msg; msg << "Could not build NIST material '" << matName << "' for region " << regionId
                                  << ". Check Geant4 NIST material spelling.";
      G4Exception("LoadMaterialMap", "ROSWORM_MATERIAL_NAME", FatalException, msg.str().c_str());
    }
    fRegionMaterials[regionId] = mat;
    fRegionMaterialNames[regionId] = matName;
    G4cout << "[ROS-WORM][MATERIAL] region=" << regionId << " material=" << matName
           << " density_g_cm3=" << mat->GetDensity()/(g/cm3) << G4endl;
  }
}

G4Material* DetectorConstruction::MaterialForRegion(G4int regionId) const
{
  auto it = fRegionMaterials.find(regionId);
  if (it != fRegionMaterials.end() && it->second) return it->second;
  return fWater;
}

G4int DetectorConstruction::CategoryToRegionId(const G4String& category, const G4String& safeName) const
{
  const auto s = category + " " + safeName;
  auto has = [&](const char* needle){ return s.find(needle) != G4String::npos; };
  if (has("whole_body_parent") || has("WholeBodyEnvelope")) return 1;
  if (has("NervousSystem")) return 2;
  if (has("BodyWallMuscle")) return 3;
  if (has("DigestiveSystem")) return 4;
  if (has("ReproductiveSystem")) return 5;
  if (has("ExcretorySystem")) return 6;
  return 0;
}
G4String DetectorConstruction::RegionKeyFromId(G4int id) const
{
  switch(id){case 1:return "body";case 2:return "nervous";case 3:return "bodywall";case 4:return "digestive";case 5:return "reproductive";case 6:return "excretory";default:return "unknown";}
}

void DetectorConstruction::LoadManifest()
{
  fRows.clear(); fRegions.clear(); fPhysicalNameToRegionId.clear();
  std::ifstream in(fManifestPath);
  if (!in) G4Exception("DetectorConstruction::LoadManifest", "ROSWORM_MANIFEST_OPEN", FatalException, ("Cannot open manifest: "+fManifestPath).c_str());
  std::string header; std::getline(in, header); auto heads = SplitCsv(header);
  std::map<std::string,int> idx; for (int i=0;i<(int)heads.size();++i) idx[Trim(heads[i])]=i;
  auto need=[&](const std::string& c){ if(!idx.count(c)) G4Exception("LoadManifest","ROSWORM_MANIFEST_COL",FatalException,("Missing column "+c).c_str()); return idx[c];};
  const int iObj=need("object_name"), iSafe=need("safe_name"), iCat=need("category_guess"), iPath=need("stl_path");
  const int iMinX=need("min_x"), iMinY=need("min_y"), iMinZ=need("min_z"), iMaxX=need("max_x"), iMaxY=need("max_y"), iMaxZ=need("max_z");
  std::string line;
  while (std::getline(in,line)) {
    if (Trim(line).empty()) continue; auto v=SplitCsv(line); if ((int)v.size() <= iPath) continue;
    ManifestRow r; r.objectName=Trim(v[iObj]); r.safeName=Trim(v[iSafe]); r.category=Trim(v[iCat]); r.stlPath=Trim(v[iPath]);
    r.minX=std::stod(v[iMinX]); r.minY=std::stod(v[iMinY]); r.minZ=std::stod(v[iMinZ]); r.maxX=std::stod(v[iMaxX]); r.maxY=std::stod(v[iMaxY]); r.maxZ=std::stod(v[iMaxZ]);
    r.regionId=CategoryToRegionId(r.category, r.safeName); if (r.regionId>0) fRows.push_back(r);
  }
  if (fRows.empty()) G4Exception("LoadManifest","ROSWORM_MANIFEST_EMPTY",FatalException,"No usable rows in manifest");
}

G4VSolid* DetectorConstruction::BuildTessellatedSolid(const G4String& name, const G4String& stlPath, const G4ThreeVector& centerModel) const
{
  auto tris = ReadBinaryStl(stlPath);
  auto* solid = new G4TessellatedSolid(name);
  const G4double scale = fMmPerUnit*mm;
  for (const auto& t: tris) {
    G4ThreeVector a=(t.v[0]-centerModel)*scale;
    G4ThreeVector b=(t.v[1]-centerModel)*scale;
    G4ThreeVector c=(t.v[2]-centerModel)*scale;
    if (((b-a).cross(c-a)).mag2() <= 0) continue;
    solid->AddFacet(new G4TriangularFacet(a,b,c,ABSOLUTE));
  }
  solid->SetSolidClosed(true);
  return solid;
}

G4VPhysicalVolume* DetectorConstruction::Construct()
{
  DefineMaterials(); LoadMaterialMap(); LoadManifest();
  ManifestRow* body = nullptr; for (auto& r: fRows) if (r.regionId==1) { body=&r; break; }
  if (!body) G4Exception("Construct","ROSWORM_NO_BODY",FatalException,"Manifest needs WholeBodyEnvelope/whole_body_parent row");
  G4ThreeVector center((body->minX+body->maxX)/2.0, (body->minY+body->maxY)/2.0, (body->minZ+body->maxZ)/2.0);
  G4double spanX=(body->maxX-body->minX)*fMmPerUnit*mm, spanY=(body->maxY-body->minY)*fMmPerUnit*mm, spanZ=(body->maxZ-body->minZ)*fMmPerUnit*mm;
  G4double half = std::max({spanX,spanY,spanZ})/2.0 + fWorldMargin;
  auto* worldS = new G4Box("world", half, half, half);
  auto* worldL = new G4LogicalVolume(worldS, fWorldMaterial, "world_log");
  auto* worldP = new G4PVPlacement(nullptr, {}, worldL, "world_phys", nullptr, false, 0, false);
  fStepLimit = new G4UserLimits(fMaxStep);

  G4LogicalVolume* bodyL = nullptr;
  for (auto& r: fRows) {
    auto* solid = BuildTessellatedSolid("solid_"+r.safeName, r.stlPath, center);
    auto* material = MaterialForRegion(r.regionId);
    auto* lv = new G4LogicalVolume(solid, material, "ow_"+r.safeName+"_log");
    lv->SetUserLimits(fStepLimit);
    auto* vis = new G4VisAttributes(); vis->SetForceWireframe(true); lv->SetVisAttributes(vis);
    const auto physName = "ow_"+r.safeName+"_phys";
    if (r.regionId == 1) {
      bodyL = lv;
      new G4PVPlacement(nullptr, {}, lv, physName, worldL, false, r.regionId, false);
    } else {
      if (!bodyL) G4Exception("Construct","ROSWORM_BODY_ORDER",FatalException,"Body must be constructed before children");
      new G4PVPlacement(nullptr, {}, lv, physName, bodyL, false, r.regionId, false);
    }
    RegionInfo info; info.id=r.regionId; info.key=RegionKeyFromId(r.regionId); info.safeName=r.safeName; info.physicalName=physName;
    info.materialName = fRegionMaterialNames.count(r.regionId) ? fRegionMaterialNames.at(r.regionId) : material->GetName();
    info.density = material->GetDensity();
    info.mass=solid->GetCubicVolume()*material->GetDensity();
    fRegions.push_back(info); fPhysicalNameToRegionId[physName]=r.regionId;
    G4cout << "[ROS-WORM][REGION] id=" << info.id << " key=" << info.key << " phys=" << info.physicalName
           << " material=" << info.materialName << " density_g_cm3=" << info.density/(g/cm3)
           << " mass_kg=" << info.mass/kg << G4endl;
  }
  return worldP;
}

G4int DetectorConstruction::RegionIdFromPhysicalName(const G4String& physName) const
{
  auto it=fPhysicalNameToRegionId.find(physName); return it==fPhysicalNameToRegionId.end()?0:it->second;
}
G4String DetectorConstruction::RegionKey(G4int id) const { return RegionKeyFromId(id); }
G4String DetectorConstruction::RegionMaterialName(G4int id) const { for (const auto& r:fRegions) if (r.id==id) return r.materialName; return "unknown"; }
G4double DetectorConstruction::RegionMass(G4int id) const { for (const auto& r:fRegions) if (r.id==id) return r.mass; return 0.0; }
