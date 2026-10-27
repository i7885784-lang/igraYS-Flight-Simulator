from pathlib import Path
import shutil,json,hashlib,zipfile
lab=Path(__file__).resolve().parent;repo=Path('/workspace/igraYS-Flight-Simulator');change=repo/'changes/internal-gear-test-3a';rep=repo/'reports/internal-gear-test-3a';change.mkdir(parents=True,exist_ok=True);rep.mkdir(parents=True,exist_ok=True)
shutil.copytree(lab/'model-source',change/'model-source',ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
for fn in ['verify_lighting.py','package.py']:shutil.copy2(lab/fn,change/fn)
shutil.copy2(lab/'lighting-checks.json',rep/'lighting-checks.json')
for kind in ['su27','mig29']:
 dest=rep/kind;dest.mkdir(exist_ok=True)
 for fn in ['bottom.png','inverted.png','quarter-135.png']:shutil.copy2(lab/'checks'/(kind+'-door-lighting')/fn,dest/fn)
change.joinpath('README.md').write_text('''# Освещение створок — уточнение теста №3

Исправлены обращённые внутрь нормали наружных панелей Су-27/МиГ-29.
Положение геометрии и все анимации побайтно/геометрически сверены с тестом №3.
Игра и исходники выпущены новыми файлами; предыдущие архивы сохранены.
Конвертер `model-source/build_model.py`, зависимости `requirements.txt`.
Авторство и GPL-2.0 сохранены в NOTICE.txt и upstream. Движок прежний, от
Aircraft Fixes Test 2. Описание полного теста: ../internal-gear-test-3/README.md.
''')
rt=lab/'runtime';shutil.copytree(change/'model-source',rt/'aircraft/fighters-fg-source',dirs_exist_ok=True)
(rt/'READ_ME_RU.txt').write_text('''Шасси внутри корпуса, тест №3а: исправлено освещение внешних створок Су-27/МиГ-29.
Распакуйте всю папку в новое место, запустите ysflight32_gl1.exe. G — шасси.
Механизмы/остальные самолёты прежние от теста №3. Су-34 в публичной сборке отсутствует.
Авторы, оригиналы, GPL и конвертеры: aircraft/*-source/NOTICE.txt.
Проверено Win64/Wine; настоящая Windows 10 x86 не проверялась.
Отчёт: https://github.com/i7885784-lang/igraYS-Flight-Simulator/blob/ysflight-center-download/reports/internal-gear-test-3a/REPORT.md
''',encoding='utf-8-sig')
name='YSFlight_Internal_Gear_Test_3a_32bit';game=repo/'downloads'/(name+'.zip')
with zipfile.ZipFile(game,'w',zipfile.ZIP_DEFLATED,6) as z:
 for p in sorted(rt.rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts:continue
  if p.suffix=='.exe' and p.name!='ysflight32_gl1.exe':continue
  if p.suffix=='.dll' and ('64' in p.name or p.name.startswith('lib')):continue
  z.write(p,name+'/'+p.relative_to(rt).as_posix())
with zipfile.ZipFile(game) as z:
 assert z.testzip() is None
 for kind in ['su47','su57']:
  for fn in [kind+'.dat',kind+'.dnm',kind+'_coarse.dnm',kind+'cockpit.srf',kind+'coll.srf']:assert z.read(name+'/aircraft/'+fn)==(lab.parent/'internal-gear-test-3/runtime/aircraft'/fn).read_bytes()
 assert z.read(name+'/ysflight32_gl1.exe')==(lab.parent/'internal-gear-test-3/runtime/ysflight32_gl1.exe').read_bytes()
 z.extractall(lab/'zip-extracted')
# Keep the exact PUBLIC engine from the old public source archive, not the private Su-34 working tree.
source=repo/'downloads/YSFlight_Internal_Gear_Test_3a_Sources.zip';manifest={}
with zipfile.ZipFile(repo/'downloads/YSFlight_Internal_Gear_Test_3_Sources.zip') as old,zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,6) as z:
 for item in old.infolist():
  if item.filename.startswith('model-source/') or item.filename=='SOURCE_MANIFEST.json':continue
  data=old.read(item.filename);z.writestr(item.filename,data)
  if item.filename not in ['mingw32.cmake','native.patch','README_RU.md']:manifest[item.filename]=hashlib.sha256(data).hexdigest()
 for p in sorted((change/'model-source').rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts:
   path='model-source/'+p.relative_to(change/'model-source').as_posix();data=p.read_bytes();z.writestr(path,data);manifest[path]=hashlib.sha256(data).hexdigest()
 z.writestr('SOURCE_MANIFEST.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(source) as z:assert z.testzip() is None and all(hashlib.sha256(z.read(n)).hexdigest()==s for n,s in manifest.items())
checks={'passed':True,'Su47_and_Su57_unchanged':True,'public_Win32_EXE_unchanged':True,'no_Su34_resources':not any(p.name.startswith('su34') for p in rt.rglob('*')),'downloads':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'CRC':True} for p in [game,source]}}
assert checks['no_Su34_resources'];(rep/'package-checks.json').write_text(json.dumps(checks,indent=2));print('Packaged public 3a; original public engine and preserved aircraft verified.')
rep.joinpath('REPORT.md').write_text('''# Уточнение теста №3: освещение створок

У Су-27 и МиГ-29 исправлена ориентация наружных панелей ниш: снаружи теперь
видна внешняя окраска, внутри — тёмная внутренняя. Положение деталей и
движение шасси не менялись. Старые архивы сохранены.

[Полная игра Windows 32-bit](https://raw.githubusercontent.com/i7885784-lang/igraYS-Flight-Simulator/ysflight-center-download/downloads/YSFlight_Internal_Gear_Test_3a_32bit.zip) ·
[Все исходники](https://raw.githubusercontent.com/i7885784-lang/igraYS-Flight-Simulator/ysflight-center-download/downloads/YSFlight_Internal_Gear_Test_3a_Sources.zip) ·
[Механизмы и видео теста №3](../internal-gear-test-3/REPORT.md).

| Су-27, низ обращён к солнцу | МиГ-29, низ обращён к солнцу |
|---|---|
| ![Су-27](su27/inverted.png) | ![МиГ-29](mig29/inverted.png) |

Проверено: один общий осмотр каждого самолёта и нижняя обшивка при перевороте;
[направление поверхностей и неизменность движения](lighting-checks.json),
[целостность архивов и сохранение остальных самолётов](package-checks.json).
Кадры реальные, Win64/Wine; настоящая Windows 10 x86 здесь не проверялась.
Су-34 в эту публичную сборку не включён.
''')
