set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:208 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :208 -screen 0 1024x768x24 >/tmp/su30-bay208.log 2>&1 &
xpid=$!;trap 'kill "$xpid" 2>/dev/null || true' EXIT
export PYTHONPATH=/workspace/ysflight-dev/python-vendor AIRCRAFT_CHECK=SU-30SM_CUSTOM INVERTED=1
export CAPS='[["bottom-down",150,35,75,"0 -.5 -2","1 0 0 0 0 0"],["bottom-up",150,35,75,"0 -.5 -2","0 0 0 0 0 0"],["main-left-down",140,40,23,"-1.8 -.1 -2","1 0 0 0 0 0"],["main-left-up",140,40,23,"-1.8 -.1 -2","0 0 0 0 0 0"],["main-right-down",220,40,23,"1.8 -.1 -2","1 0 0 0 0 0"],["main-right-up",220,40,23,"1.8 -.1 -2","0 0 0 0 0 0"],["nose-down",150,35,21,"0 -.1 3.2","1 0 0 0 0 0"],["nose-up",150,35,21,"0 -.1 3.2","0 0 0 0 0 0"]]'
GAME_RUNTIME=/workspace/ysflight-dev/su30sm-bay-seams/runtime CHECK_NAME=after-bottom python /workspace/ysflight-dev/su30sm-bay-seams/capture.py inspect
export CAPS='[["main-left-mid",140,40,23,"-1.8 -.1 -2",".5 0 0 0 0 0"],["main-right-mid",220,40,23,"1.8 -.1 -2",".5 0 0 0 0 0"],["nose-mid",150,35,21,"0 -.1 3.2",".5 0 0 0 0 0"]]'
GAME_RUNTIME=/workspace/ysflight-dev/su30sm-dark-channel/runtime CHECK_NAME=before-mid python /workspace/ysflight-dev/su30sm-bay-seams/capture.py inspect
GAME_RUNTIME=/workspace/ysflight-dev/su30sm-bay-seams/runtime CHECK_NAME=after-mid python /workspace/ysflight-dev/su30sm-bay-seams/capture.py inspect
unset INVERTED
export PYTHONPATH=/workspace/ysflight-dev/python-vendor AIRCRAFT_CHECK=SU-30SM_CUSTOM GAME_RUNTIME=/workspace/ysflight-dev/su30sm-bay-seams/runtime
export CAPS='[["front",180,-10,58,"0 -.5 -1.5","1 0 0 0 0 0"],["front-close",175,-12,24,"-1.18 -.55 -1.5","1 0 0 0 0 0"],["front-left",150,-22,26,"-1.18 -.6 -1.4","1 0 0 0 0 0"],["front-right",210,-22,26,"1.18 -.6 -1.4","1 0 0 0 0 0"],["side-left",90,-12,70,"0 -.3 -2","1 0 0 0 0 0"],["side-right",270,-12,70,"0 -.3 -2","1 0 0 0 0 0"],["top",145,45,90,"0 0 -1","1 0 0 0 0 0"],["rear",0,10,60,"0 -.4 -8.5","1 0 0 0 0 0"]]'
CHECK_NAME=after-ground python /workspace/ysflight-dev/su30sm-bay-seams/capture.py ground
CHECK_NAME=after-gear64 python /workspace/ysflight-dev/su30sm-bay-seams/capture.py gear
export GEAR_DOWN=1 ORBIT_DISTANCE=95 ORBIT_AIM='0 0 -1'
CHECK_NAME=after-orbit64 python /workspace/ysflight-dev/su30sm-bay-seams/capture.py orbit
unset GEAR_DOWN
export WINELOADER=/workspace/ysflight-dev/wow64-test/wine-11.21-amd64-wow64/bin/wine WINESERVER=/workspace/ysflight-dev/wow64-test/wine-11.21-amd64-wow64/bin/wineserver WINEPREFIX=/workspace/ysflight-dev/wine-su30-wow64-clean GAME_EXE=ysflight32_gl1.exe
unset WINEDLLPATH
CHECK_NAME=after-gear32 python /workspace/ysflight-dev/su30sm-bay-seams/capture.py gear
