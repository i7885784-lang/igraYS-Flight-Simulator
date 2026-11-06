set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:217 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :217 -screen 0 1024x768x24 >/tmp/su30-seal217.log 2>&1 &
xpid=$!;trap 'kill "$xpid" 2>/dev/null || true' EXIT
export PYTHONPATH=/workspace/ysflight-dev/python-vendor AIRCRAFT_CHECK=SU-30SM_CUSTOM
export CAPS='[["air-front",180,0,55,"0 -.55 .2","1 0 0 0 0 0"],["air-left-front",180,0,22,"-1.1 -.55 .2","1 0 0 0 0 0"],["air-right-front",180,0,22,"1.1 -.55 .2","1 0 0 0 0 0"],["air-left-below",150,-25,24,"-1.1 -.55 .2","1 0 0 0 0 0"],["air-right-below",210,-25,24,"1.1 -.55 .2","1 0 0 0 0 0"],["air-bottom",180,-40,55,"0 -.55 .2","1 0 0 0 0 0"],["air-left-side",90,-10,55,"-1.1 -.55 .2","1 0 0 0 0 0"],["air-right-side",270,-10,55,"1.1 -.55 .2","1 0 0 0 0 0"],["air-high-diagonal",150,20,28,"-1.1 -.55 .2","1 0 0 0 0 0"]]'
GAME_RUNTIME=/workspace/ysflight-dev/su30sm-bay-seams/runtime CHECK_NAME=before-air python /workspace/ysflight-dev/su30sm-intake-seal/capture.py inspect
GAME_RUNTIME=/workspace/ysflight-dev/su30sm-intake-seal/runtime CHECK_NAME=after-air python /workspace/ysflight-dev/su30sm-intake-seal/capture.py inspect
