cmake_minimum_required(VERSION 3.10)

project(SharSpineQuadBenchmark VERSION 1.0)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED True)
set(CMAKE_C_STANDARD 11)

include(cmake/CPM.cmake)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# Parent directory holds the simd_quad_*.c sources. Add them as sources to the
# benchmark executable, gated on the host architecture: only the variants
# whose ISA matches will compile.
set(QUAD_DIR "${CMAKE_CURRENT_SOURCE_DIR}/..")

set(QUAD_SOURCES "")
if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm64|aarch64)$" OR APPLE)
    list(APPEND QUAD_SOURCES
        "${QUAD_DIR}/simd_quad_pi5.c"
        "${QUAD_DIR}/simd_quad_m4.c"
        "${QUAD_DIR}/simd_quad_graviton.c")
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64|i.86)$")
    list(APPEND QUAD_SOURCES "${QUAD_DIR}/simd_quad_intel.c")
else()
    message(FATAL_ERROR "Unsupported CMAKE_SYSTEM_PROCESSOR: ${CMAKE_SYSTEM_PROCESSOR}")
endif()

add_executable(benchmark benchmarks/benchmark.cpp ${QUAD_SOURCES})
target_include_directories(benchmark PRIVATE "${QUAD_DIR}")

# Per-arch tuning flags. -march/-mcpu=native is the right default for a
# benchmark host; CI / cross hosts can override CMAKE_<LANG>_FLAGS.
if(NOT MSVC)
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm64|aarch64)$" OR APPLE)
        target_compile_options(benchmark PRIVATE -mcpu=native -O3)
    elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64|i.86)$")
        target_compile_options(benchmark PRIVATE -march=native -O3)
    endif()
endif()

CPMAddPackage("gh:lemire/counters#v3.1.0")
target_link_libraries(benchmark PRIVATE counters)
