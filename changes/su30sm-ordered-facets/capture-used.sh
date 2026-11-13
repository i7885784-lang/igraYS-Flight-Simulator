set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:220 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :220 -screen 0 1024x768x24 > work/facets/xvfb.log 2>&1 &
xpid=$!; trap 'kill "$xpid" 2>/dev/null || true' EXIT
export AIRCRAFT_CHECK=SU-30SM_CUSTOM INVERTED=1
export CAPS='[["match",90,18,40,"-1.4 -.5 -1.5","0 0 0 0 0 0"],["near-a",84,20,42,"-1.4 -.5 -1.5","0 0 0 0 0 0"],["near-b",98,14,42,"-1.4 -.5 -1.5","0 0 0 0 0 0"],["lower",90,38,44,"-1.4 -.5 -1.5","0 0 0 0 0 0"],["mid",90,18,40,"-1.4 -.5 -1.5",".5 0 0 0 0 0"],["down",90,18,40,"-1.4 -.5 -1.5","1 0 0 0 0 0"]]'
for variant in after; do
 if [ "$variant" = before ]; then export GAME_RUNTIME=/workspace/work/su30sm-local-skin/work/candidate/runtime; else export GAME_RUNTIME=/workspace/work/su30sm-local-skin/work/facets-probe/runtime; fi
 CHECK_NAME="ordered-$variant" /workspace/work/venv/bin/python work/lab/capture.py inspect
done
