#!/bin/bash
set -euo pipefail
source /workspace/ysflight-dev/env.sh
mkdir -p "$XDG_CACHE_HOME" "$WINEPREFIX/drive_c/windows/system32"
cp /workspace/ysflight-dev/tools/usr/x86_64-w64-mingw32/lib/zlib1.dll "$WINEPREFIX/drive_c/windows/system32/zlib1.dll"
if ! DISPLAY=:99 xwininfo -root >/dev/null 2>&1; then
  Xvfb :99 -screen 0 1280x960x24 -ac -nolisten tcp > /workspace/ysflight-dev/xvfb.log 2>&1 &
  for i in {1..30}; do
    if DISPLAY=:99 xwininfo -root >/dev/null 2>&1; then break; fi
    sleep .2
  done
fi
"$WINELOADER" cmd /c echo WINE_OK
