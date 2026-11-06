set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:216 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :216 -screen 0 1024x768x24 >/tmp/su30-seal216.log 2>&1 &
xpid=$!;trap 'kill "$xpid" 2>/dev/null || true' EXIT
export PYTHONPATH=/workspace/ysflight-dev/python-vendor AIRCRAFT_CHECK=SU-30SM_CUSTOM
export CAPS='[["front",180,-4,55,"0 -.55 -.1","1 0 0 0 0 0"],["left-match",165,-8,22,"-1.1 -.55 .2","1 0 0 0 0 0"],["right-match",195,-8,22,"1.1 -.55 .2","1 0 0 0 0 0"],["left-straight",180,-4,22,"-1.1 -.55 .2","1 0 0 0 0 0"],["right-straight",180,-4,22,"1.1 -.55 .2","1 0 0 0 0 0"],["left-below",155,-25,24,"-1.1 -.65 .2","1 0 0 0 0 0"],["right-below",205,-25,24,"1.1 -.65 .2","1 0 0 0 0 0"],["left-side",120,-8,28,"-1.1 -.55 .2","1 0 0 0 0 0"],["right-side",240,-8,28,"1.1 -.55 .2","1 0 0 0 0 0"]]'
GAME_RUNTIME=/workspace/ysflight-dev/su30sm-intake-seal/runtime CHECK_NAME=after-ground python /workspace/ysflight-dev/su30sm-intake-seal/capture.py ground
export GEAR_DOWN=1 ORBIT_DISTANCE=22 ORBIT_AIM='1.1 -.55 .2' ORBIT_PITCH=-8 ORBIT_HEADINGS='[120,135,150,165,180,195,210,225,240]'
GAME_RUNTIME=/workspace/ysflight-dev/su30sm-intake-seal/runtime CHECK_NAME=after-orbit python /workspace/ysflight-dev/su30sm-intake-seal/capture.py orbit
