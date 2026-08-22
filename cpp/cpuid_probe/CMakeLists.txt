cmake_minimum_required(VERSION 3.24)

project(platval_cpuid_probe VERSION 0.1.0 LANGUAGES CXX)

include(CTest)

add_library(
    cpuid_core
    src/cpuid_access.cpp
    src/decoder.cpp
    src/json.cpp
)
target_include_directories(cpuid_core PUBLIC include)
target_compile_features(cpuid_core PUBLIC cxx_std_20)
set_target_properties(cpuid_core PROPERTIES CXX_EXTENSIONS OFF)

if(MSVC)
    target_compile_options(cpuid_core PRIVATE /W4 /permissive-)
else()
    target_compile_options(cpuid_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

add_executable(cpuid_probe src/main.cpp)
target_link_libraries(cpuid_probe PRIVATE cpuid_core)

if(BUILD_TESTING)
    add_executable(cpuid_decoder_tests tests/decoder_tests.cpp)
    target_link_libraries(cpuid_decoder_tests PRIVATE cpuid_core)
    add_test(NAME cpuid_decoder_tests COMMAND cpuid_decoder_tests)
endif()
