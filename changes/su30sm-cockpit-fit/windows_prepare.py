from pathlib import Path
import sys,json,zipfile,subprocess,os
from apply import SHA,models_from_zip
root=Path.cwd();bits=int(sys.argv[1]);arch='x86' if bits==32 else 'x64';name=f'Su30SM_LocalDefects_Windows_{arch}.zip';subprocess.run(['gh','release','download','su30sm-confirmed-defects-20261114','--repo','i7885784-lang/igraYS-Flight-Simulator','--pattern',name,'--dir','downloads'],check=True);p=root/'downloads'/name;entry=next(e for e in json.loads((root/'changes/su30sm-cockpit-fit/previous-packages.json').read_text()) if e['file']==name);assert SHA(p.read_bytes())==entry['sha256']
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None;models=models_from_zip(z);z.extractall(root)
for n,data in models.items():(root/'runtime/aircraft'/n).write_bytes(data)
print('Prepared exact exterior and cockpit models',bits)
