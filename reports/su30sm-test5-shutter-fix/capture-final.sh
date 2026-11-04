set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:163 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :163 -screen 0 1024x768x24 >/tmp/su30-shutter-final-xvfb.log 2>&1 &
xpid=$!
trap 'kill "$xpid" 2>/dev/null || true' EXIT
export PYTHONPATH=/workspace/ysflight-dev/python-vendor AIRCRAFT_CHECK=SU-30SM_CUSTOM
for version in before after; do
 if [ "$version" = before ]; then export GAME_RUNTIME=/workspace/ysflight-dev/active-su30sm-test5-intake-fix/runtime; else export GAME_RUNTIME=/workspace/ysflight-dev/su30sm-shutter-fix/runtime; fi
 export CAPS='[["side", 95, -4, 85, "0 -.65 -1", "1 0 0 0 0 0"], ["quarter", 140, -10, 90, "0 -.65 -1", "1 0 0 0 0 0"], ["main-close", 90, -8, 42, "2.05 -1 -2.3", "1 0 0 0 0 0"]]'
 CHECK_NAME="$version-ground" python /workspace/ysflight-dev/su30sm-shutter-fix/capture.py ground
 export INVERTED=1
 export CAPS='[["up", 145, 25, 90, "0 -.7 -1.2", "0 0 0 0 0 0"], ["early-open", 145, 25, 90, "0 -.7 -1.2", "0.05 0 0 0 0 0"], ["opening", 145, 25, 90, "0 -.7 -1.2", "0.1 0 0 0 0 0"], ["fully-open", 145, 25, 90, "0 -.7 -1.2", "0.175 0 0 0 0 0"], ["mid", 145, 25, 90, "0 -.7 -1.2", "0.5 0 0 0 0 0"], ["closing", 145, 25, 90, "0 -.7 -1.2", "0.85 0 0 0 0 0"], ["near-down", 145, 25, 90, "0 -.7 -1.2", "0.95 0 0 0 0 0"], ["down", 145, 25, 90, "0 -.7 -1.2", "1 0 0 0 0 0"], ["main-up", 75, 15, 45, "2.05 -.7 -1.2", "0 0 0 0 0 0"], ["main-down", 75, 15, 45, "2.05 -.7 -1.2", "1 0 0 0 0 0"]]'
 CHECK_NAME="$version-poses" python /workspace/ysflight-dev/su30sm-shutter-fix/capture.py inspect
 unset INVERTED
done
export GAME_RUNTIME=/workspace/ysflight-dev/su30sm-shutter-fix/runtime
CHECK_NAME=after-live-gear python /workspace/ysflight-dev/su30sm-shutter-fix/capture.py gear
