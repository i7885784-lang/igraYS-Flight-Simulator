set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:196 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :196 -screen 0 1024x768x24 >/tmp/su30-intake196.log 2>&1 &
xpid=$!;trap 'kill "$xpid" 2>/dev/null || true' EXIT
export PYTHONPATH=/workspace/ysflight-dev/python-vendor AIRCRAFT_CHECK=SU-30SM_CUSTOM GEAR_DOWN=1 ORBIT_DISTANCE=55 ORBIT_AIM='-1.18 -.55 -1.5'
export GAME_RUNTIME=/workspace/ysflight-dev/su30sm-visual-polish/runtime
CHECK_NAME=before-orbit python /workspace/ysflight-dev/su30sm-intake-artifacts/capture.py orbit
export GAME_RUNTIME=/workspace/ysflight-dev/su30sm-intake-artifacts/runtime
CHECK_NAME=after-orbit python /workspace/ysflight-dev/su30sm-intake-artifacts/capture.py orbit
