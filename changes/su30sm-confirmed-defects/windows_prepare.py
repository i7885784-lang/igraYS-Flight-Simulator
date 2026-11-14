"""Prepare one architecture for a real Windows launch using the exact frozen patch."""
from pathlib import Path
import sys,zipfile,json,hashlib,subprocess
ROOT=Path.cwd();HERE=ROOT/'changes/su30sm-confirmed-defects';sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin/model-source'));import dnm
from freeze import apply_delta
bits=int(sys.argv[1]);arch='x86' if bits==32 else 'x64';name=f'Su30SM_LargePanels_Windows_{arch}.zip';subprocess.run(['gh','release','download','su30sm-large-panels-20261113','--repo','i7885784-lang/igraYS-Flight-Simulator','--pattern',name,'--dir','downloads'],check=True);old=ROOT/'downloads'/name;sha=lambda b:hashlib.sha256(b).hexdigest();expected=next(e for e in json.loads((HERE/'previous-packages.json').read_text()) if e['file']==name);assert sha(old.read_bytes())==expected['sha256']
with zipfile.ZipFile(old) as z:z.extractall(ROOT)
f=ROOT/'runtime/aircraft/su30sm.dnm';assert sha(f.read_bytes())=='91a201f3ca02d7c69345d197827b1567cedcc87edb51409ffc0006b8cc0ae61c';p,ns=dnm.read(f);patchdir=ROOT/'dist/su30sm-confirmed-defects';meta=json.loads((patchdir/'metadata.json').read_text())
for e in meta['patches']:
 with zipfile.ZipFile(patchdir/e['zip']) as z:data=z.read(e['member'])
 assert sha(data)==e.get('payload_sha256',e['sha256']);p[e['pack']]=apply_delta(p[e['pack']],json.loads(data)) if e['type']=='face-delta' else data.decode().splitlines()
dnm.write(f,p,ns);f.write_bytes(f.read_bytes().replace(b'\r\n',b'\n'));assert sha(f.read_bytes())==meta['model_sha256'];print('Exact final model',meta['model_sha256'],arch)
