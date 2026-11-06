set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:221 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :221 -screen 0 1024x768x24 >/tmp/su30-natural221.log 2>&1 &
xpid=$!;trap 'kill "$xpid" 2>/dev/null || true' EXIT
export PYTHONPATH=/workspace/ysflight-dev/python-vendor AIRCRAFT_CHECK=SU-30SM_CUSTOM
export CAPS='[["front-down",180,-8,75,"0 -.4 -.4","1 0 0 0 0 0"],["front-up",180,-8,75,"0 -.4 -.4","0 0 0 0 0 0"],["intake-left",165,-8,22,"-1.1 -.55 .2","1 0 0 0 0 0"],["intake-right",195,-8,22,"1.1 -.55 .2","1 0 0 0 0 0"],["intake-front",180,0,22,"-1.1 -.55 .2","1 0 0 0 0 0"],["intake-below",155,-25,24,"-1.1 -.65 .2","1 0 0 0 0 0"],["intake-side",120,-8,28,"-1.1 -.55 .2","1 0 0 0 0 0"],["intake-right-side",240,-8,28,"1.1 -.55 .2","1 0 0 0 0 0"],["bottom-down",150,-65,100,"0 -.4 -1.5","1 0 0 0 0 0"],["bottom-up",150,-65,100,"0 -.4 -1.5","0 0 0 0 0 0"],["gear-032",140,-35,60,"0 -.4 -2",".32 0 0 0 0 0"],["gear-05",140,-35,60,"0 -.4 -2",".5 0 0 0 0 0"],["main-left",120,-35,30,"-1.9 -.5 -2.7","1 0 0 0 0 0"],["main-right",240,-35,30,"1.9 -.5 -2.7","1 0 0 0 0 0"],["nose-well",145,-45,30,"0 -.4 3.1","1 0 0 0 0 0"],["rear",0,-6,72,"0 -.1 -4","1 0 0 0 0 0"],["nozzles",0,-5,30,"0 -.3 -9.5","0 0 0 0 0 0"],["top",150,65,110,"0 0 -1.3","0 0 0 0 0 0"],["side",90,5,100,"0 0 -1","1 0 0 0 0 0"],["canopy-open",130,15,42,"0 1 3","1 0 1 0 0 0"],["brake-open",40,30,42,"0 1 -.5","1 0 0 1 0 0"]]'
for variant in old-gap before after; do
 case "$variant" in
 old-gap) rt=/workspace/ysflight-dev/su30sm-bay-seams/runtime;;
 before) rt=/workspace/ysflight-dev/su30sm-intake-depth/runtime;;
 after) rt=/workspace/ysflight-dev/su30sm-natural-pass/runtime;;
 esac
 GAME_RUNTIME="$rt" CHECK_NAME="$variant-air" python /workspace/ysflight-dev/su30sm-natural-pass/capture.py inspect
 done
for c in gear canopy brake engine orbit; do
 CHECK_NAME="after-$c" python /workspace/ysflight-dev/su30sm-natural-pass/capture.py "$c"
 done
