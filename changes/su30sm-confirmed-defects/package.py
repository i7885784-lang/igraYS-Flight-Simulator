"""Apply only the frozen three-pack patch to the last genuine x86/x64 game archives."""
from pathlib import Path
import sys,json,zipfile,hashlib,struct,tempfile,os
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin/model-source'));import dnm
from freeze import apply_delta
TAG='su30sm-confirmed-defects-20261114';REPO='i7885784-lang/igraYS-Flight-Simulator';STAMP=(2026,11,14,0,0,0)
PREVIOUS='91a201f3ca02d7c69345d197827b1567cedcc87edb51409ffc0006b8cc0ae61c';sha=lambda b:hashlib.sha256(b).hexdigest()
def put(z,name,data):
 i=zipfile.ZipInfo(name,STAMP);i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,data,compresslevel=6)
def build(out,prior):
 out.mkdir(parents=True,exist_ok=True);patchdir=ROOT/'dist/su30sm-confirmed-defects';meta=json.loads((patchdir/'metadata.json').read_text());patches={}
 for e in meta['patches']:
  with zipfile.ZipFile(patchdir/e['zip']) as z:data=z.read(e['member'])
  assert sha(data)==e.get('payload_sha256',e['sha256']);patches[e['pack']]=json.loads(data) if e['type']=='face-delta' else data.decode().splitlines()
 rows=[];model=None;previous=None
 for arch,machine,magic in [('x86',0x14c,0x10b),('x64',0x8664,0x20b)]:
  old=prior/f'Su30SM_LargePanels_Windows_{arch}.zip';new=out/f'Su30SM_LocalDefects_Windows_{arch}.zip'
  expected=next(e for e in json.loads((ROOT/'changes/su30sm-confirmed-defects/previous-packages.json').read_text()) if e['file']==old.name);assert sha(old.read_bytes())==expected['sha256']
  with zipfile.ZipFile(old) as zi:
   previous=zi.read('runtime/aircraft/su30sm.dnm');assert sha(previous)==PREVIOUS
   with tempfile.TemporaryDirectory() as td:
    f=Path(td)/'model.dnm';f.write_bytes(previous);p,ns=dnm.read(f);before={k:list(v) for k,v in p.items()};p.update({name:apply_delta(p[name],patch) if isinstance(patch,dict) else patch for name,patch in patches.items()});assert set(k for k in p if p[k]!=before[k])==set(patches);dnm.write(f,p,ns);model=f.read_bytes()
   assert sha(model)==meta['model_sha256']
   passport=json.loads(zi.read('runtime/ARCHITECTURE.json'));exe=zi.read('runtime/'+passport['exe']);pe=struct.unpack_from('<I',exe,0x3c)[0];assert struct.unpack_from('<H',exe,pe+4)[0]==machine and struct.unpack_from('<H',exe,pe+24)[0]==magic
   nativefile=ROOT/f'reports/su30sm-confirmed-defects/native-{32 if arch=="x86" else 64}-results.json';native=json.loads(nativefile.read_text()) if nativefile.exists() else {};verified=bool(native.get('passed') and native.get('native_windows') and native.get('model_sha256')==sha(model) and native.get('exe_sha256')==sha(exe));assert verified or os.environ.get('REQUIRE_NATIVE_CHECKS')!='1';history=passport.copy();passport.update(model_sha256=sha(model),previous_model_sha256=PREVIOUS,current_change='Only two fixed front skin bands and proven imported F4 remnants in the existing outer-door apertures; all moving meshes and all nodes exact',engine_recompiled=False,native_windows_launch_verified=verified,native_windows_run=native.get('actions_run_url'),current_model_native_windows_launch_retested=verified,current_model_visual_check=meta['visual_check']+'; native Windows '+arch+' '+('passed' if verified else 'pending'),check_scope='Both PE architectures, SHA, ZIP CRC, immutable resources; actual Windows x86/x64 launch evidence and x64 Wine keyboard gear cycle; see report.',historical_passport=history)
   with zipfile.ZipFile(new,'w') as zo:
    for n in zi.namelist():put(zo,n,model if n=='runtime/aircraft/su30sm.dnm' else json.dumps(passport,indent=2).encode() if n=='runtime/ARCHITECTURE.json' else zi.read(n))
    put(zo,'runtime/rollback-local-defects/su30sm.dnm',previous)
    put(zo,'README_LOCAL_DEFECTS_RU.txt',f'Локально исправлены передние полосы неподвижной обшивки и остатки корпуса в проёмах основных наружных створок. Створки, стойки, колёса, ниши, воздухозаборники и анимации сохранены. Запуск штатным BAT. Откат: runtime/rollback-local-defects/su30sm.dnm → runtime/aircraft/su30sm.dnm. EXE прежний, архитектура проверена по PE. Реальная проверка игры: обе архитектуры на Windows; x64 также под Wine. Протоколы и кадры в отчёте. https://github.com/{REPO}/releases/tag/{TAG}\n'.encode())
   with zipfile.ZipFile(new) as z:
    assert z.testzip() is None;protected=[n for n in zi.namelist() if n not in ['runtime/aircraft/su30sm.dnm','runtime/ARCHITECTURE.json']];assert all(z.read(n)==zi.read(n) for n in protected)
   rows.append(dict(file=new.name,sha256=sha(new.read_bytes()),bytes=new.stat().st_size,architecture=arch,PE_machine=hex(machine),optional_header=hex(magic),exe_sha256=sha(exe),model_sha256=sha(model),unchanged_previous_entries=len(protected),zip_crc_passed=True))
 source=out/'Su30SM_LocalDefects_ModelSources.zip'
 with zipfile.ZipFile(source,'w') as z:
  for folder in ['changes/su30sm-confirmed-defects','changes/su30sm-large-panels','changes/su30sm-local-skin','reports/su30sm-confirmed-defects','dist/su30sm-confirmed-defects']:
   for f in sorted((ROOT/folder).rglob('*')):
    if f.is_file() and '__pycache__' not in f.parts and 'geometry-cache' not in f.parts:put(z,str(f.relative_to(ROOT)),f.read_bytes())
  put(z,'baseline/su30sm.dnm',previous);put(z,'generated/su30sm.dnm',model);put(z,'README_ENGINE_SOURCES.txt',b'Unchanged engine sources and license history: https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/su30sm-local-skin-20261111/Su30SM_LocalSkin_FullSources.zip\n')
 with zipfile.ZipFile(source) as z:assert z.testzip() is None
 (out/'packages.json').write_text(json.dumps(rows,indent=2));files=[out/e['file'] for e in rows]+[source];(out/'SHA256SUMS.txt').write_text(''.join(sha(f.read_bytes())+'  '+f.name+'\n' for f in files));print(json.dumps(rows,indent=2))
if __name__=='__main__':build(Path(sys.argv[1]),Path(sys.argv[2]))
