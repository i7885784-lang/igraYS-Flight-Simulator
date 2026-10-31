from pathlib import Path
import os,json,zipfile,subprocess,tempfile,shutil,hashlib,urllib.request,urllib.error
from fingerprints import zero_hash
r=Path.cwd();here=r/'changes/aircraft-personal-test15';repo='i7885784-lang/igraYS-Flight-Simulator';tag='personal-fighters-test15-20261031';release_id=429728766;sha=lambda b:hashlib.sha256(b).hexdigest();expected=json.loads((here/'expected.json').read_text())
def gh(*a):return subprocess.check_output(['gh',*a])
release=json.loads(gh('api',f'repos/{repo}/releases/{release_id}'));assert release['draft'];prefix=release['html_url'].replace('/tag/','/download/')
with tempfile.TemporaryDirectory() as td:
 t=Path(td);gh('release','download','personal-fighters-test14-20261030','--repo',repo,'--pattern','YSFlight_Test_14_Game_32bit.zip','--pattern','YSFlight_Personal_Test_14_Sources.zip','--dir',str(t))
 for name,h in [('YSFlight_Test_14_Game_32bit.zip','13da537ad055b0902e69d6ff2c23bee84fdde3714f44ea608c5f75fc28d869a3'),('YSFlight_Personal_Test_14_Sources.zip','9e12f712d356bf984ecdf48c67675354f4047834d4df4b85ec4fd5cb396c6bc8')]:assert sha((t/name).read_bytes())==h
 game=t/'YSFlight_Test_15_Game';game.mkdir()
 with zipfile.ZipFile(t/'YSFlight_Test_14_Game_32bit.zip') as z:
  for n in z.namelist():
   if n.startswith('YSFlight_Test_14_Game/') and not n.endswith('/'):
    p=game/n.removeprefix('YSFlight_Test_14_Game/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
 with zipfile.ZipFile(t/'YSFlight_Personal_Test_14_Sources.zip') as z:z.extractall(t)
 src=t/'sources';work=src/'test15';shutil.copytree(here,work,ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(src/'test9/model-source',work/'model-source');(work/'baseline').mkdir();(work/'upstream/su27').mkdir(parents=True)
 for k in ['su27','su34','mig29','su47','su57']:shutil.copy2(game/'aircraft'/f'{k}.dnm',work/'baseline'/f'{k}.dnm')
 ref=src/'test13/upstream/Su-27.ac';assert sha(ref.read_bytes())==expected['su27_ac'];shutil.copy2(ref,work/'upstream/su27/Su-27.ac')
 subprocess.run(['python',str(work/'build_models.py')],check=True);subprocess.run(['python',str(work/'run_checks.py')],check=True)
 changed=[]
 for k in ['su27','su34','mig29','su47']:
  for n in [k+'.dnm',k+'_coarse.dnm']:
   data=(work/'runtime/aircraft'/n).read_bytes();print('MODEL HASH',n,sha(data),'local',expected[n],flush=True);assert sha(data)==expected[n] or zero_hash(data)==expected['zero_normalized'][n],n;(game/'aircraft'/n).write_bytes(data);changed.append('aircraft/'+n)
 unchanged=0
 with zipfile.ZipFile(t/'YSFlight_Test_14_Game_32bit.zip') as z:
  for n in z.namelist():
   rel=n.removeprefix('YSFlight_Test_14_Game/')
   if n.endswith('/') or rel in changed:continue
   if rel.startswith('aircraft/') or rel=='ysflight32_gl1.exe':assert (game/rel).read_bytes()==z.read(n);unchanged+=1
 history=game/'history';history.mkdir(exist_ok=True);shutil.move(str(game/'TEST_14_MANIFEST.json'),str(history/'TEST_14_MANIFEST.json'));(game/'TEST_15_MANIFEST.json').write_text(json.dumps({'base':14,'models':expected,'engine_unchanged':True,'unchanged_aircraft_and_exe_files':unchanged,'changed_files':changed},indent=2))
 (game/'READ_ME_RU.txt').write_text('Личный тест №15 от полной №14. Запуск ysflight32_gl1.exe. Су-27/Су-34: стыки и шарниры; Су-47: внутренние выступы; МиГ-29: закрытие внутреннего края ниш. Исправлены оси управляющих поверхностей, фонарей и тормоза Су-27/МиГ. G — шасси, F/R — закрылки, B — воздушный тормоз, Alt+5 — фонарь, Ctrl+Shift+F9 — диагностика, повторное нажатие её отключает. Внешняя исходная обшивка, Су-57, сопла/струя и движок сохранены. Снимки, видео, подробности в отдельном отчёте. Полная сборка остаётся для личного теста, статус прав Су-34 не изменён.\n',encoding='utf-8-sig')
 (game/'SOURCE_DOWNLOADS.txt').write_text('Complete corresponding sources for personal test15:\n'+prefix+'/YSFlight_Personal_Test_15_Sources.zip\n\nReport/photos/videos:\nhttps://github.com/'+repo+'/blob/ysflight-center-download/reports/personal-playtest-15/README.md\n',encoding='utf-8');shutil.copy2(here/'NOTICE.txt',game/'licenses/personal-test15-NOTICE.txt');shutil.rmtree(work/'runtime');shutil.rmtree(work/'baseline-runtime')
 (src/'history/test14_SOURCE_MANIFEST.json').write_bytes((src/'SOURCE_MANIFEST.json').read_bytes());(src/'SOURCE_MANIFEST.json').write_text(json.dumps({'test':15,'base':14,'engine_unchanged':True,'models':expected},indent=2));(src/'README_RU.md').write_text('Тест №15. Полный неизменный движок №14 в engine/. Новая адаптация test15/: pip install -r test15/requirements.txt; python test15/build_models.py; python test15/run_checks.py. Исходники/авторство/все прежние конвертеры сохранены.\n')
 files=[]
 for name,folder in [('YSFlight_Test_15_Game_32bit.zip',game),('YSFlight_Test_15_Report.zip',r/'reports/personal-playtest-15'),('YSFlight_Personal_Test_15_Sources.zip',src)]:
  out=t/name
  with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for p in sorted(folder.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:z.write(p,folder.name+'/'+str(p.relative_to(folder)))
  with zipfile.ZipFile(out) as z:assert z.testzip() is None
  gh('release','upload',tag,str(out),'--repo',repo);verify=t/'verify';verify.mkdir(exist_ok=True);gh('release','download',tag,'--repo',repo,'--pattern',name,'--dir',str(verify));assert sha((verify/name).read_bytes())==sha(out.read_bytes());url=prefix+'/'+name
  try:urllib.request.urlopen(url+'?privacy='+os.environ['GITHUB_RUN_ID']);raise RuntimeError('Unexpected anonymous access')
  except urllib.error.HTTPError as e:assert e.code==404
  files.append({'name':name,'url':url,'bytes':out.stat().st_size,'sha256':sha(out.read_bytes()),'download_verified':True})
 assert json.loads(gh('api',f'repos/{repo}/releases/{release_id}'))['draft'];(r/'reports/personal-playtest-15/STATUS.json').write_text(json.dumps({'draft':True,'assets':files},indent=2)+'\n')
