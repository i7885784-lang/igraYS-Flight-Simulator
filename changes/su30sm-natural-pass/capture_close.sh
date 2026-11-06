set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:221 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :221 -screen 0 1024x768x24 >/tmp/su30-natural221b.log 2>&1 &
xpid=$!;trap 'kill "$xpid" 2>/dev/null || true' EXIT
export PYTHONPATH=/workspace/ysflight-dev/python-vendor AIRCRAFT_CHECK=SU-30SM_CUSTOM
export CAPS='[["left-match",165,-8,22,"-1.1 -.55 .2","1 0 0 0 0 0"],["right-match",195,-8,22,"1.1 -.55 .2","1 0 0 0 0 0"],["front",180,-4,55,"0 -.55 -.1","1 0 0 0 0 0"],["left-straight",180,-4,22,"-1.1 -.55 .2","1 0 0 0 0 0"],["right-straight",180,-4,22,"1.1 -.55 .2","1 0 0 0 0 0"],["canopy",130,18,52,"0 1 3","1 1 0 0 0 0"]]'
for variant in old-gap before after; do
 case "$variant" in
 old-gap) rt=/workspace/ysflight-dev/su30sm-bay-seams/runtime;;
 before) rt=/workspace/ysflight-dev/su30sm-intake-depth/runtime;;
 after) rt=/workspace/ysflight-dev/su30sm-natural-pass/runtime;;
 esac
 GAME_RUNTIME="$rt" CHECK_NAME="$variant-ground" python /workspace/ysflight-dev/su30sm-natural-pass/capture.py ground
 done
