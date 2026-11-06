set -eu
. /workspace/ysflight-dev/env.sh
export DISPLAY=:221 XDG_RUNTIME_DIR=/tmp/ysflight-runtime
Xvfb :221 -screen 0 1024x768x24 >/tmp/su30-natural221c.log 2>&1 &
xpid=$!;trap 'kill "$xpid" 2>/dev/null || true' EXIT
export PYTHONPATH=/workspace/ysflight-dev/python-vendor AIRCRAFT_CHECK=SU-30SM_CUSTOM
export CAPS='[["full-front",180,0,110,"0 0 0","1 0 0 0 0 0"],["full-top",180,89,175,"0 0 0","0 0 0 0 0 0"],["full-side",90,0,130,"0 0 0","1 0 0 0 0 0"],["full-bottom-up",180,-89,175,"0 0 0","0 0 0 0 0 0"],["full-bottom-down",180,-89,175,"0 0 0","1 0 0 0 0 0"],["full-rear",0,0,110,"0 0 0","1 0 0 0 0 0"],["quarter-front",135,23,120,"0 0 0","1 0 0 0 0 0"],["quarter-rear",45,23,120,"0 0 0","1 0 0 0 0 0"]]'
for variant in before after; do
 case "$variant" in before) rt=/workspace/ysflight-dev/su30sm-intake-depth/runtime;; after) rt=/workspace/ysflight-dev/su30sm-natural-pass/runtime;; esac
 GAME_RUNTIME="$rt" CHECK_NAME="$variant-overview" python /workspace/ysflight-dev/su30sm-natural-pass/capture.py inspect
 done
