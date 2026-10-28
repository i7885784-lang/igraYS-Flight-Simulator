"""Reproduce reviewed Su-27 data; assemble and verify a private-only Win32 test."""
from pathlib import Path
import os,sys,json,hashlib,zipfile,tempfile,subprocess,shutil,runpy,urllib.parse,urllib.error
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
helper=runpy.run_path(str(REPO/'changes/su34-private-converter/build_private_draft.py'),run_name='private_helpers');request=helper['request'];OWNER=helper['OWNER'];sha=lambda b:hashlib.sha256(b).hexdigest();ident=os.environ.get('RELEASE_ID','427025255');assert ident.isdecimal();api='https://api.github.com/repos/'+OWNER
with request(api+'/releases/'+ident) as r:release=json.load(r)
assert release['draft'] is True
nonce=os.environ.get('GITHUB_RUN_ID','local')
def anonymous_status(url):
 try:
  with request(url+('?check=' if '?' not in url else '&check=')+nonce,auth=False) as r:return r.status
 except urllib.error.HTTPError as e:return e.code
assert anonymous_status(release['url'])==404,'Draft is anonymously accessible'
expected=json.loads((HERE/'expected.json').read_text());assets=[]
with tempfile.TemporaryDirectory(prefix='personal-test6-') as tmp:
 tmp=Path(tmp);work=tmp/'converter';work.mkdir();game=tmp/'YSFlight_Personal_Test_6_32bit';game.mkdir()
 for aid,name,digest in [(685405315,'base-game.zip','c4a76c33c862a7e58a4d3008d0e4a1dfaab26ad21ae8300f03a7f2e0e7179755'),(685405459,'base-sources.zip','670c91f969565b65c5ee028c43b542b8c04ba5024197a117d579d0d0f4e08623')]:
  with request(api+'/releases/assets/'+str(aid)+'?base='+nonce,accept='application/octet-stream') as r:data=r.read()
  assert sha(data)==digest,'Base archive hash mismatch: '+name
  (tmp/name).write_bytes(data)
 with zipfile.ZipFile(tmp/'base-game.zip') as old:
  assert old.testzip() is None
  prefix=old.namelist()[0].split('/')[0]
  for n in old.namelist():
   rel=n.split('/',1)[1] if '/' in n else ''
   if rel and not n.endswith('/'):
    assert '..' not in Path(rel).parts
    p=game/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old.read(n))
 for f in HERE.rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts:
   p=work/f.relative_to(HERE);p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,p)
 (work/'baseline').mkdir();shutil.copy2(game/'aircraft/su27.dnm',work/'baseline/su27.dnm');assert sha((work/'baseline/su27.dnm').read_bytes())==expected['baseline_su27_sha256']
 (work/'runtime/aircraft').mkdir(parents=True)
 for script in ['repair_su27.py','nozzles.py']:
  result=subprocess.run([sys.executable,str(work/script)],capture_output=True,text=True)
  assert result.returncode==0,script+': '+result.stderr[-1500:]
 for name,digest in expected['models_sha256'].items():
  assert sha((work/'runtime/aircraft'/name).read_bytes())==digest,'Model differs from reviewed bytes: '+name
  shutil.copy2(work/'runtime/aircraft'/name,game/'aircraft'/name)
 preserved={}
 with zipfile.ZipFile(tmp/'base-game.zip') as old:
  for kind in ['su34','mig29','su47','su57']:
   names=[n for n in old.namelist() if n.startswith(prefix+'/aircraft/'+kind) and not n.endswith('/')]
   assert len(names)>=4
   for n in names:assert (game/n[len(prefix)+1:]).read_bytes()==old.read(n)
   preserved[kind]=len(names)
  assert (game/'ysflight32_gl1.exe').read_bytes()==old.read(prefix+'/ysflight32_gl1.exe')
  assert (game/'aircraft/aircraft.lst').read_bytes()==old.read(prefix+'/aircraft/aircraft.lst')
 manifest={'test':6,'updated_aircraft':['su27'],'su34_new_rig_included':False,'unchanged_aircraft':preserved,'win32_exe_unchanged':True,'locally_reviewed_models_reproduced_byte_for_byte':True,'models_sha256':expected['models_sha256'],'native_windows_10_x86_tested':False,'validated':'Win64/Wine; native G down/up, engine states, eight overall views; geometry sweep and original contour comparison','private_only_due_to_su34_rights':True}
 (game/'TEST_6_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 (game/'READ_ME_RU.txt').write_text('Личный тест №6. Распаковать в новую папку. Play_Su27.bat; G — шасси.\nИсправлен Су-27: выступающие стенки ниш, дубли стоек, прилегание передних створок, внутренний проход механизма, сопла и форсаж.\nСу-34 ВКЛЮЧЁН, но пока НЕ обновлён: сохранена модель теста №5, его известные дефекты ещё остаются. МиГ-29, Су-47, Су-57 неизменны.\nПроверки: Win64/Wine. EXE в ZIP — Windows 32-bit. Запуск на настоящей Windows 10 x86 здесь не выполнялся. Кинематика — игровое приближение, не заводская схема.\nПрава Су-34 не выяснены: сборка только личная, не публиковать.\nИсходники: YSFlight_Personal_Test_6_Sources.zip в '+release['html_url']+'\n',encoding='utf-8-sig')
 (game/'SOURCE_DOWNLOADS.txt').write_text(release['html_url']+'\nYSFlight_Personal_Test_6_Sources.zip\n')
 shutil.copy2(HERE/'NOTICE-FGUK.txt',game/'licenses/su27-FGUK-NOTICE.txt')
 archive=tmp/'YSFlight_Personal_Test_6_32bit.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,6) as z:
  for f in sorted(game.rglob('*')):
   if f.is_file():z.write(f,game.name+'/'+f.relative_to(game).as_posix())
 sources=tmp/'YSFlight_Personal_Test_6_Sources.zip'
 with zipfile.ZipFile(tmp/'base-sources.zip') as old,zipfile.ZipFile(sources,'w',zipfile.ZIP_DEFLATED,6) as z:
  assert old.testzip() is None
  for n in old.namelist():z.writestr(n,old.read(n))
  for f in work.rglob('*'):
   rel=f.relative_to(work)
   if f.is_file() and not any(s in ['runtime','__pycache__'] for s in rel.parts):z.write(f,'test6-su27/'+rel.as_posix())
 for file in [archive,sources]:
  with zipfile.ZipFile(file) as z:assert z.testzip() is None
  payload=file.read_bytes()
  with request(release['url']+'/assets') as r:existing=json.load(r)
  assert not any(a['name']==file.name for a in existing),'Refusing to overwrite old asset'
  url='https://uploads.github.com/repos/'+OWNER+'/releases/'+ident+'/assets?name='+urllib.parse.quote(file.name)
  with request(url,payload,content_type='application/zip') as r:asset=json.load(r)
  with request(asset['url']+'?verify='+nonce,accept='application/octet-stream') as r:downloaded=r.read()
  assert sha(downloaded)==sha(payload),'Re-download hash mismatch'
  with zipfile.ZipFile(__import__('io').BytesIO(downloaded)) as z:assert z.testzip() is None
  assert anonymous_status(asset['url'])==404 and anonymous_status(asset['browser_download_url'])==404
  assets.append({'name':file.name,'url':asset['browser_download_url'],'bytes':len(payload),'sha256':sha(payload),'authenticated_download_verified':True,'anonymous_http_status':404})
  print('Uploaded, downloaded and verified:',file.name,len(payload),flush=True)
 out=REPO/'reports/personal-playtest-6/STATUS.json';out.write_text(json.dumps({'draft':True,'release_url':release['html_url'],'assets':assets,'manifest':manifest},ensure_ascii=False,indent=2)+'\n')
 print('PASS: personal test 6 verified.',flush=True)
