set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:231 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :231 -screen 0 1024x768x24 > work/large-panels/xvfb-lit.log 2>&1 &
xpid=$!; trap 'kill "$xpid" 2>/dev/null || true' EXIT
export AIRCRAFT_CHECK=SU-30SM_CUSTOM GAME_RUNTIME=/workspace/work/su30sm-local-skin/work/facets-probe/runtime INVERTED=0
export CAPS='[["ground-lit",0,0,28,"-1.45 -.8 -1.3","1 0 0 0 0 0"],["ground-lit-near",10,2,30,"-1.45 -.8 -1.3","1 0 0 0 0 0"],["ground-lit-mid",0,0,28,"-1.45 -.8 -1.3",".5 0 0 0 0 0"]]'

for variant in before after; do
 if [ "$variant" = before ]; then model=work/ordered-facets/su30sm.dnm; else model=work/large-panels/su30sm.dnm; fi
 cp "$model" "$GAME_RUNTIME/aircraft/su30sm.dnm"
 CHECK_NAME="large-$variant-side-lit" /workspace/work/venv/bin/python work/lab/capture-side-lit.py ground
done
