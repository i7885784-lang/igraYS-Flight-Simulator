#!/bin/bash
set -euo pipefail
repo=/workspace/igraYS-Flight-Simulator
dev=/workspace/ysflight-dev
if [ ! -x "$dev/tools/usr/bin/cmake" ]; then
 bash "$repo/reports/environment-2026-10-26/tools/install.sh"
fi
python3 - <<'PY'
from pathlib import Path
import json,hashlib,subprocess,shutil
repo=Path('/workspace/igraYS-Flight-Simulator');dev=Path('/workspace/ysflight-dev');eng=dev/'YSFlight_Su57_Test_2_Engine_Source';source=repo/'changes/su47-test-1'
h=json.loads((source/'engine-hashes.json').read_text());states=[]
for rel,expected in h.items():
 actual=hashlib.sha256((eng/rel).read_bytes()).hexdigest()
 states.append('old' if actual==expected['original'] else 'new' if actual==expected['modified'] else 'unknown')
if all(s=='old' for s in states):subprocess.run(['patch','-p1','--batch','--forward','-i',str(source/'native.patch')],cwd=eng,check=True)
elif not all(s=='new' for s in states):raise RuntimeError('Engine has unrelated changes; preserve and reconcile before setup: '+str(states))
lab=dev/'su47-test-1';lab.mkdir(exist_ok=True)
for name in ['check_game.py','validate.py','package.py']:shutil.copy2(source/name,lab/name)
# Keep editable conversion sources separate from the checkout.
copy=lab/'portable-source'
if not copy.exists():shutil.copytree(source/'model-source',copy)
subprocess.run(['python3','build_model.py'],cwd=copy,check=True)
rt=lab/'runtime'
if not rt.exists():shutil.copytree(dev/'YSFlight_Su57_Test_2_32bit',rt)
for p in (copy/'runtime/aircraft').iterdir():shutil.copy2(p,rt/'aircraft'/p.name)
f=rt/'aircraft/aircraft.lst';line='aircraft/su47.dat aircraft/su47.dnm aircraft/su47coll.srf aircraft/su47_coarse.dnm aircraft/su47cockpit.srf'
if line not in f.read_text():f.write_text(f.read_text()+'\n'+line+'\n')
PY
bash "$dev/build.sh" 32
bash "$dev/build.sh" 64
for bits in 32 64; do
 cp "$dev/YSFlight_Su57_Test_2_Engine_Source/build$bits/main/ysflight${bits}_gl1.exe" "$dev/su47-test-1/runtime/ysflight${bits}_gl1.exe"
 for kind in snd voice; do cp "$dev/YSFlight_Su57_Test_2_Engine_Source/build$bits/main/plugin/${kind}Ysflight$bits.dll" "$dev/su47-test-1/runtime/plugin/${kind}Ysflight$bits.dll"; done
 done
source "$dev/env.sh"
bash "$dev/start.sh"
