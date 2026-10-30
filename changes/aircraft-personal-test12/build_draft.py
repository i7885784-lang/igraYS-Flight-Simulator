from pathlib import Path
import os,json,zipfile,subprocess,tempfile,shutil,hashlib,urllib.request,urllib.error
r=Path.cwd();here=r/'changes/aircraft-personal-test12';repo='i7885784-lang/igraYS-Flight-Simulator';tag='personal-fighters-test12-20261030';sha=lambda b:hashlib.sha256(b).hexdigest()
def gh(*a):return subprocess.check_output(['gh',*a])
release=json.loads(gh('api',f'repos/{repo}/releases/429274288'));assert release['draft']
with tempfile.TemporaryDirectory() as td:
 t=Path(td);gh('release','download','personal-fighters-test11-20261030','--repo',repo,'--pattern','YSFlight_Test_11_Game_32bit.zip','--pattern','YSFlight_Personal_Test_11_Sources.zip','--dir',str(t))
 for name,h in [('YSFlight_Test_11_Game_32bit.zip','13d2357ecfe184ccbaebe9ea3f0b360bcf8574c00be0868d7753f03c24acee82'),('YSFlight_Personal_Test_11_Sources.zip','25a19ef1ee89701dffaec574d13baba0e5f825b103482b1dedd65edf01b5aca3')]:assert sha((t/name).read_bytes())==h
 game=t/'YSFlight_Test_12_Game';game.mkdir();src=t/'sources';src.mkdir()
 with zipfile.ZipFile(t/'YSFlight_Test_11_Game_32bit.zip') as z:
  for n in z.namelist():
   if n.startswith('YSFlight_Test_11_Game/') and not n.endswith('/'):
    p=game/n.removeprefix('YSFlight_Test_11_Game/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
 with zipfile.ZipFile(t/'YSFlight_Personal_Test_11_Sources.zip') as z:z.extractall(t)
 with zipfile.ZipFile(t/'YSFlight_Test_11_Game_32bit.zip') as old:
  for n in old.namelist():
   if n.startswith('YSFlight_Test_11_Game/aircraft/') and not n.endswith('/'):
    assert (game/n.removeprefix('YSFlight_Test_11_Game/')).read_bytes()==old.read(n)
 work=src/'test12';shutil.copytree(here,work,ignore=shutil.ignore_patterns('bin','__pycache__'))
 exe=(here/'bin/ysflight32_gl1.exe').read_bytes();assert sha(exe)==(here/'bin.sha256').read_text().strip();(game/'ysflight32_gl1.exe').write_bytes(exe)
 subprocess.run(['patch','--batch','-p1','-i',str(here/'native.patch')],cwd=src/'engine',check=True)
 for n,h in json.loads((here/'engine-files.json').read_text()).items():assert sha((src/'engine'/n).read_bytes())==h
 (game/'READ_ME_RU.txt').write_text('Личный тест №12 от полной №11. Запуск ysflight32_gl1.exe. Исправлен порядок отрисовки: тени до прозрачных эффектов; тень самолёта больше не закрашивает струю. Геометрия неизменна. Права Су-34 не выяснены, НЕ распространять. Источники и авторство сохранены. Проверки Win64/Wine; Windows x86 напрямую не проверялся.\n',encoding='utf-8-sig')
 for n in ['TEST_11_MANIFEST.json']:
  p=game/n
  if p.exists():p.rename(game/'history'/n)
 shutil.copy2(here/'NOTICE.txt',game/'licenses/personal-test12-NOTICE.txt')
 (game/'TEST_12_MANIFEST.json').write_text(json.dumps({'base':11,'models_unchanged':True,'win32_sha256':sha(exe),'private_only':True},indent=2))
 (src/'history/test11_SOURCE_MANIFEST.json').write_bytes((src/'SOURCE_MANIFEST.json').read_bytes());(src/'SOURCE_MANIFEST.json').write_text(json.dumps({'test':12,'base':11,'engine_files':json.loads((here/'engine-files.json').read_text()),'models_unchanged':True},indent=2));(src/'README_RU.md').write_text('Тест №12: полный движок engine/, патч и проверки test12/. Геометрия точно №11. Сборка движка как test10/BUILD_ENGINE.md. Все прежние исходники и уведомления сохранены.\n')

 files=[]
 for name,folder in [('YSFlight_Test_12_Game_32bit.zip',game),('YSFlight_Test_12_Report.zip',r/'reports/personal-playtest-12'),('YSFlight_Personal_Test_12_Sources.zip',src)]:
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
 assert json.loads(gh('api',f'repos/{repo}/releases/429274288'))['draft']
 (r/'reports/personal-playtest-12/STATUS.json').write_text(json.dumps({'draft':True,'assets':files},indent=2)+'\n')
