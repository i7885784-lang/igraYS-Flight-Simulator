set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:190 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :190 -screen 0 1024x768x24 >/tmp/su30-polish190.log 2>&1 &
xpid=$!;trap 'kill "$xpid" 2>/dev/null || true' EXIT
export PYTHONPATH=/workspace/ysflight-dev/python-vendor AIRCRAFT_CHECK=SU-30SM_CUSTOM GAME_RUNTIME=/workspace/ysflight-dev/su30sm-visual-polish/runtime
export CAPS='[["rear",0,5,48,"0 -.4 -8.6","1 0 0 0 0 0"],["rear-quarter",35,15,50,"0 -.5 -7.8","1 0 0 0 0 0"],["main-gap",90,-5,30,"2.3 -.3 -2","1 0 0 0 0 0"],["nose-gap",110,-8,26,"0 -.2 3.3","1 0 0 0 0 0"],["canopy-open",90,8,55,"0 1.2 3.3","1 1 0 0 0 0"],["front",180,-7,75,"0 -.8 -.2","1 0 0 0 0 0"],["side",90,0,85,"0 .2 -1","1 0 0 0 0 0"]]'
CHECK_NAME=after-ground python /workspace/ysflight-dev/su30sm-visual-polish/capture.py ground
export INVERTED=1
export CAPS='[["rear-bottom",25,25,55,"0 -.3 -7","0 0 0 0 0 0"],["centre-bottom",160,35,55,"0 -.5 -1.6","0 0 0 0 0 0"],["gear-mid",145,25,85,"0 -.7 -1.2",".5 0 0 0 0 0"],["main-mid",75,15,42,"2.05 -.7 -1.2",".5 0 0 0 0 0"]]'
CHECK_NAME=after-bottom python /workspace/ysflight-dev/su30sm-visual-polish/capture.py inspect
unset INVERTED
CHECK_NAME=after-brake python /workspace/ysflight-dev/su30sm-visual-polish/capture.py brake

CHECK_NAME=after-canopy python /workspace/ysflight-dev/su30sm-visual-polish/capture.py canopy
CHECK_NAME=after-gear python /workspace/ysflight-dev/su30sm-visual-polish/capture.py gear
CHECK_NAME=after-engine python /workspace/ysflight-dev/su30sm-visual-polish/capture.py engine
