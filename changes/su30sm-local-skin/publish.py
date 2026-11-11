"""Publish only frozen validated game files; assemble corresponding sources in CI."""
from pathlib import Path
import zipfile,hashlib,json,subprocess,struct
r=Path.cwd();out=r/'work/delivery';out.mkdir(parents=True,exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest();model=None;base=None
metadata=json.loads((r/'reports/su30sm-local-skin/packages.json').read_text())
for entry in metadata:
 p=r/'dist/su30sm-local-skin'/entry['file'];assert sha(p.read_bytes())==entry['sha256']
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None;data=z.read('runtime/aircraft/su30sm.dnm');assert sha(data)==entry['model_sha256'];model=data;base=z.read('runtime/rollback-local-skin/su30sm.dnm');passport=json.loads(z.read('runtime/ARCHITECTURE.json'));exe=z.read('runtime/'+passport['exe']);assert sha(exe)==entry['exe_sha256'];pe=struct.unpack_from('<I',exe,0x3c)[0];assert struct.unpack_from('<H',exe,pe+4)[0]==int(entry['machine'],16)
legacy=r/'work/legacy-source';legacy.mkdir(exist_ok=True)
subprocess.run(['gh','release','download','personal-su30sm-natural-intake-20261106','--repo','i7885784-lang/igraYS-Flight-Simulator','--pattern','YSFlight_Su30SM_NaturalIntake_FullSources.zip','--dir',str(legacy)],check=True)
legacy=legacy/'YSFlight_Su30SM_NaturalIntake_FullSources.zip'
with zipfile.ZipFile(legacy) as z:assert z.testzip() is None
source=out/'Su30SM_LocalSkin_FullSources.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for folder in ['changes/su30sm-local-skin','changes/su30sm-rear-seams','changes/su30sm-black-wells','reports/su30sm-local-skin']:
  for p in sorted((r/folder).rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts:z.write(p,p.relative_to(r))
 z.writestr('baseline/su30sm.dnm',base);z.writestr('generated/su30sm.dnm',model)
 z.write(legacy,'legacy/'+legacy.name,compress_type=zipfile.ZIP_STORED)
 z.writestr('README.txt','Read changes/su30sm-local-skin/README.md and reports/su30sm-local-skin/REPORT.md. baseline/ is the exact 3d463be runtime model; generated/ is the validated repair. legacy/ preserves the complete unmodified earlier engine/model sources and license notices. Engine EXEs were not rebuilt.\n')
with zipfile.ZipFile(source) as z:assert z.testzip() is None
files=[r/'dist/su30sm-local-skin'/e['file'] for e in metadata]+[source]
(out/'SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in files))
print('All frozen game SHA/PE/CRC checks and source CRC checks passed')
