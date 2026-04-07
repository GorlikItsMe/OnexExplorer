set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_PROCESSOR x86_64)

# This toolchain file expects LLVM-MinGW unpacked somewhere and pointed to via LLVM_MINGW_ROOT.
# Example:
#   export LLVM_MINGW_ROOT="$PWD/third_party/llvm-mingw"
if(NOT DEFINED LLVM_MINGW_ROOT)
  if(DEFINED ENV{LLVM_MINGW_ROOT})
    set(LLVM_MINGW_ROOT "$ENV{LLVM_MINGW_ROOT}")
  endif()
endif()

if(NOT DEFINED LLVM_MINGW_ROOT)
  message(FATAL_ERROR "LLVM_MINGW_ROOT is not set (path to llvm-mingw).")
endif()

set(_TOOLBIN "${LLVM_MINGW_ROOT}/bin")

set(CMAKE_C_COMPILER   "${_TOOLBIN}/x86_64-w64-mingw32-clang")
set(CMAKE_CXX_COMPILER "${_TOOLBIN}/x86_64-w64-mingw32-clang++")
set(CMAKE_RC_COMPILER  "${_TOOLBIN}/llvm-rc")

# Where to search for headers/libs when cross-compiling
set(CMAKE_FIND_ROOT_PATH
  "${LLVM_MINGW_ROOT}/x86_64-w64-mingw32"
  "${LLVM_MINGW_ROOT}"
)

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

# Allow passing a Qt prefix from the environment (helps non-interactive builds)
# Example:
#   QT_WIN_PREFIX="$PWD/third_party/qt/5.15.2/mingw81_64"
if(DEFINED ENV{QT_WIN_PREFIX})
  list(PREPEND CMAKE_PREFIX_PATH "$ENV{QT_WIN_PREFIX}")
  list(PREPEND CMAKE_FIND_ROOT_PATH "$ENV{QT_WIN_PREFIX}")
endif()

# Make CMake prefer static libs when available (tweak as needed)
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)

