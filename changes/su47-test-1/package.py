from pathlib import Path
import zipfile,shutil,hashlib,struct,json,subprocess
lab=Path(__file__).resolve().parent;repo=Path('/workspace/igraYS-Flight-Simulator');rt=lab/'runtime';source=repo/'changes/su47-test-1/model-source';dst=rt/'aircraft/su47-source'
if dst.exists():shutil.rmtree(dst) # Only our generated source bundle, not user runtime data.
shutil.copytree(source,dst)
readme='''Су-47 «Беркут» — отдельный тест №1, основа Су-57 №2.
Распакуйте ВСЮ папку в новое место. Запустите ysflight32_gl1.exe.
Новый полёт → выбрать SU-47_BERKUT → задать карту/старт → Полететь.
Дополнительно: Файл → загрузить Su47_Test.yfs → Взлететь (старт в воздухе).
Су-27, МиГ-29 и Су-57 сохранены. Старую рабочую игру не заменяйте.
G — выпуск/уборка шасси. Alt+5 — фонарь на стоянке/малой скорости.
Стрелки — тангаж/крен; Z/C — руль направления, X — центр; F/R — закрылки.
Q/A — тяга, Tab — форсаж. Для видимого форсажа нужен газ >90%.
Батарея и двигатели сразу готовы, отдельного ручного запуска нет.
Геометрия: Nobatgeldi Geldimammedov, Nobatgeldi/Su_47_Berkut,
commit 70e2a7296ae211e3c1b0b95ff7b4dd3aef622260, GPL-3.0.
Редактируемый MLOD, лицензия и конвертер включены: aircraft/su47-source.
Ресурсы Arma 3 и чужие ракеты/пилот не используются.
Аэродинамика и механизмы — игровые приближения. Сопла не отклоняются.
Проверки механик выполнены отдельной Win64-сборкой под Wine.
На настоящей Windows 10 x86 этот ZIP здесь не запускался.
Отчёт: https://github.com/i7885784-lang/igraYS-Flight-Simulator/blob/ysflight-center-download/reports/su47-test-1/REPORT.md
'''
(rt/'READ_ME_RU.txt').write_text(readme,encoding='utf-8-sig')
shutil.copy2(lab/'checks/inspect/start.yfs',rt/'Su47_Test.yfs')
# PE32 only, Windows GUI, production has no diagnostic interface.
imports={}
for f in [rt/'ysflight32_gl1.exe',rt/'plugin/sndYsflight32.dll',rt/'plugin/voiceYsflight32.dll']:
 b=f.read_bytes();offset=struct.unpack_from('<I',b,0x3c)[0];assert b[offset:offset+4]==b'PE\0\0';assert struct.unpack_from('<H',b,offset+4)[0]==0x14c
 if f.suffix=='.exe':assert struct.unpack_from('<H',b,offset+24+68)[0]==2 and b'MODELCHECK t=' not in b and b'ARMAMENTCHECK time=' not in b
 t=subprocess.check_output(['i686-w64-mingw32-objdump','-p',str(f)],text=True);imports[f.name]=[s.split('DLL Name: ')[1].strip() for s in t.splitlines() if 'DLL Name: ' in s];assert not any(s.lower().startswith('lib') for s in imports[f.name])
zip_path=repo/'downloads/YSFlight_Su47_Test_1_32bit.zip';prefix='YSFlight_Su47_Test_1_32bit/'
files=[]
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,6) as z:
 for p in sorted(rt.rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts:continue
  rel=p.relative_to(rt)
  if p.suffix.lower()=='.exe' and p.name!='ysflight32_gl1.exe':continue
  if p.suffix.lower()=='.dll' and ('64' in p.name or p.name.startswith('lib')):continue
  z.write(p,prefix+rel.as_posix());files.append(rel.as_posix())
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 assert [n for n in z.namelist() if n.lower().endswith('.exe')]==[prefix+'ysflight32_gl1.exe']
 assert not any('64.dll' in n for n in z.namelist())
 for name in ['su27','mig29','su57']:
  for ext in ['dat','dnm','coll.srf']:
   rel=f'aircraft/{name}.{ext}' if ext!='coll.srf' else f'aircraft/{name}coll.srf'
   assert z.read(prefix+rel)==(lab.parent/'YSFlight_Su57_Test_2_32bit'/rel).read_bytes()
 assert 'upstream/Su_47_Berkut.p3d' in '\n'.join(z.namelist())
 for name in ['su47.dat','su47.dnm','su47_coarse.dnm','su47coll.srf','su47cockpit.srf']:assert z.read(prefix+'aircraft/'+name)==(rt/'aircraft'/name).read_bytes()
 extract=lab/'zip-extracted';extract.mkdir(exist_ok=True);z.extractall(extract)
report={'passed':True,'zip':str(zip_path.name),'sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest(),'bytes':zip_path.stat().st_size,'files':len(files),'imports':imports,'CRC':True,'independent_extraction':True,'old_three_preserved':True,'native_Windows10_x86_run':False}
(lab/'package-checks.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
# Complete modified C++ and libraries plus the editable model source.
engine=lab.parent/'YSFlight_Su57_Test_2_Engine_Source';sz=repo/'downloads/YSFlight_Su47_Test_1_Sources.zip';manifest={}
with zipfile.ZipFile(sz,'w',zipfile.ZIP_DEFLATED,6) as z:
 for root,pre in [(engine/'YSFLIGHT/src','engine/YSFLIGHT/src/'),(engine/'public/src','engine/public/src/'),(engine/'YSFLIGHT/scripts','engine/YSFLIGHT/scripts/'),(source,'model-source/')]:
  for p in sorted(root.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts:
    n=pre+p.relative_to(root).as_posix();z.write(p,n);manifest[n]=hashlib.sha256(p.read_bytes()).hexdigest()
 for p in list(engine.glob('LICENSE*'))+[engine/'YSFLIGHT/LICENSE']:
  if p.exists():z.write(p,'engine/'+p.relative_to(engine).as_posix())
 z.write(engine/'mingw32.cmake','mingw32.cmake');z.write(repo/'changes/su47-test-1/native.patch','native.patch')
 z.writestr('SOURCE_MANIFEST.json',json.dumps(manifest,indent=2))
 z.writestr('README_RU.md','Су-47 тест №1. engine/YSFLIGHT/src и engine/public/src уже содержат изменения; native.patch повторно НЕ накладывать.\nМодель: model-source/build_model.py; Python + зависимости requirements.txt. Ресурсы — из игрового ZIP.\nДля сборки C++ разместить ресурсы в engine/YSFLIGHT/runtime, исключив EXE из ресурсов (CMake иначе перезапишет новый EXE).\nCMake Release + MinGW i686 POSIX. Полные проверенные флаги: в changes/su47-test-1/setup.sh и reports/environment-2026-10-26/tools/build.sh опубликованного репозитория.\nЦель ysflight32_gl1. Плагины libsndYsflight32.dll и libvoiceYsflight32.dll переименовать в sndYsflight32.dll и voiceYsflight32.dll.\nОригинальные уведомления авторства в исходниках сохранены. MLOD и модель GPL-3.0 — см. model-source/NOTICE.txt и LICENSE.\n')
with zipfile.ZipFile(sz) as z:
 assert z.testzip() is None
 assert all(hashlib.sha256(z.read(n)).hexdigest()==sha for n,sha in manifest.items())
(lab/'sources-checks.json').write_text(json.dumps({'passed':True,'files_in_manifest':len(manifest),'sha256':hashlib.sha256(sz.read_bytes()).hexdigest(),'bytes':sz.stat().st_size},indent=2))
