cmake_minimum_required(VERSION 3.16)
project(ros_worm_transport_manifest)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Geant4 REQUIRED ui_all vis_all)
include(${Geant4_USE_FILE})

set(SOURCES
  src/DetectorConstruction.cc
  src/PhysicsList.cc
  src/PrimaryGenerator.cc
  src/ActionInitialization.cc
  src/RunAction.cc
  src/EventAction.cc
  src/SteppingAction.cc
)

add_executable(ros_worm_manifest ros_worm_manifest.cc ${SOURCES})
target_include_directories(ros_worm_manifest PRIVATE include)
target_link_libraries(ros_worm_manifest ${Geant4_LIBRARIES})

get_filename_component(ROSWORM_REPO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
target_compile_definitions(ros_worm_manifest PRIVATE ROSWORM_REPO_ROOT="${ROSWORM_REPO_ROOT}")

file(COPY macros DESTINATION ${CMAKE_BINARY_DIR})
