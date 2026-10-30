from pathlib import Path
import os,json,zipfile,subprocess,tempfile,shutil,hashlib,urllib.request,urllib.error
r=Path.cwd();here=r/'changes/aircraft-personal-test11';repo='i7885784-lang/igraYS-Flight-Simulator';tag='personal-fighters-test11-20261030';sha=lambda b:hashlib.sha256(b).hexdigest()
def gh(*a):return subprocess.check_output(['gh',*a])
release=json.loads(gh('api',f'repos/{repo}/releases/429225685'));assert release['draft']
with tempfile.TemporaryDirectory() as td:
 t=Path(td);gh('release','download','personal-fighters-test10-20261030','--repo',repo,'--pattern','YSFlight_Test_10_All_In_One.zip','--pattern','YSFlight_Personal_Test_10_Sources.zip','--dir',str(t))
 for name,h in [('YSFlight_Test_10_All_In_One.zip','aa901aaf4fb159ce5b0c2a0babf8a3e21156489218ad952d28327339c12cf4a4'),('YSFlight_Personal_Test_10_Sources.zip','3b1a7e3eab48999ab9fb68597514cc9b437d1687174584c3aed571a9bf5e8c8e')]:assert sha((t/name).read_bytes())==h
 game=t/'YSFlight_Test_11_Game';game.mkdir();src=t/'sources';src.mkdir()
 with zipfile.ZipFile(t/'YSFlight_Test_10_All_In_One.zip') as z:
  for n in z.namelist():
   if n.startswith('YSFlight_Test_10/Game/') and not n.endswith('/'):
    p=game/n.removeprefix('YSFlight_Test_10/Game/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
 with zipfile.ZipFile(t/'YSFlight_Personal_Test_10_Sources.zip') as z:z.extractall(src)
 work=src/'test11';shutil.copytree(here,work,ignore=shutil.ignore_patterns('bin','__pycache__'));shutil.copytree(src/'test9/model-source',work/'model-source');(work/'baseline').mkdir();shutil.copy2(game/'aircraft/su34.dnm',work/'baseline/su34.dnm');shutil.copy2(src/'test9/uncut-su34.srf',work/'baseline/uncut-su34.srf')
 subprocess.run(['python',str(work/'fix_su34.py')],check=True)
 for n,h in json.loads((here/'expected.json').read_text()).items():
  b=(work/'runtime/aircraft'/n).read_bytes();assert sha(b)==h;(game/'aircraft'/n).write_bytes(b)
 exe=(here/'bin/ysflight32_gl1.exe').read_bytes();assert sha(exe)==(here/'bin.sha256').read_text().strip();(game/'ysflight32_gl1.exe').write_bytes(exe)
 subprocess.run(['patch','--batch','-p1','-i',str(here/'native.patch')],cwd=src/'engine',check=True)
 for n,h in json.loads((here/'engine-files.json').read_text()).items():assert sha((src/'engine'/n).read_bytes())==h
 (game/'READ_ME_RU.txt').write_text('Личный тест №11 от полной №10. Запуск ysflight32_gl1.exe. Су-34: внутренняя облицовка и стыки створок; пять самолётов: свечение струи, без непрозрачной тени газа. Ctrl+Shift+F9 — диагностика. Права Су-34 не выяснены, НЕ распространять. Источники и авторство сохранены. Проверки Win64/Wine; Windows x86 напрямую не проверялся.\n',encoding='utf-8-sig')
 for n in ['TEST_10_MANIFEST.json']:
  p=game/n
  if p.exists():p.rename(game/'history'/n)
 shutil.copy2(here/'NOTICE.txt',game/'licenses/personal-test11-NOTICE.txt')
 (game/'TEST_11_MANIFEST.json').write_text(json.dumps({'base':10,'models':json.loads((here/'expected.json').read_text()),'win32_sha256':sha(exe),'private_only':True},indent=2))
 shutil.rmtree(work/'runtime');shutil.copy2(src/'SOURCE_MANIFEST.json',src/'history/test10_SOURCE_MANIFEST.json');(src/'SOURCE_MANIFEST.json').write_text(json.dumps({'test':11,'base':10,'engine_files':json.loads((here/'engine-files.json').read_text()),'models':json.loads((here/'expected.json').read_text())},indent=2));(src/'README_RU.md').write_text('Тест №11. Полный движок в engine/. Новая адаптация в test11/, входные файлы сохранены. pip install -r test11/requirements.txt; python test11/fix_su34.py. Сборка движка как test10/BUILD_ENGINE.md. Все старые исходники и лицензии сохранены.\n')
 files=[]
 for name,folder in [('YSFlight_Test_11_Game_32bit.zip',game),('YSFlight_Test_11_Report.zip',r/'reports/personal-playtest-11'),('YSFlight_Personal_Test_11_Sources.zip',src)]:
  out=t/name
  with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for p in sorted(folder.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:z.write(p,folder.name+'/'+str(p.relative_to(folder)))
  with zipfile.ZipFile(out) as z:assert z.testzip() is None
  gh('release','upload',tag,str(out),'--repo',repo);verify=t/'verify';verify.mkdir(exist_ok=True);gh('release','download',tag,'--repo',repo,'--pattern',name,'--dir',str(verify));assert sha((verify/name).read_bytes())==sha(out.read_bytes());url=release['html_url'].replace('/tag/','/download/')+'/'+name
  try:
   urllib.request.urlopen(url+'?privacy='+os.environ['GITHUB_RUN_ID']);raise RuntimeError('Unexpected anonymous access')
  except urllib.error.HTTPError as e:assert e.code==404
  files.append({'name':name,'url':url,'bytes':out.stat().st_size,'sha256':sha(out.read_bytes()),'download_verified':True})
 assert json.loads(gh('api',f'repos/{repo}/releases/429225685'))['draft']
 (r/'reports/personal-playtest-11/STATUS.json').write_text(json.dumps({'draft':True,'assets':files},indent=2)+'\n')
