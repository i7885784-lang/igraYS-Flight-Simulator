"""Assemble four frozen surface patches into genuine separate x86/x64 archives."""
from pathlib import Path
import sys,json,zipfile,hashlib,struct,tempfile
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin/model-source'));import dnm
TAG='su30sm-large-panels-20261113';REPO='i7885784-lang/igraYS-Flight-Simulator';STAMP=(2026,11,13,0,0,0)
PREVIOUS='8f0b40ea8897103c9756c1b08471d1525275adc9267030b239c0d95351257422';CLEAN='6f8e20b21990820dcc3aa49f91e92ef4a1771047951671f61732d111256b30c6'
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(z,name,data):
 i=zipfile.ZipInfo(name,STAMP);i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,data,compresslevel=6)
def build(out,prior):
 out.mkdir(parents=True,exist_ok=True);patchdir=ROOT/'dist/su30sm-large-panels';meta=json.loads((patchdir/'metadata.json').read_text());patches={}
 for entry in meta['patches']:
  with zipfile.ZipFile(patchdir/entry['zip']) as z:data=z.read(entry['pack']);assert sha(data)==entry['sha256'];patches[entry['pack']]=data.decode().splitlines()
 rows=[];model=None;previous=None;clean=None
 for arch,machine,magic in [('x86',0x14c,0x10b),('x64',0x8664,0x20b)]:
  old=prior/f'Su30SM_OrderedFacets_Windows_{arch}.zip';new=out/f'Su30SM_LargePanels_Windows_{arch}.zip'
  with zipfile.ZipFile(old) as zi:
   previous=zi.read('runtime/aircraft/su30sm.dnm');clean=zi.read('runtime/rollback-ordered-facets/su30sm.dnm');assert sha(previous)==PREVIOUS and sha(clean)==CLEAN
   with tempfile.TemporaryDirectory() as td:
    f=Path(td)/'model.dnm';f.write_bytes(previous);p,ns=dnm.read(f);before={k:list(v) for k,v in p.items()};p.update(patches);assert set(k for k in p if p[k]!=before[k])==set(patches);dnm.write(f,p,ns);model=f.read_bytes()
   assert sha(model)==meta['model_sha256']
   a=json.loads(zi.read('runtime/ARCHITECTURE.json'));exe=zi.read('runtime/'+a['exe']);pe=struct.unpack_from('<I',exe,0x3c)[0];assert struct.unpack_from('<H',exe,pe+4)[0]==machine and struct.unpack_from('<H',exe,pe+24)[0]==magic
   oldpass=a.copy();a.update(model_sha256=sha(model),previous_model_sha256=PREVIOUS,current_change='Four confirmed local skin/shutter surfaces; all other 158 PCKs and all 162 node records exact',engine_recompiled=False,native_windows_launch_verified=False,native_windows_run=None,current_model_native_windows_launch_retested=False,current_model_visual_check='x64 OpenGL Wine: actual closed and ground gear-down cameras, near angles and intermediate poses; x86 not launched',check_scope='Both PE architectures, resources, SHA and CRC; actual game x64 Wine only',historical_passport=oldpass)
   with zipfile.ZipFile(new,'w') as zo:
    for n in zi.namelist():put(zo,n,model if n=='runtime/aircraft/su30sm.dnm' else json.dumps(a,indent=2).encode() if n=='runtime/ARCHITECTURE.json' else zi.read(n))
    put(zo,'runtime/rollback-large-panels/su30sm.dnm',previous)
    put(zo,'README_LARGE_PANELS_RU.txt',f'Крупные грани MainBayFixedSkin_Left/Right и MainWheelBayShutter_Left/Right. Оси, родители, зазоры, стойки, колёса, ниши и анимационные записи сохранены. Запуск штатным BAT. Откат: заменить runtime/aircraft/su30sm.dnm копией runtime/rollback-large-panels/su30sm.dnm. EXE неизменны. Игра проверена x64 под Wine; x86 и нативная Windows заново не запускались. Источники/отчёт: https://github.com/{REPO}/releases/tag/{TAG}\n'.encode())
   with zipfile.ZipFile(new) as z:
    assert z.testzip() is None;protected=[n for n in zi.namelist() if n not in ['runtime/aircraft/su30sm.dnm','runtime/ARCHITECTURE.json']];assert all(z.read(n)==zi.read(n) for n in protected)
   rows.append(dict(file=new.name,sha256=sha(new.read_bytes()),bytes=new.stat().st_size,architecture=arch,PE_machine=hex(machine),optional_header=hex(magic),exe_sha256=sha(exe),model_sha256=sha(model),unchanged_previous_entries=len(protected),zip_crc_passed=True))
 source=out/'Su30SM_LargePanels_ModelSources.zip'
 with zipfile.ZipFile(source,'w') as z:
  for folder in ['changes/su30sm-large-panels','changes/su30sm-local-skin','reports/su30sm-large-panels','dist/su30sm-large-panels']:
   for f in sorted((ROOT/folder).rglob('*')):
    if f.is_file() and '__pycache__' not in f.parts and 'geometry-cache' not in f.parts:put(z,str(f.relative_to(ROOT)),f.read_bytes())
  put(z,'baseline/su30sm.dnm',clean);put(z,'previous/su30sm.dnm',previous);put(z,'generated/su30sm.dnm',model);put(z,'TASK_CONTEXT.md',(ROOT/'TASK_CONTEXT.md').read_bytes());put(z,'README_ENGINE_SOURCES.txt',b'New stage: changes/su30sm-large-panels/README.md. Complete unchanged engine sources and license history: https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/su30sm-local-skin-20261111/Su30SM_LocalSkin_FullSources.zip\n')
 with zipfile.ZipFile(source) as z:assert z.testzip() is None
 (out/'packages.json').write_text(json.dumps(rows,indent=2));files=[out/e['file'] for e in rows]+[source];(out/'SHA256SUMS.txt').write_text(''.join(sha(f.read_bytes())+'  '+f.name+'\n' for f in files));print(json.dumps(rows,indent=2))
if __name__=='__main__':build(Path(sys.argv[1] if len(sys.argv)>1 else ROOT/'work/large-packages'),Path(sys.argv[2] if len(sys.argv)>2 else ROOT/'work/ordered-downloaded'))
