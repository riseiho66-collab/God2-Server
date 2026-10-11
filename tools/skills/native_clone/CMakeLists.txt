cmake_minimum_required(VERSION 3.24)
project(God2ShunyingClone LANGUAGES CXX)
if(NOT WIN32 OR NOT MSVC OR NOT CMAKE_SIZEOF_VOID_P EQUAL 4)
  message(FATAL_ERROR "God2ShunyingClone requires MSVC Win32 (-A Win32), not x64")
endif()
add_library(God2ShunyingClone SHARED clone_hooks.cpp clone_visuals.cpp clone_particles.cpp battle_background.cpp bull_effect.cpp bull_native_tick.cpp)
target_compile_features(God2ShunyingClone PRIVATE cxx_std_20)
target_compile_definitions(God2ShunyingClone PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX _WIN32_WINNT=0x0601)
target_compile_options(God2ShunyingClone PRIVATE /W4 /permissive- /EHsc /utf-8)
# The isolated client has no new VC runtime deployment dependency.
set_property(TARGET God2ShunyingClone PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded")
set_target_properties(God2ShunyingClone PROPERTIES PREFIX "" OUTPUT_NAME "God2ShunyingClone"
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
foreach(configuration IN ITEMS DEBUG RELEASE RELWITHDEBINFO MINSIZEREL)
  set_target_properties(God2ShunyingClone PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY_${configuration} "${CMAKE_BINARY_DIR}/bin")
endforeach()

target_link_libraries(God2ShunyingClone PRIVATE winmm)
