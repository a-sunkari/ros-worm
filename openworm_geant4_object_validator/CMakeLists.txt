cmake_minimum_required(VERSION 3.16)
project(openworm_geometry_validator LANGUAGES CXX)

find_package(Geant4 REQUIRED ui_all vis_all gdml)

add_executable(openworm_validator
  src/SmokeActionInitialization.cc
  src/main.cc
  src/DetectorConstruction.cc
  src/STLReader.cc
)

target_include_directories(openworm_validator PRIVATE include)
target_link_libraries(openworm_validator PRIVATE ${Geant4_LIBRARIES})
target_compile_features(openworm_validator PRIVATE cxx_std_17)
