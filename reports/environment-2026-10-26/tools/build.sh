#!/bin/bash
set -euo pipefail
cd /workspace/ysflight-dev/YSFlight_Su57_Test_2_Engine_Source
source /workspace/ysflight-dev/env.sh
bits=${1:-32}
case "$bits" in
  32) toolchain="$PWD/mingw32.cmake"; diagnostic= ;;
  64) toolchain=/workspace/ysflight-dev/mingw64.cmake; diagnostic=-DV861_VALIDATION ;;
  *) exit 2 ;;
esac
cmake -S YSFLIGHT/src -B "build$bits" -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$toolchain" -DCMAKE_BUILD_TYPE=Release '-DCMAKE_CXX_STANDARD_LIBRARIES=-lkernel32 -luser32 -lgdi32 -lwinspool -lshell32 -lole32 -loleaut32 -luuid -lcomdlg32 -ladvapi32 -limm32' \
  "-DCMAKE_CXX_FLAGS=${diagnostic:+$diagnostic }-DWIN32 -D_WINDOWS -DNOMINMAX -fpermissive -fno-delete-null-pointer-checks" \
  '-DCMAKE_C_FLAGS=-Wno-error=incompatible-pointer-types' \
  '-DCMAKE_SHARED_LINKER_FLAGS=-static -static-libgcc -static-libstdc++' \
  '-DCMAKE_EXE_LINKER_FLAGS=-static -static-libgcc -static-libstdc++ -mwindows'
cmake --build "build$bits" --target "ysflight${bits}_gl1" --parallel 3

# MinGW prefixes DLL outputs with lib; the game loads the Windows names.
cp "build$bits/sounddll/win32/libsndYsflight$bits.dll" "build$bits/main/plugin/sndYsflight$bits.dll"
cp "build$bits/voicedll/generic/libvoiceYsflight$bits.dll" "build$bits/main/plugin/voiceYsflight$bits.dll"
