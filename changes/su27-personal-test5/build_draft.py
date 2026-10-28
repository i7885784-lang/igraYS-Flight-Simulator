"""Rebuild locally reviewed Su-27; keep the complete Su-34 game draft-only."""
from pathlib import Path
import os,sys,json,hashlib,zipfile,tempfile,subprocess,shutil,runpy,urllib.parse,urllib.error
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
helper=runpy.run_path(str(REPO/'changes/su34-private-converter/build_private_draft.py'),run_name='private_helpers');request=helper['request'];OWNER=helper['OWNER'];sha=lambda b:hashlib.sha256(b).hexdigest();ident=os.environ.get('RELEASE_ID','426818196');assert ident.isdecimal();api='https://api.github.com/repos/'+OWNER
with request(api+'/releases/'+ident) as r:release=json.load(r)
assert release['draft'] is True
# This job runs on GitHub's runner; unlike a credentialed cloud gateway this
# request has a genuinely anonymous route. Fail before handling private geometry.
def anonymous_status(url):
 try:
  with request(url+('?check=' if '?' not in url else '&check=')+os.environ['GITHUB_RUN_ID'],auth=False) as r:return r.status
 except urllib.error.HTTPError as e:return e.code
assert anonymous_status(release['url'])==404
expected=json.loads((HERE/'expected.json').read_text());assets=[]
with tempfile.TemporaryDirectory(prefix='personal-test5-') as tmp:
 tmp=Path(tmp);work=tmp/'converter';work.mkdir();game=tmp/'YSFlight_Personal_Test_5_32bit';game.mkdir()
 for aid,name in [(682412185,'base-game.zip'),(682412416,'base-sources.zip')]:
  with request(api+'/releases/assets/'+str(aid)+'?base='+os.environ['GITHUB_RUN_ID'],accept='application/octet-stream') as r:data=r.read()
  (tmp/name).write_bytes(data)
 with zipfile.ZipFile(tmp/'base-game.zip') as old:
  prefix=old.namelist()[0].split('/')[0]
  for n in old.namelist():
   rel=n.split('/',1)[1] if '/' in n else ''
   if rel and not n.endswith('/'):
    p=game/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old.read(n))
 with zipfile.ZipFile(tmp/'base-sources.zip') as z:
  for n in z.namelist():
   if n.startswith('model-source/') and not n.endswith('/'):
    p=work/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
 for f in HERE.rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts:
   rel=f.relative_to(HERE);p=work/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,p)
 (work/'runtime/aircraft').mkdir(parents=True)
 for name in ['su27.dnm','su27_coarse.dnm']:shutil.copy2(game/'aircraft'/name,work/'runtime/aircraft'/name)
 result=subprocess.run([sys.executable,str(REPO/'changes/aircraft-test-5/repair_brake_seat.py'),str(work)],capture_output=True,text=True)
 assert result.returncode==0,'Brake reconstruction failed: '+result.stderr[-1000:]
 (work/'working-base').mkdir()
 for name,digest in expected['working_base_sha256'].items():
  data=(work/'runtime/aircraft'/name).read_bytes();assert sha(data)==digest,'Working baseline mismatch: '+name; (work/'working-base'/name).write_bytes(data)
 result=subprocess.run([sys.executable,str(work/'make_upper_bay27.py')],capture_output=True,text=True)
 assert result.returncode==0,'Model reconstruction failed: '+result.stderr[-1000:]
 for name,digest in expected['models_sha256'].items():
  p=work/'runtime/aircraft'/name if name.startswith('su27') else game/'aircraft'/name
  assert sha(p.read_bytes())==digest,'Model differs from the locally reviewed one: '+name
 for name in ['su27.dnm','su27_coarse.dnm']:shutil.copy2(work/'runtime/aircraft'/name,game/'aircraft'/name)
 # Everything else, including Su-34 and the shipping Win32 EXE, is unchanged.
 preserved={}
 with zipfile.ZipFile(tmp/'base-game.zip') as old:
  for kind in ['su34','mig29','su47','su57']:
   names=[n for n in old.namelist() if n.startswith(prefix+'/aircraft/'+kind) and not n.endswith('/')]
   for n in names:assert (game/n[len(prefix)+1:]).read_bytes()==old.read(n)
   preserved[kind]=len(names)
  assert (game/'ysflight32_gl1.exe').read_bytes()==old.read(prefix+'/ysflight32_gl1.exe')
 readme='Личный промежуточный тест №5. Полностью распаковать в новую папку. Play_Su27.bat, G — выпуск/уборка.\nОбновлён Су-27: узкие отдельные створки, внутренние ниши, связанная стойка и складные тяги.\nСу-34 пока прежний, из теста №4: новый механизм НЕ включён, его проблемы ещё не объявлены исправленными. МиГ-29, Су-47, Су-57 сохранены.\nИгра проверялась Win64/Wine; поставляется самостоятельный Win32 GUI EXE. Windows 10 x86 здесь не проверялась.\nНе публиковать: права на геометрию Су-34 не подтверждены. Источники и лицензии сохранены; текстуры/звуки/системы GTA не переносились.\nИсходники этой версии: YSFlight_Personal_Test_5_Sources.zip в '+release['html_url']+'\n'
 (game/'READ_ME_RU.txt').write_text(readme,encoding='utf-8-sig');(game/'SOURCE_DOWNLOADS.txt').write_text(release['html_url']+'\nYSFlight_Personal_Test_5_Sources.zip\n')
 shutil.copy2(HERE/'NOTICE-FGUK.txt',game/'licenses/su27-FGUK-NOTICE.txt')
 manifest={'test':5,'new_su34_rig_included':False,'preserved_aircraft':preserved,'win32_exe_unchanged':True,'locally_reviewed_models_reproduced_byte_for_byte':True,'models_sha256':expected['models_sha256'],'native_windows_10_x86_tested':False,'game_validation':'Win64/Wine, native G both directions, 401 geometric poses including interpolation; reviewed movement frames','source':'GPL notices and original resources retained in corresponding source ZIP'}
 (game/'TEST_5_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 archive=tmp/'YSFlight_Personal_Test_5_32bit.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,6) as z:
  for f in sorted(game.rglob('*')):
   if f.is_file():z.write(f,game.name+'/'+f.relative_to(game).as_posix())
 sources=tmp/'YSFlight_Personal_Test_5_Sources.zip'
 with zipfile.ZipFile(tmp/'base-sources.zip') as old,zipfile.ZipFile(sources,'w',zipfile.ZIP_DEFLATED,6) as z:
  for n in old.namelist():z.writestr(n,old.read(n))
  for f in work.rglob('*'):
   rel=f.relative_to(work)
   if f.is_file() and not any(s in ['runtime','__pycache__'] for s in rel.parts):z.write(f,'test5-su27/'+rel.as_posix())
 for f in [archive,sources]:
  with zipfile.ZipFile(f) as z:assert z.testzip() is None
 # Only the two private ZIPs are uploaded. Su-27 media contain no Su-34 resources.
 for file in [archive,sources]:
  payload=file.read_bytes()
  with request(release['url']+'/assets') as r:existing=json.load(r)
  assert not any(a['name']==file.name for a in existing),'Refusing to overwrite an existing test asset'
  url='https://uploads.github.com/repos/'+OWNER+'/releases/'+ident+'/assets?name='+urllib.parse.quote(file.name)
  with request(url,payload,content_type='application/zip') as r:asset=json.load(r)
  with request(asset['url']+'?verify='+os.environ['GITHUB_RUN_ID'],accept='application/octet-stream') as r:downloaded=r.read()
  assert sha(downloaded)==sha(payload),'Authenticated re-download mismatch'
  assert anonymous_status(asset['url'])==404 and anonymous_status(asset['browser_download_url'])==404,'Asset is not private'
  assets.append({'name':file.name,'url':asset['browser_download_url'],'bytes':len(payload),'sha256':sha(payload),'authenticated_download_verified':True,'anonymous_http_status':404})
  print('Uploaded, re-downloaded and verified private:',file.name,len(payload),flush=True)
 out=REPO/'reports/personal-playtest-5/STATUS.json';out.write_text(json.dumps({'draft':True,'release_url':release['html_url'],'assets':assets,'manifest':manifest},ensure_ascii=False,indent=2)+'\n')
 print('PASS: private test ready, models match local reviewed bytes; no anonymous asset access.',flush=True)
