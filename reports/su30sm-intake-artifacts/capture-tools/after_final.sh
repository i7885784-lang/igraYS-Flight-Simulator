set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:200 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :200 -screen 0 1024x768x24 >/tmp/su30-intake200.log 2>&1 &
xpid=$!;trap 'kill "$xpid" 2>/dev/null || true' EXIT
export PYTHONPATH=/workspace/ysflight-dev/python-vendor AIRCRAFT_CHECK=SU-30SM_CUSTOM GAME_RUNTIME=/workspace/ysflight-dev/su30sm-intake-artifacts/runtime
export CAPS='[["screen-match",175,-10,32,"-1.18 -.55 -1.5","1 0 0 0 0 0"],["screen-low",185,-18,32,"-1.18 -.55 -1.5","1 0 0 0 0 0"]]'
CHECK_NAME=after-detail python /workspace/ysflight-dev/su30sm-intake-artifacts/capture.py ground
export CAPS='[["user-angle",155,-9,35,"-1.1 -.6 -1.7","1 0 0 0 0 0"],["front",180,-10,55,"0 -.5 -1.6","1 0 0 0 0 0"],["left-intake",165,-8,25,"-1.18 -.54 -1.7","1 0 0 0 0 0"],["right-intake",195,-8,25,"1.18 -.54 -1.7","1 0 0 0 0 0"],["low-left",150,-20,32,"-1.18 -.6 -2","1 0 0 0 0 0"],["side",110,-10,42,"-1.3 -.6 -2.3","1 0 0 0 0 0"]]'
CHECK_NAME=after-ground python /workspace/ysflight-dev/su30sm-intake-artifacts/capture.py ground
export INVERTED=1
export CAPS='[["underside-up",155,30,70,"0 -.5 -2","0 0 0 0 0 0"],["underside-mid",155,30,70,"0 -.5 -2",".5 0 0 0 0 0"],["underside-down",155,30,70,"0 -.5 -2","1 0 0 0 0 0"]]'
CHECK_NAME=after-bottom python /workspace/ysflight-dev/su30sm-intake-artifacts/capture.py inspect
unset INVERTED
CHECK_NAME=after-gear python /workspace/ysflight-dev/su30sm-intake-artifacts/capture.py gear
export GEAR_DOWN=1 ORBIT_DISTANCE=55 ORBIT_AIM='-1.18 -.55 -1.5'
CHECK_NAME=after-orbit python /workspace/ysflight-dev/su30sm-intake-artifacts/capture.py orbit
