from pathlib import Path
import zipfile,shutil,hashlib,struct,json,subprocess
lab=Path(__file__).resolve().parent;repo=Path('/workspace/igraYS-Flight-Simulator');rt=lab/'runtime';source=repo/'changes/internal-gear-test-3/model-source';dst=rt/'aircraft/fighters-fg-source'
shutil.copytree(source,dst,dirs_exist_ok=True)
shutil.copytree(repo/'changes/internal-gear-test-3/su57-source',rt/'aircraft/su57-source',dirs_exist_ok=True)
(rt/'READ_ME_RU.txt').write_text("Шасси внутри корпуса — тест №3.\nОтдельная полная версия. Распакуйте в новую папку, запустите ysflight32_gl1.exe.\nИсправлены наружные коробки ниш Су-27/МиГ-29, складывание, створки и тяги.\nG — шасси, Alt+5 — фонарь, B — тормоз, F/R — закрылки, Q/A — газ, Tab — форсаж.\nСу-47 и поздняя ревизия Су-57 сохранены. Су-34 в эту публичную сборку не входит.\nГеометрия Су-27/МиГ-29 FGMEMBERS, GPL-2.0; авторы/оригиналы/конвертер: aircraft/fighters-fg-source/NOTICE.txt.\nСу-47 и Су-57 сохраняют GPL-3.0 и свои исходники.\nПроверено Win64/Wine, настоящая Windows 10 x86 здесь не проверялась.\nФото/видео и ограничения: https://github.com/i7885784-lang/igraYS-Flight-Simulator/blob/ysflight-center-download/reports/internal-gear-test-3/REPORT.md\n",encoding='utf-8-sig')
for k in ['su27','mig29']:shutil.copy2(lab/'checks'/(k+'-final-overview')/'start.yfs',rt/(k+'_Test.yfs'))
imports={}
for f in [rt/'ysflight32_gl1.exe',rt/'plugin/sndYsflight32.dll',rt/'plugin/voiceYsflight32.dll']:
 b=f.read_bytes();o=struct.unpack_from('<I',b,0x3c)[0];assert b[o:o+4]==b'PE\0\0' and struct.unpack_from('<H',b,o+4)[0]==0x14c
 if f.suffix=='.exe':assert struct.unpack_from('<H',b,o+24+68)[0]==2 and b'MODELCHECK t=' not in b
 t=subprocess.check_output(['i686-w64-mingw32-objdump','-p',str(f)],text=True);imports[f.name]=[s.split('DLL Name: ')[1].strip() for s in t.splitlines() if 'DLL Name: ' in s];assert not any(s.lower().startswith('lib') for s in imports[f.name])
zip_path=repo/'downloads/YSFlight_Internal_Gear_Test_3_32bit.zip';prefix='YSFlight_Internal_Gear_Test_3_32bit/'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,6) as z:
 for p in sorted(rt.rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts:continue
  if p.suffix.lower()=='.exe' and p.name!='ysflight32_gl1.exe':continue
  if p.suffix.lower()=='.dll' and ('64' in p.name or p.name.startswith('lib')):continue
  z.write(p,prefix+p.relative_to(rt).as_posix())
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 assert [n for n in z.namelist() if n.lower().endswith('.exe')]==[prefix+'ysflight32_gl1.exe']
 for name in ['su47','su57']:
  for filename in [name+'.dat',name+'.dnm',name+'_coarse.dnm',name+'coll.srf',name+'cockpit.srf']:
   assert z.read(prefix+'aircraft/'+filename)==(lab.parent/'fighters-fg-test-2/runtime/aircraft'/filename).read_bytes()
 for name in ['su27','mig29','su57']:
  for filename in [name+'.dat',name+'.dnm',name+'_coarse.dnm',name+'coll.srf',name+'cockpit.srf']:
   assert z.read(prefix+'aircraft/'+filename)==(lab/('su57-source' if name=='su57' else 'model-source')/'runtime/aircraft'/filename).read_bytes()
 count=len(z.namelist());z.extractall(lab/'zip-extracted')
(lab/'package-checks.json').write_text(json.dumps({'passed':True,'zip':zip_path.name,'sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest(),'bytes':zip_path.stat().st_size,'files':count,'imports':imports,'CRC':True,'independent_extraction':True,'Su47_preserved':True,'Su57_latest_revision_included':True,'native_Windows10_x86_run':False},indent=2))
engine=lab.parent/'YSFlight_Su57_Test_2_Engine_Source';sz=repo/'downloads/YSFlight_Internal_Gear_Test_3_Sources.zip';manifest={}
with zipfile.ZipFile(sz,'w',zipfile.ZIP_DEFLATED,6) as z:
 for root,pre in [(engine/'YSFLIGHT/src','engine/YSFLIGHT/src/'),(engine/'public/src','engine/public/src/'),(engine/'YSFLIGHT/scripts','engine/YSFLIGHT/scripts/'),(source,'model-source/'),(rt/'aircraft/su47-source','preserved/su47-source/'),(rt/'aircraft/su57-source','su57-source/')]:
  for p in sorted(root.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts:
    n=pre+p.relative_to(root).as_posix();z.write(p,n);manifest[n]=hashlib.sha256(p.read_bytes()).hexdigest()
 for p in list(engine.glob('LICENSE*'))+[engine/'YSFLIGHT/LICENSE']:
  if p.exists():z.write(p,'engine/'+p.relative_to(engine).as_posix())
 z.write(engine/'mingw32.cmake','mingw32.cmake');z.write(repo/'changes/internal-gear-test-3/native.patch','native.patch')
 z.writestr('SOURCE_MANIFEST.json',json.dumps(manifest,indent=2))
 z.writestr('README_RU.md','Движок уже содержит изменения, native.patch повторно НЕ накладывать.\nМодели: model-source/build_model.py и su57-source/build_model.py; зависимости requirements.txt.\nCMake Release + MinGW i686 POSIX. Точные флаги: changes/internal-gear-test-3/README.md в опубликованном репозитории.\nРесурсы из игрового ZIP положить в engine/YSFLIGHT/runtime, исключив EXE из ресурсов (CMake иначе перезапишет новый EXE).\nЦель ysflight32_gl1. Плагины libsndYsflight32.dll и libvoiceYsflight32.dll переименовать без lib.\nСу-27/МиГ-29 GPL-2.0, см. NOTICE.txt. Су-57 и Су-47 сохраняют GPL-3.0 и авторство, оригиналы включены.\n')
with zipfile.ZipFile(sz) as z:
 assert z.testzip() is None and all(hashlib.sha256(z.read(n)).hexdigest()==sha for n,sha in manifest.items())
(lab/'sources-checks.json').write_text(json.dumps({'passed':True,'files_in_manifest':len(manifest),'sha256':hashlib.sha256(sz.read_bytes()).hexdigest(),'bytes':sz.stat().st_size},indent=2))
print('Game and full source ZIP CRC/manifest passed.')
