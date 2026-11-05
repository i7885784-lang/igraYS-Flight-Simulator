set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:183 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :183 -screen 0 1024x768x24 >/tmp/su30-bays-183.log 2>&1 &
xpid=$!
trap 'kill "$xpid" 2>/dev/null || true' EXIT
export PYTHONPATH=/workspace/ysflight-dev/python-vendor AIRCRAFT_CHECK=SU-30SM_CUSTOM
export GAME_RUNTIME=/workspace/ysflight-dev/su30sm-gear-bays-repair/runtime
export CAPS='[["front",180,-7,75,"0 -.8 -.2","-1 -1 -1 -1 -1 -1"],["main-close",90,-8,42,"2.05 -1 -2.3","-1 -1 -1 -1 -1 -1"],["nose-close",125,-12,30,"0 -.8 3.2","-1 -1 -1 -1 -1 -1"],["bottom",145,-35,80,"0 -.7 -.5","-1 -1 -1 -1 -1 -1"],["main-left",270,-8,42,"-2.05 -1 -2.3","-1 -1 -1 -1 -1 -1"],["side",95,-4,85,"0 -.65 -1","-1 -1 -1 -1 -1 -1"],["nose-front",180,-12,32,"0 -1 3.2","-1 -1 -1 -1 -1 -1"]]'
CHECK_NAME=after-final-ground python /workspace/ysflight-dev/su30sm-gear-bays-repair/capture.py ground
export INVERTED=1
export CAPS='[["up",145,25,90,"0 -.7 -1.2","0 0 0 0 0 0"],["opening",145,25,90,"0 -.7 -1.2",".15 0 0 0 0 0"],["mid",145,25,90,"0 -.7 -1.2",".5 0 0 0 0 0"],["closing",145,25,90,"0 -.7 -1.2",".87 0 0 0 0 0"],["down",145,25,90,"0 -.7 -1.2","1 0 0 0 0 0"],["main-up",75,15,45,"2.05 -.7 -1.2","0 0 0 0 0 0"],["main-down",75,15,45,"2.05 -.7 -1.2","1 0 0 0 0 0"],["nose-up",160,30,30,"0 .0 3.1","0 0 0 0 0 0"],["nose-mid",160,30,30,"0 .0 3.1",".3 0 0 0 0 0"],["nose-down",160,30,30,"0 .0 3.1","1 0 0 0 0 0"]]'
CHECK_NAME=after-final-poses python /workspace/ysflight-dev/su30sm-gear-bays-repair/capture.py inspect
unset INVERTED
CHECK_NAME=after-native-cycle python /workspace/ysflight-dev/su30sm-gear-bays-repair/capture.py gear
