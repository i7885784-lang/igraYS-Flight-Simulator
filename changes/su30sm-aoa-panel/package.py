from pathlib import Path
import sys,json,zipfile,shutil,subprocess,urllib.request
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'changes/su30sm-high-alpha'))
from build_candidate import source,FILES,MODEL,COCKPIT,pe,SHA
NATIVE_RUN=43701212771
TAG='su30sm-aoa-panel-20261115';REPO='i7885784-lang/igraYS-Flight-Simulator'
OLD={32:('x86','1ecb5b8b5b22a2648d88263c3bbf3ab3d5f52efdaf119057b44b114958b7b226'),64:('x64','27927b0375548ee4c9dc07b003e0ba4dc1bcfa0dc59850c7c120cea01feaf62d')}
STAMP=(2026,11,15,0,0,0)
def put(z,n,b):
 i=zipfile.ZipInfo(n,STAMP);i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,b,compresslevel=6)
def previous(bits):
 arch,sha=OLD[bits];p=ROOT/'work/previous'/f'Su30SM_AOA110_Windows_{arch}.zip';p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  url='https://github.com/'+REPO+'/releases/download/su30sm-aoa110-20261115/'+p.name
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=120) as r,p.open('wb') as f:shutil.copyfileobj(r,f)
 assert SHA(p.read_bytes())==sha;return p
if __name__=='__main__':
 out=ROOT/'work/packages';out.mkdir(parents=True,exist_ok=True);report=ROOT/'reports/su30sm-aoa-panel';engine=source(ROOT/'work/source-package');subprocess.run([sys.executable,str(ROOT/'changes/su30sm-high-alpha/patch.py'),str(engine)],check=True)
 rows=[];models={}
 for bits in [32,64]:
  arch,_=OLD[bits];built=ROOT/f'artifacts/build-{bits}';native=ROOT/f'artifacts/native-{bits}';info=json.loads((built/'build-info.json').read_text());test=json.loads((native/'results.json').read_text());exe=(built/f'ysflight{bits}_gl1.exe').read_bytes();pe(exe,bits)
  assert test['passed'] and test['native_windows'] and test['bits']==bits and info['bits']==bits
  assert SHA(exe)==info['exe_sha256']==test['exe_sha256'] and test['model_sha256']==MODEL and test['cockpit_sha256']==COCKPIT
  assert set(info['source_files'])==set(FILES) and all(SHA((engine/p).read_bytes())==s for p,s in info['source_files'].items())
  if (native/'panel.png').exists():shutil.copyfile(native/'panel.png',report/f'panel-{bits}.png')
  (report/f'native-{bits}-results.json').write_text(json.dumps(test,indent=2));shutil.copyfile(built/'build-info.json',report/f'build-{bits}.json')
  if bits==64:
   hi=[s for s in test['states'] if s['highAlpha']=='1'];peak=max(float(s['aoaDeg']) for s in hi);assert 50<peak<=65.5
   (report/'MEASURED.txt').write_text(f'Actual Windows x64 full-stick peak AOA: {peak:.6f} deg.\nReturn to ordinary mode verified.\nPanel open/edit/reset/close verified. One panel image; no video.\n')
  game=out/f'Su30SM_AOAPanel_Windows_{arch}.zip'
  with zipfile.ZipFile(previous(bits)) as old:
   assert old.testzip() is None;models={n:old.read('runtime/aircraft/'+n) for n in ['su30sm.dnm','su30smcockpit.dnm']};assert SHA(models['su30sm.dnm'])==MODEL and SHA(models['su30smcockpit.dnm'])==COCKPIT
   passport=json.loads(old.read('runtime/ARCHITECTURE.json'));passport.update(exe_sha256=SHA(exe),current_change='Su30 CtrlShiftL compact AOA panel, F7/F8 adjust30..110deg, F9 default65; CtrlL mode and stabilization unchanged',native_windows_launch_verified=True,native_windows_run=f'https://github.com/{REPO}/actions/runs/{NATIVE_RUN}')
   replacements={f'runtime/ysflight{bits}_gl1.exe':exe,'runtime/ARCHITECTURE.json':json.dumps(passport,indent=2).encode(),'runtime/SOURCE_DOWNLOADS.txt':f'Complete corresponding sources and notices: https://github.com/{REPO}/releases/download/{TAG}/Su30SM_AOAPanel_FullSources.zip\n'.encode()}
   with zipfile.ZipFile(game,'w') as z:
    for n in old.namelist():put(z,n,replacements.get(n,old.read(n)))
    for n in replacements:put(z,'runtime/rollback-aoa-panel/'+n,old.read(n))
    put(z,'README_AOAPanel_RU.txt',(ROOT/'changes/su30sm-aoa-panel/README.md').read_bytes())
   with zipfile.ZipFile(game) as z:
    assert z.testzip() is None;kept=[n for n in old.namelist() if n not in replacements];assert all(z.read(n)==old.read(n) for n in kept)
   rows.append(dict(file=game.name,bits=bits,sha256=SHA(game.read_bytes()),bytes=game.stat().st_size,exe_sha256=SHA(exe),model_sha256=MODEL,cockpit_sha256=COCKPIT,native_windows_verified=True,zip_crc_passed=True,unchanged_previous_entries=len(kept),**pe(exe,bits)))
 assert len({r['exe_sha256'] for r in rows})==2
 src=out/'Su30SM_AOAPanel_FullSources.zip'
 with zipfile.ZipFile(src,'w') as z:
  for f in sorted(engine.rglob('*')):
   if f.is_file():put(z,'engine/'+str(f.relative_to(engine)),f.read_bytes())
  for folder in ['changes/su30sm-aoa-panel','changes/su30sm-high-alpha','changes/su30sm-nozzle-vector','changes/su30sm-local-skin/model-source','dist/su30sm-nozzle-vector']:
   for f in sorted((ROOT/folder).rglob('*')):
    if f.is_file() and '__pycache__' not in f.parts and f.name!='evidence.zip':put(z,str(f.relative_to(ROOT)),f.read_bytes())
  for n,b in models.items():put(z,'generated/'+n,b)
  put(z,'REPORT_RU.md',(report/'REPORT_RU.md').read_bytes())
  for n in ['su30sm-aoa-panel-native.yml','su30sm-aoa-panel-publish.yml']:put(z,'.github/workflows/'+n,(ROOT/'.github/workflows'/n).read_bytes())
 with zipfile.ZipFile(src) as z:assert z.testzip() is None
 with zipfile.ZipFile(out/'Su30SM_AOAPanel_Report.zip','w') as z:
  for f in sorted(report.iterdir()):
   if f.is_file():put(z,f.name,f.read_bytes())
 (out/'packages.json').write_text(json.dumps(rows,indent=2));(out/'SHA256SUMS.txt').write_text(''.join(SHA(f.read_bytes())+'  '+f.name+'\n' for f in sorted(out.iterdir()) if f.is_file() and f.name!='SHA256SUMS.txt'));print(json.dumps(rows,indent=2))
