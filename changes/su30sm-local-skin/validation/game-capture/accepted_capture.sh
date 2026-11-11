set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:210 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
"$WINESERVER" -k || true
Xvfb :210 -screen 0 1024x768x24 > /workspace/work/xvfb210.log 2>&1 &
xpid=$!; trap 'kill "$xpid" 2>/dev/null || true' EXIT
export AIRCRAFT_CHECK=SU-30SM_CUSTOM
for variant in after; do
 if [ "$variant" = before ]; then export GAME_RUNTIME=/workspace/work/su30sm-local-skin/work/before/runtime; else export GAME_RUNTIME=/workspace/work/su30sm-local-skin/work/candidate/runtime; fi
 export INVERTED=1
 export CAPS='[["screen-match",195,75,62,"0 -.3 -1.5","0 0 0 0 0 0"],["near-left",185,65,58,"0 -.3 -1.5","0 0 0 0 0 0"],["near-right",205,65,58,"0 -.3 -1.5","0 0 0 0 0 0"],["left-close",195,65,28,"-1.45 -.6 -1.6","0 0 0 0 0 0"],["right-close",165,65,28,"1.45 -.6 -1.6","0 0 0 0 0 0"],["bottom",180,89,90,"0 -.3 -1.5","0 0 0 0 0 0"],["mid",195,75,62,"0 -.3 -1.5",".5 0 0 0 0 0"],["down",195,75,62,"0 -.3 -1.5","1 0 0 0 0 0"],["phase020",195,75,62,"0 -.3 -1.5",".2 0 0 0 0 0"],["phase085",195,75,62,"0 -.3 -1.5",".85 0 0 0 0 0"],["left-close-mid",195,65,28,"-1.45 -.6 -1.6",".5 0 0 0 0 0"],["right-close-mid",165,65,28,"1.45 -.6 -1.6",".5 0 0 0 0 0"],["rear-bottom",15,40,90,"0 -.3 -1.5","0 0 0 0 0 0"]]'
 CHECK_NAME="$variant-accepted-belly" /workspace/work/venv/bin/python /workspace/work/su30sm-local-skin/work/lab/capture.py inspect
 export INVERTED=0
 export CAPS='[["top",180,89,175,"0 0 0","0 0 0 0 0 0"],["side-left",90,0,140,"0 0 0","0 0 0 0 0 0"],["side-right",270,0,140,"0 0 0","0 0 0 0 0 0"],["bottom",180,-89,175,"0 0 0","1 0 0 0 0 0"],["front",180,0,140,"0 0 0","1 0 0 0 0 0"],["rear",0,0,140,"0 0 0","1 0 0 0 0 0"]]'
 CHECK_NAME="$variant-accepted-overall" /workspace/work/venv/bin/python /workspace/work/su30sm-local-skin/work/lab/capture.py inspect
done
for variant in before after; do
 if [ "$variant" = before ]; then export GAME_RUNTIME=/workspace/work/su30sm-local-skin/work/before/runtime; else export GAME_RUNTIME=/workspace/work/su30sm-local-skin/work/candidate/runtime; fi
 export INVERTED=1 NATIVE_VIEW='195 65 62'
 CHECK_NAME="$variant-native-accepted" /workspace/work/venv/bin/python /workspace/work/su30sm-local-skin/work/lab/capture.py gear
done
