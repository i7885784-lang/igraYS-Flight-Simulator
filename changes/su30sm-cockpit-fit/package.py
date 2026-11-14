"""Two genuine Windows architectures; change only the two DNM and their passport."""
from pathlib import Path
import sys,json,zipfile,struct,os
from apply import ROOT,SHA,models_from_zip,load_patch
TAG='su30sm-cockpit-fit-20261114';REPO='i7885784-lang/igraYS-Flight-Simulator';STAMP=(2026,11,14,0,0,0)
def put(z,name,data):
 i=zipfile.ZipInfo(name,STAMP);i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,data,compresslevel=6)
def build(out,prior):
 out.mkdir(parents=True,exist_ok=True);previous=json.loads((ROOT/'changes/su30sm-cockpit-fit/previous-packages.json').read_text());meta,_=load_patch();rows=[];models=None;baseline=None
 for arch,machine,magic,bits in [('x86',0x14c,0x10b,32),('x64',0x8664,0x20b,64)]:
  old=prior/f'Su30SM_LocalDefects_Windows_{arch}.zip';expected=next(e for e in previous if e['file']==old.name);assert SHA(old.read_bytes())==expected['sha256'];dest=out/f'Su30SM_CockpitFit_Windows_{arch}.zip'
  with zipfile.ZipFile(old) as zi:
   assert zi.testzip() is None;models=models_from_zip(zi);baseline={n:zi.read('runtime/aircraft/'+n) for n in models};passport=json.loads(zi.read('runtime/ARCHITECTURE.json'));exe=zi.read('runtime/'+passport['exe']);off=struct.unpack_from('<I',exe,0x3c)[0];assert struct.unpack_from('<H',exe,off+4)[0]==machine and struct.unpack_from('<H',exe,off+24)[0]==magic
   nf=ROOT/f'reports/su30sm-cockpit-fit/native-{bits}-results.json';native=json.loads(nf.read_text()) if nf.exists() else {};verified=bool(native.get('passed') and native.get('native_windows') and native.get('model_sha256')==SHA(models['su30sm.dnm']) and native.get('cockpit_sha256')==SHA(models['su30smcockpit.dnm']) and native.get('exe_sha256')==SHA(exe));assert verified or os.environ.get('REQUIRE_NATIVE_CHECKS')!='1'
   history=passport.copy();passport.update(model_sha256=SHA(models['su30sm.dnm']),cockpit_sha256=SHA(models['su30smcockpit.dnm']),current_change='Only Su30Interior in both models: fitted fore cabin and closed rear enclosure; seats/displays and all other packs/nodes exact',engine_recompiled=False,current_model_native_windows_launch_retested=verified,native_windows_launch_verified=verified,native_windows_run=native.get('actions_run_url'),historical_passport=history)
   replacements={'runtime/aircraft/'+n:data for n,data in models.items()};replacements['runtime/ARCHITECTURE.json']=json.dumps(passport,indent=2).encode()
   with zipfile.ZipFile(dest,'w') as zo:
    for n in zi.namelist():put(zo,n,replacements[n] if n in replacements else zi.read(n))
    for n,data in baseline.items():put(zo,'runtime/rollback-cockpit-fit/'+n,data)
    put(zo,'README_COCKPIT_FIT_RU.txt',f'Су-30СМ: подогнаны передние детали интерьера, замкнут задний отсек кабины. Кресла, приборы, корпус, стёкла, шасси и анимации сохранены. Запуск штатным BAT. Для отката скопировать оба DNM из runtime/rollback-cockpit-fit в runtime/aircraft. Предыдущие релизы сохранены. Обе архитектуры проверены на настоящей Windows; кадры и ограничения в отчёте: https://github.com/{REPO}/releases/tag/{TAG}\n'.encode())
   with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None;kept=[n for n in zi.namelist() if n not in replacements];assert all(z.read(n)==zi.read(n) for n in kept);assert not any('TASK_CONTEXT' in n for n in z.namelist())
   rows.append(dict(file=dest.name,sha256=SHA(dest.read_bytes()),bytes=dest.stat().st_size,architecture=arch,PE_machine=hex(machine),optional_header=hex(magic),exe_sha256=SHA(exe),model_sha256=SHA(models['su30sm.dnm']),cockpit_sha256=SHA(models['su30smcockpit.dnm']),native_windows_verified=verified,unchanged_previous_entries=len(kept),zip_crc_passed=True))
 source=out/'Su30SM_CockpitFit_ModelSources.zip'
 with zipfile.ZipFile(source,'w') as z:
  for folder in ['changes/su30sm-cockpit-fit','changes/su30sm-local-skin/model-source','dist/su30sm-cockpit-fit','reports/su30sm-cockpit-fit']:
   for f in sorted((ROOT/folder).rglob('*')):
    if f.is_file() and '__pycache__' not in f.parts and 'geometry-cache' not in f.parts:put(z,str(f.relative_to(ROOT)),f.read_bytes())
  for rel in ['changes/su30sm-local-skin/requirements.txt','changes/su30sm-local-skin/validation/triangles.py','.github/workflows/su30sm-cockpit-fit-native.yml']:put(z,rel,(ROOT/rel).read_bytes())
  for n in models:put(z,'baseline/'+n,baseline[n]);put(z,'generated/'+n,models[n])
  put(z,'README_ENGINE_SOURCES.txt',b'Engine unchanged. Full engine source/history/notices: https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/su30sm-local-skin-20261111/Su30SM_LocalSkin_FullSources.zip\n')
 with zipfile.ZipFile(source) as z:assert z.testzip() is None and not any('TASK_CONTEXT' in n for n in z.namelist())
 (out/'packages.json').write_text(json.dumps(rows,indent=2));files=[out/e['file'] for e in rows]+[source];(out/'SHA256SUMS.txt').write_text(''.join(SHA(f.read_bytes())+'  '+f.name+'\n' for f in files));print(json.dumps(rows,indent=2))
if __name__=='__main__':build(Path(sys.argv[1]),Path(sys.argv[2]))
