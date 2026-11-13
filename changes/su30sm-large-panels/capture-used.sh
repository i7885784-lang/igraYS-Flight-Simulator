set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:232 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :232 -screen 0 1024x768x24 > work/large-panels/xvfb-final.log 2>&1 &
xpid=$!; trap 'kill "$xpid" 2>/dev/null || true' EXIT
export AIRCRAFT_CHECK=SU-30SM_CUSTOM GAME_RUNTIME=/workspace/work/su30sm-local-skin/work/facets-probe/runtime
for variant in after; do
 if [ "$variant" = before ]; then model=work/ordered-facets/su30sm.dnm; else model=work/large-panels/su30sm.dnm; fi
 cp "$model" "$GAME_RUNTIME/aircraft/su30sm.dnm"
 export INVERTED=1
 export CAPS='[["left-closed",90,18,33,"-1.4 -.55 -1.3","0 0 0 0 0 0"],["left-near",98,26,33,"-1.4 -.55 -1.3","0 0 0 0 0 0"],["right-closed",270,18,33,"1.4 -.55 -1.3","0 0 0 0 0 0"],["left-mid",90,18,33,"-1.4 -.55 -1.3",".5 0 0 0 0 0"],["bottom",180,89,80,"0 -.5 -1.4","0 0 0 0 0 0"]]'
 CHECK_NAME="large-$variant-air" /workspace/work/venv/bin/python work/lab/capture.py inspect
 export INVERTED=0
 export CAPS='[["ground-match",90,0,28,"-1.45 -.8 -1.3","1 0 0 0 0 0"],["ground-near",100,2,30,"-1.45 -.8 -1.3","1 0 0 0 0 0"],["ground-mid",90,0,28,"-1.45 -.8 -1.3",".5 0 0 0 0 0"],["ground-left",270,0,28,"1.45 -.8 -1.3","1 0 0 0 0 0"]]'
 CHECK_NAME="large-$variant-ground" /workspace/work/venv/bin/python work/lab/capture.py ground
done

export INVERTED=1 NATIVE_VIEW="90 18 45"
CHECK_NAME=large-native /workspace/work/venv/bin/python work/lab/capture.py gear

export INVERTED=0
export CAPS='[["ground-lit",0,0,28,"-1.45 -.8 -1.3","1 0 0 0 0 0"],["ground-lit-near",10,2,30,"-1.45 -.8 -1.3","1 0 0 0 0 0"],["ground-lit-mid",0,0,28,"-1.45 -.8 -1.3",".5 0 0 0 0 0"]]'
CHECK_NAME=large-after-side-lit /workspace/work/venv/bin/python work/lab/capture-side-lit.py ground
