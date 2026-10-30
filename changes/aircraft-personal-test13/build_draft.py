from pathlib import Path
import os,json,zipfile,subprocess,tempfile,shutil,hashlib,urllib.request,urllib.error
r=Path.cwd();here=r/'changes/aircraft-personal-test13';repo='i7885784-lang/igraYS-Flight-Simulator';tag='personal-fighters-test13-20261030';sha=lambda b:hashlib.sha256(b).hexdigest();expected=json.loads((here/'expected.json').read_text())
def gh(*a):return subprocess.check_output(['gh',*a])
release=json.loads(gh('api',f'repos/{repo}/releases/429320349'));assert release['draft']
with tempfile.TemporaryDirectory() as td:
 t=Path(td);gh('release','download','personal-fighters-test12-20261030','--repo',repo,'--pattern','YSFlight_Test_12_Game_32bit.zip','--pattern','YSFlight_Personal_Test_12_Sources.zip','--dir',str(t))
 for name,h in [('YSFlight_Test_12_Game_32bit.zip','4f62ee9655925720e441785cee8d24da9e86d5e8e66bb92e426669897dc83452'),('YSFlight_Personal_Test_12_Sources.zip','7874271fc064198a3fd04f19fa51fa95fcede12bd4497d40d9f822a9dd77ac4b')]:assert sha((t/name).read_bytes())==h
 game=t/'YSFlight_Test_13_Game';game.mkdir()
 with zipfile.ZipFile(t/'YSFlight_Test_12_Game_32bit.zip') as z:
  for n in z.namelist():
   if n.startswith('YSFlight_Test_12_Game/') and not n.endswith('/'):
    p=game/n.removeprefix('YSFlight_Test_12_Game/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
 with zipfile.ZipFile(t/'YSFlight_Personal_Test_12_Sources.zip') as z:z.extractall(t)
 src=t/'sources';work=src/'test13';shutil.copytree(here,work,ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(src/'test9/model-source',work/'model-source');(work/'baseline').mkdir();shutil.copy2(game/'aircraft/su27.dnm',work/'baseline/su27.dnm');(work/'upstream').mkdir();ac=src/'test6-su27/model-source/upstream/su27/Su-27.ac';assert sha(ac.read_bytes())==expected['upstream_ac'];shutil.copy2(ac,work/'upstream/Su-27.ac')
 subprocess.run(['python',str(work/'fix_su27.py')],check=True)
 subprocess.run(['python',str(work/'audit.py')],check=True);assert json.loads((work/'collision-checks.json').read_text())['passed']
 for n in ['su27.dnm','su27_coarse.dnm']:
  data=(work/'runtime/aircraft'/n).read_bytes();assert sha(data)==expected[n],n;(game/'aircraft'/n).write_bytes(data)
 unchanged=0
 with zipfile.ZipFile(t/'YSFlight_Test_12_Game_32bit.zip') as z:
  for n in z.namelist():
   rel=n.removeprefix('YSFlight_Test_12_Game/')
   if n.endswith('/') or rel in ['aircraft/su27.dnm','aircraft/su27_coarse.dnm']:continue
   if rel.startswith('aircraft/') or rel=='ysflight32_gl1.exe':assert (game/rel).read_bytes()==z.read(n);unchanged+=1
 (game/'history/TEST_12_MANIFEST.json').write_bytes((game/'TEST_12_MANIFEST.json').read_bytes());(game/'TEST_12_MANIFEST.json').unlink();(game/'TEST_13_MANIFEST.json').write_text(json.dumps({'base':12,'models':expected,'engine_unchanged':True,'other_aircraft_files_unchanged':unchanged,'su27_collision_poses':401},indent=2));(game/'READ_ME_RU.txt').write_text('Личный тест №13 от полной №12. Запуск ysflight32_gl1.exe. Су-27: внутренние стенки основных ниш закрывают просвет над створками на обеих сторонах. Старые поверхности, механизм, движок и остальные самолёты сохранены. Ctrl+Shift+F9 — диагностика. Авторство и исходники сохранены. Полная игра только для личного теста: права Су-34 не выяснены, не распространять.\n',encoding='utf-8-sig');shutil.copy2(here/'NOTICE.txt',game/'licenses/personal-test13-NOTICE.txt');shutil.rmtree(work/'runtime');(src/'history/test12_SOURCE_MANIFEST.json').write_bytes((src/'SOURCE_MANIFEST.json').read_bytes());(src/'SOURCE_MANIFEST.json').write_text(json.dumps({'test':13,'base':12,'engine_unchanged':True,'models':expected},indent=2));(src/'README_RU.md').write_text('Тест №13. Полный неизменный движок №12 в engine/. Новая адаптация test13/: pip install -r test13/requirements.txt; python test13/fix_su27.py; python test13/audit.py. Первичная геометрия и все прошлые исходники сохранены.\n')
 files=[]
 for name,folder in [('YSFlight_Test_13_Game_32bit.zip',game),('YSFlight_Test_13_Report.zip',r/'reports/personal-playtest-13'),('YSFlight_Personal_Test_13_Sources.zip',src)]:
  out=t/name
  with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for p in sorted(folder.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:z.write(p,folder.name+'/'+str(p.relative_to(folder)))
  with zipfile.ZipFile(out) as z:assert z.testzip() is None
  gh('release','upload',tag,str(out),'--repo',repo);verify=t/'verify';verify.mkdir(exist_ok=True);gh('release','download',tag,'--repo',repo,'--pattern',name,'--dir',str(verify));assert sha((verify/name).read_bytes())==sha(out.read_bytes());url=release['html_url'].replace('/tag/','/download/')+'/'+name
  try:urllib.request.urlopen(url+'?privacy='+os.environ['GITHUB_RUN_ID']);raise RuntimeError('Unexpected anonymous access')
  except urllib.error.HTTPError as e:assert e.code==404
  files.append({'name':name,'url':url,'bytes':out.stat().st_size,'sha256':sha(out.read_bytes()),'download_verified':True})
 assert json.loads(gh('api',f'repos/{repo}/releases/429320349'))['draft']
 (r/'reports/personal-playtest-13/STATUS.json').write_text(json.dumps({'draft':True,'assets':files},indent=2)+'\n')
