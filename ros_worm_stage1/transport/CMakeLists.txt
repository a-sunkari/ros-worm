cmake_minimum_required(VERSION 3.16)
project(ros_worm_transport_stage1)

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

add_executable(ros_worm ros_worm.cc ${SOURCES})
target_include_directories(ros_worm PRIVATE include)
target_link_libraries(ros_worm ${Geant4_LIBRARIES})

file(COPY macros DESTINATION ${CMAKE_BINARY_DIR})
file(COPY analysis DESTINATION ${CMAKE_BINARY_DIR})
file(COPY geometry DESTINATION ${CMAKE_BINARY_DIR})
