from pathlib import Path
import sys,zipfile,json,shutil
from prepare import ROOT,META,SHA,old_game,pe
bits=int(sys.argv[1]);prior=old_game(bits,ROOT/'downloads');built=ROOT/'work/built';info=json.loads((built/'build-info.json').read_text());assert info['bits']==bits and info['model_sha256']==META['model_sha256']
with zipfile.ZipFile(prior) as z:assert z.testzip() is None;z.extractall(ROOT)
model=(built/'su30sm.dnm').read_bytes();exe=(built/f'ysflight{bits}_gl1.exe').read_bytes();assert SHA(model)==META['model_sha256'] and SHA(exe)==info['exe_sha256'];pe(exe,bits)
(ROOT/'runtime/aircraft/su30sm.dnm').write_bytes(model);(ROOT/f'runtime/ysflight{bits}_gl1.exe').write_bytes(exe);assert SHA((ROOT/'runtime/aircraft/su30smcockpit.dnm').read_bytes())==META['cockpit_sha256']
print('Native Windows fixture ready',bits)
