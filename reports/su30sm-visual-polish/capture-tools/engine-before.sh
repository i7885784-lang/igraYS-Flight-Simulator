set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:189 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :189 -screen 0 1024x768x24 >/tmp/su30-polish189.log 2>&1 &
xpid=$!;trap 'kill "$xpid" 2>/dev/null || true' EXIT
export PYTHONPATH=/workspace/ysflight-dev/python-vendor AIRCRAFT_CHECK=SU-30SM_CUSTOM GAME_RUNTIME=/workspace/ysflight-dev/su30sm-gear-bays-repair/runtime
CHECK_NAME=before-engine python /workspace/ysflight-dev/su30sm-visual-polish/capture.py engine
