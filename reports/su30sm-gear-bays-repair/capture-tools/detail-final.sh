set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:184 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :184 -screen 0 1024x768x24 >/tmp/su30-detail184.log 2>&1 &
xpid=$!
trap 'kill "$xpid" 2>/dev/null || true' EXIT
export PYTHONPATH=/workspace/ysflight-dev/python-vendor AIRCRAFT_CHECK=SU-30SM_CUSTOM INVERTED=1
export CAPS='[["main-mid-right",75,15,45,"2.05 -.7 -1.2",".5 0 0 0 0 0"],["main-mid-left",285,15,45,"-2.05 -.7 -1.2",".5 0 0 0 0 0"],["main-closing",75,15,45,"2.05 -.7 -1.2",".87 0 0 0 0 0"]]'
GAME_RUNTIME=/workspace/ysflight-dev/su30sm-shutter-fix/runtime CHECK_NAME=before-detail python /workspace/ysflight-dev/su30sm-gear-bays-repair/capture.py inspect
GAME_RUNTIME=/workspace/ysflight-dev/su30sm-gear-bays-repair/runtime CHECK_NAME=after-detail python /workspace/ysflight-dev/su30sm-gear-bays-repair/capture.py inspect
