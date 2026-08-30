cmake_minimum_required(VERSION 3.16...3.27)
project(ros_worm_chemistry_stage1)

option(WITH_GEANT4_UIVIS "Build with Geant4 UI and Vis drivers" ON)
if(WITH_GEANT4_UIVIS)
  find_package(Geant4 REQUIRED ui_all vis_all)
else()
  find_package(Geant4 REQUIRED)
endif()

include(${Geant4_USE_FILE})
include_directories(${PROJECT_SOURCE_DIR}/include)

file(GLOB sources ${PROJECT_SOURCE_DIR}/src/*.cc)
file(GLOB headers ${PROJECT_SOURCE_DIR}/include/*.hh)

add_executable(ros_worm_chem chem6.cc ${sources} ${headers})
target_link_libraries(ros_worm_chem ${Geant4_LIBRARIES})

# Preserve the original chem6 executable name as an alias for sanity testing.
add_executable(chem6 chem6.cc ${sources} ${headers})
target_link_libraries(chem6 ${Geant4_LIBRARIES})

file(GLOB CHEM_SCRIPTS
  ${PROJECT_SOURCE_DIR}/*.in
  ${PROJECT_SOURCE_DIR}/*.mac
  ${PROJECT_SOURCE_DIR}/*.C)
foreach(_script ${CHEM_SCRIPTS})
  configure_file(${_script} ${PROJECT_BINARY_DIR}/. COPYONLY)
endforeach()

file(COPY analysis DESTINATION ${PROJECT_BINARY_DIR})
configure_file(${PROJECT_SOURCE_DIR}/electron_spectrum.example.csv
               ${PROJECT_BINARY_DIR}/electron_spectrum.example.csv COPYONLY)

install(TARGETS ros_worm_chem chem6 DESTINATION bin)
