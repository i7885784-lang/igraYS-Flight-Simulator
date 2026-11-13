"""Build two real architecture ZIPs using only the validated frozen one-PCK patch."""
from pathlib import Path
import sys,json,zipfile,hashlib,struct,tempfile
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin/model-source'));import dnm
TAG='su30sm-ordered-facets-20261113';REPO='i7885784-lang/igraYS-Flight-Simulator';BASE='6f8e20b21990820dcc3aa49f91e92ef4a1771047951671f61732d111256b30c6';TARGET='MainBayFixedSkin_Left.srf';STAMP=(2026,11,13,0,0,0)
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(z,name,data):
 info=zipfile.ZipInfo(name,STAMP);info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data,compresslevel=6)
def build(out):
 out.mkdir(parents=True,exist_ok=True)
 update=zipfile.ZipFile(ROOT/'dist/su30sm-ordered-facets/ModelUpdate.zip');meta=json.loads(update.read('metadata.json'));patch=update.read(TARGET).decode().splitlines();rows=[];model=None;baseline=None
 for arch,machine,magic in [('x86',0x14c,0x10b),('x64',0x8664,0x20b)]:
  old=ROOT/f'dist/su30sm-local-skin/Su30SM_LocalSkin_Windows_{arch}.zip';new=out/f'Su30SM_OrderedFacets_Windows_{arch}.zip'
  with zipfile.ZipFile(old) as zi:
   baseline=zi.read('runtime/aircraft/su30sm.dnm');assert sha(baseline)==BASE
   with tempfile.TemporaryDirectory() as td:
    file=Path(td)/'model.dnm';file.write_bytes(baseline);p,ns=dnm.read(file);p[TARGET]=patch;dnm.write(file,p,ns);model=file.read_bytes()
   assert sha(model)==meta['model_sha256']
   a=json.loads(zi.read('runtime/ARCHITECTURE.json'));exe=zi.read('runtime/'+a['exe']);pe=struct.unpack_from('<I',exe,0x3c)[0];assert struct.unpack_from('<H',exe,pe+4)[0]==machine and struct.unpack_from('<H',exe,pe+24)[0]==magic
   oldpass=a.copy();a.update(model_sha256=sha(model),previous_model_sha256=BASE,current_change='Ordered planes only on MainBayFixedSkin_Left; all 161 other PCKs and all 162 node records exact',engine_recompiled=False,native_windows_launch_verified=False,native_windows_run=None,current_model_native_windows_launch_retested=False,current_model_visual_check='x64 OpenGL Wine, six matched camera/gear poses; x86 not launched',check_scope='Both PE architectures, SHA and CRC checked; actual game check x64 Wine only',historical_passport=oldpass)
   with zipfile.ZipFile(new,'w') as zo:
    for name in zi.namelist():put(zo,name,model if name=='runtime/aircraft/su30sm.dnm' else json.dumps(a,indent=2).encode() if name=='runtime/ARCHITECTURE.json' else zi.read(name))
    put(zo,'runtime/rollback-ordered-facets/su30sm.dnm',baseline)
    put(zo,'README_ORDERED_FACETS_RU.txt',f'Локально изменена только неподвижная MainBayFixedSkin_Left. Все створки/шасси/ниши/анимации сохранены. Створка в выделенной области остаётся более гладкой согласно запрету. Запуск штатным BAT; откат заменой runtime/aircraft/su30sm.dnm из runtime/rollback-ordered-facets/su30sm.dnm. EXE не пересобирался. Проверка игры: x64 под Wine; x86 и нативная Windows заново не запускались. Отчёт и исходники: https://github.com/{REPO}/releases/tag/{TAG}\n'.encode())
   with zipfile.ZipFile(new) as z:
    assert z.testzip() is None;names=[n for n in zi.namelist() if n not in ['runtime/aircraft/su30sm.dnm','runtime/ARCHITECTURE.json']];assert all(zi.read(n)==z.read(n) for n in names)
   rows.append({'file':new.name,'sha256':sha(new.read_bytes()),'bytes':new.stat().st_size,'architecture':arch,'PE_machine':hex(machine),'optional_header':hex(magic),'exe_sha256':sha(exe),'model_sha256':sha(model),'unchanged_original_entries':len(names),'zip_crc_passed':True})
 # This archive covers the new model stage; complete unchanged engine sources remain public.
 sources=out/'Su30SM_OrderedFacets_ModelSources.zip'
 with zipfile.ZipFile(sources,'w') as z:
  for folder in ['changes/su30sm-ordered-facets','changes/su30sm-local-skin','reports/su30sm-ordered-facets']:
   for file in sorted((ROOT/folder).rglob('*')):
    if file.is_file() and '__pycache__' not in file.parts and 'geometry-cache' not in file.parts:put(z,str(file.relative_to(ROOT)),file.read_bytes())
  put(z,'baseline/su30sm.dnm',baseline);put(z,'generated/su30sm.dnm',model);put(z,'dist/su30sm-ordered-facets/ModelUpdate.zip',(ROOT/'dist/su30sm-ordered-facets/ModelUpdate.zip').read_bytes());put(z,'TASK_CONTEXT.md',(ROOT/'TASK_CONTEXT.md').read_bytes())
  put(z,'README_ENGINE_SOURCES.txt',b'New stage: changes/su30sm-ordered-facets/README.md. Complete unchanged engine/model source history and licenses: https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/su30sm-local-skin-20261111/Su30SM_LocalSkin_FullSources.zip\n')
 with zipfile.ZipFile(sources) as z:assert z.testzip() is None
 (out/'packages.json').write_text(json.dumps(rows,indent=2));files=[out/e['file'] for e in rows]+[sources];(out/'SHA256SUMS.txt').write_text(''.join(sha(f.read_bytes())+'  '+f.name+'\n' for f in files));print(json.dumps(rows,indent=2))
if __name__=='__main__':build(Path(sys.argv[1] if len(sys.argv)>1 else ROOT/'work/ordered-packages'))
