#!/bin/bash
set -euo pipefail
engine=$(realpath "$1")
bits=${2:-64}
build=$(realpath -m "${3:-$engine/build$bits}")
cmake -S "$engine/YSFLIGHT/src" -B "$build" -G Ninja \
 -DCMAKE_TOOLCHAIN_FILE="$engine/mingw$bits.cmake" -DCMAKE_BUILD_TYPE=Release \
 '-DCMAKE_CXX_STANDARD_LIBRARIES=-lkernel32 -luser32 -lgdi32 -lwinspool -lshell32 -lole32 -loleaut32 -luuid -lcomdlg32 -ladvapi32 -limm32' \
 "-DCMAKE_CXX_FLAGS=$([ "$bits" = 64 ] && echo -DV861_VALIDATION || true) -DWIN32 -D_WINDOWS -DNOMINMAX -fpermissive -fno-delete-null-pointer-checks" \
 '-DCMAKE_C_FLAGS=-Wno-error=incompatible-pointer-types' \
 '-DCMAKE_SHARED_LINKER_FLAGS=-static -static-libgcc -static-libstdc++' \
 '-DCMAKE_EXE_LINKER_FLAGS=-static -static-libgcc -static-libstdc++ -mwindows'
cmake --build "$build" --target "ysflight${bits}_gl1" --parallel 3
