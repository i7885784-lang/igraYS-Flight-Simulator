"""Keep genuine Windows architectures/resources; replace only exterior DNM/passport."""
from pathlib import Path
import sys,json,zipfile,struct,os
from apply import ROOT,SHA,patch_bytes
TAG='su30sm-recessed-bay-20261114';REPO='i7885784-lang/igraYS-Flight-Simulator';STAMP=(2026,11,14,0,0,0)
BASE='ee1f9324e1c4a46179efd2af2323e5cd0b599e19221e1d8e04910e3332071f27';COCKPIT='564308f1149862461dbc254dfb4372475a067ed0182eb61faf9d7345fa1807b9'
PREVIOUS={'x86':'0c7cfcfedee6fc391216ea8915060c6209cb4b7011e3287d53ef475c2952cde6','x64':'a4a577a23da6ff7dded8e87cf02c41e789c829da453eb0fda5ce9d8308fa66fe'}
def put(z,name,data):
 i=zipfile.ZipInfo(name,STAMP);i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,data,compresslevel=6)
def build(out,prior):
 out.mkdir(parents=True,exist_ok=True);rows=[];model=None;baseline=None
 for arch,machine,magic,bits in [('x86',0x14c,0x10b,32),('x64',0x8664,0x20b,64)]:
  old=prior/f'Su30SM_CockpitFit_Windows_{arch}.zip';assert SHA(old.read_bytes())==PREVIOUS[arch];dest=out/f'Su30SM_RecessedBay_Windows_{arch}.zip'
  with zipfile.ZipFile(old) as zi:
   assert zi.testzip() is None;baseline=zi.read('runtime/aircraft/su30sm.dnm');assert SHA(baseline)==BASE;model=patch_bytes(baseline);cockpit=zi.read('runtime/aircraft/su30smcockpit.dnm');assert SHA(cockpit)==COCKPIT
   passport=json.loads(zi.read('runtime/ARCHITECTURE.json'));exe=zi.read('runtime/'+passport['exe']);off=struct.unpack_from('<I',exe,0x3c)[0];assert struct.unpack_from('<H',exe,off+4)[0]==machine and struct.unpack_from('<H',exe,off+24)[0]==magic
   native=json.loads((ROOT/f'reports/su30sm-recessed-bay/native-{bits}-results.json').read_text());verified=bool(native['passed'] and native['native_windows'] and native['model_sha256']==SHA(model) and native['exe_sha256']==SHA(exe));assert verified
   history=passport.copy();passport.update(model_sha256=SHA(model),cockpit_sha256=COCKPIT,previous_model_sha256=BASE,current_change='Aft fixed skin returned to existing large main doors; matching F4 aperture; five packs only; all original nodes and mechanisms exact',engine_recompiled=False,current_model_native_windows_launch_retested=verified,native_windows_launch_verified=verified,native_windows_run=native['actions_run_url'],historical_passport=history)
   replacements={'runtime/aircraft/su30sm.dnm':model,'runtime/ARCHITECTURE.json':json.dumps(passport,indent=2).encode()}
   with zipfile.ZipFile(dest,'w') as zo:
    for n in zi.namelist():put(zo,n,replacements[n] if n in replacements else zi.read(n))
    put(zo,'runtime/rollback-recessed-bay/su30sm.dnm',baseline)
    put(zo,'README_RECESSED_BAY_RU.txt',f'Су-30СМ: задний выступ обшивки перенесён в большую наружную створку; ниша открывается и закрывается вместе с ней. Оси, родители, анимации, малые створки, стойки, колёса, существующие ниши, кабина и воздухозаборники сохранены. Запуск штатным BAT из полностью распакованного архива. Откат: runtime/rollback-recessed-bay/su30sm.dnm → runtime/aircraft/su30sm.dnm. EXE прежний, архитектура проверена по PE; обе версии запускались на Windows. Подробные сравнения и ограничения: https://github.com/{REPO}/releases/tag/{TAG}\n'.encode())
   with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None;kept=[n for n in zi.namelist() if n not in replacements];assert all(z.read(n)==zi.read(n) for n in kept);assert SHA(z.read('runtime/rollback-recessed-bay/su30sm.dnm'))==BASE;assert not any('TASK_CONTEXT' in n for n in z.namelist())
   rows.append(dict(file=dest.name,sha256=SHA(dest.read_bytes()),bytes=dest.stat().st_size,architecture=arch,PE_machine=hex(machine),optional_header=hex(magic),exe_sha256=SHA(exe),model_sha256=SHA(model),cockpit_sha256=COCKPIT,native_windows_verified=verified,unchanged_previous_entries=len(kept),zip_crc_passed=True))
 source=out/'Su30SM_RecessedBay_ModelSources.zip'
 with zipfile.ZipFile(source,'w') as z:
  for folder in ['changes/su30sm-recessed-bay','changes/su30sm-local-skin/model-source','dist/su30sm-recessed-bay','reports/su30sm-recessed-bay']:
   for f in sorted((ROOT/folder).rglob('*')):
    if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.zip':put(z,str(f.relative_to(ROOT)),f.read_bytes())
    elif f.is_file() and folder.startswith('dist/'):put(z,str(f.relative_to(ROOT)),f.read_bytes())
  for rel in ['changes/su30sm-local-skin/fit_field.py','changes/su30sm-local-skin/requirements.txt','changes/su30sm-local-skin/validation/model.py','changes/su30sm-local-skin/validation/collision.py','changes/su30sm-local-skin/validation/triangles.py','.github/workflows/su30sm-recessed-bay-native.yml']:put(z,rel,(ROOT/rel).read_bytes())
  put(z,'baseline/su30sm.dnm',baseline);put(z,'generated/su30sm.dnm',model)
  put(z,'README_ENGINE_SOURCES.txt',b'Engine unchanged. Full engine source/history/notices: https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/su30sm-local-skin-20261111/Su30SM_LocalSkin_FullSources.zip\n')
 with zipfile.ZipFile(source) as z:assert z.testzip() is None and not any('TASK_CONTEXT' in n for n in z.namelist())
 (out/'packages.json').write_text(json.dumps(rows,indent=2));files=[out/e['file'] for e in rows]+[source];(out/'SHA256SUMS.txt').write_text(''.join(SHA(f.read_bytes())+'  '+f.name+'\n' for f in files));print(json.dumps(rows,indent=2))
if __name__=='__main__':build(Path(sys.argv[1]),Path(sys.argv[2]))
