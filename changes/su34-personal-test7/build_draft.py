"""Assemble the reviewed two-aircraft test without publicly distributing Su-34."""
from pathlib import Path
import os,sys,json,hashlib,zipfile,tempfile,subprocess,shutil,runpy,urllib.parse,urllib.error,io,struct
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
helper=runpy.run_path(str(REPO/'changes/su34-private-converter/build_private_draft.py'),run_name='private_helpers');request=helper['request'];geometry_digest=helper['geometry_digest'];OWNER=helper['OWNER'];sha=lambda b:hashlib.sha256(b).hexdigest();ident=os.environ.get('RELEASE_ID','427079833');assert ident.isdecimal();api='https://api.github.com/repos/'+OWNER;nonce=os.environ['GITHUB_RUN_ID']
with request(api+'/releases/'+ident) as r:release=json.load(r)
assert release['draft'] is True

def anonymous_status(url):
 try:
  with request(url+('?check=' if '?' not in url else '&check=')+nonce,auth=False) as r:return r.status
 except urllib.error.HTTPError as e:return e.code
assert anonymous_status(release['url'])==404
expected=json.loads((HERE/'expected.json').read_text());assets=[]
def put(z,name,data):
 i=zipfile.ZipInfo(name,(2026,10,28,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,data,compresslevel=6)
with tempfile.TemporaryDirectory(prefix='personal-test7-') as tmp:
 tmp=Path(tmp);work=tmp/'converter';work.mkdir();game=tmp/'YSFlight_Personal_Test_7_32bit';game.mkdir()
 for aid,name,digest in [(685951934,'base-game.zip','e6bf8006ed61d4f494164f4ed3ff4aa13f7e019e9e1b37eb0bf9afa604e82059'),(685952220,'base-sources.zip','eb78299435caefc1cd0f22a224b7557f80ee35d9ef4718ae730fb6079d8aae5b')]:
  with request(api+'/releases/assets/'+str(aid)+'?base='+nonce,accept='application/octet-stream') as r:data=r.read()
  assert sha(data)==digest,'Base archive hash mismatch: '+name;(tmp/name).write_bytes(data)
 with zipfile.ZipFile(tmp/'base-game.zip') as old:
  assert old.testzip() is None;prefix=old.namelist()[0].split('/')[0]
  for n in old.namelist():
   rel=n.split('/',1)[1] if '/' in n else ''
   if rel and not n.endswith('/'):
    assert '..' not in Path(rel).parts;p=game/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old.read(n))
 for f in HERE.rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts:
   p=work/f.relative_to(HERE);p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,p)
 (work/'baseline').mkdir();shutil.copy2(game/'aircraft/su34.dnm',work/'baseline/su34.dnm');assert sha((work/'baseline/su34.dnm').read_bytes())==expected['baseline_su34_sha256']
 with zipfile.ZipFile(tmp/'base-sources.zip') as old:
  assert old.testzip() is None and not any(n.lower().endswith('.ytd') for n in old.namelist())
  yft=old.read('su34-converter/upstream/su34_hi.yft');assert sha(yft)=='83e31ef412b924b65a25aa4b5a49d3363b38fd2dd01c5b89292065130d10af5c'
 (work/'upstream').mkdir();(work/'upstream/su34_hi.yft').write_bytes(yft);(work/'runtime/aircraft').mkdir(parents=True)
 env=dict(os.environ,SU34_CANDIDATE_PATH=str(work/'candidate/aircraft/su34.dnm'))
 for script in ['build.py','nozzles.py']:
  result=subprocess.run([sys.executable,str(work/script)],env=env,capture_output=True,text=True)
  assert result.returncode==0,script+': '+result.stderr[-1500:]
 generated=work/'runtime/aircraft';actual={};exact=True
 for name,digest in expected['reviewed_models_sha256'].items():
  f=generated/name;assert geometry_digest(f)==expected['reviewed_geometry_digest'],'Geometry, topology or state mismatch: '+name
  actual[name]=sha(f.read_bytes());exact=exact and actual[name]==digest;shutil.copy2(f,game/'aircraft'/name)
 preserved={}
 with zipfile.ZipFile(tmp/'base-game.zip') as old:
  for kind in ['su27','mig29','su47','su57']:
   names=[n for n in old.namelist() if n.startswith(prefix+'/aircraft/'+kind) and not n.endswith('/')];assert len(names)>=4
   for n in names:assert (game/n[len(prefix)+1:]).read_bytes()==old.read(n)
   preserved[kind]=len(names)
  assert (game/'ysflight32_gl1.exe').read_bytes()==old.read(prefix+'/ysflight32_gl1.exe')
  for n in ['aircraft/aircraft.lst','aircraft/su34.dat','aircraft/su34coll.srf','aircraft/su34cockpit.srf']:assert (game/n).read_bytes()==old.read(prefix+'/'+n)
 pe=(game/'ysflight32_gl1.exe').read_bytes();off=struct.unpack_from('<I',pe,60)[0];assert pe[off:off+4]==b'PE\0\0' and struct.unpack_from('<H',pe,off+4)[0]==0x14c
 manifest={'test':7,'updated_aircraft':['su34'],'su27_from_reviewed_test6':True,'unchanged_aircraft':preserved,'win32_exe_unchanged':True,'exe_machine':'PE i386 GUI','reviewed_models_reproduced_byte_for_byte':exact,'models_sha256':actual,'reviewed_geometry_digest':expected['reviewed_geometry_digest'],'geometry_position_comparison_m':.00001,'native_windows_10_x86_tested':False,'game_validation':'Win64/Wine; native G down/up, full control endpoints, B airbrake and AB; reviewed video and 360 camera; 401 geometry poses including interpolation','kinematics':'game approximation, not factory verified','private_only_due_to_su34_rights':True}
 (game/'TEST_7_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 (game/'READ_ME_RU.txt').write_text('Личный тест №7: Су-27 + обновлённый Су-34. Распаковать полностью в НОВУЮ папку; Play_Su27.bat / Play_Su34.bat.\nG — шасси, B — воздушное торможение. Су-34: отдельные ниши сбоку корпуса, исправленные стойки/тележки, створки, передняя ниша и сопла. Воздухозаборники и низ двигателей неподвижны. Су-27 сохранён из исправленного теста №6; МиГ-29, Су-47, Су-57 неизменны.\nWin32 GUI EXE. Проверки выполнены Win64/Wine; настоящая Windows 10 x86 здесь не проверялась. Кинематика игровая, заводская точность не заявляется.\nГеометрия Су-34: DEVBenSon/FiveM-Plane-Pack, автор fantazer_rnd. Текстуры, звуки и системы GTA не перенесены. Права распространения/продажи не подтверждены: только личная сборка, не публиковать.\nПолные исходники: YSFlight_Personal_Test_7_Sources.zip в '+release['html_url']+'\n',encoding='utf-8-sig')
 (game/'SOURCE_DOWNLOADS.txt').write_text(release['html_url']+'\nYSFlight_Personal_Test_7_Sources.zip\n')
 shutil.copy2(HERE/'model-source/NOTICE.txt',game/'licenses/su34-prototype-NOTICE.txt')
 archive=tmp/'YSFlight_Personal_Test_7_32bit.zip'
 with zipfile.ZipFile(archive,'w') as z:
  for f in sorted(game.rglob('*')):
   if f.is_file():put(z,game.name+'/'+f.relative_to(game).as_posix(),f.read_bytes())
 sources=tmp/'YSFlight_Personal_Test_7_Sources.zip'
 with zipfile.ZipFile(tmp/'base-sources.zip') as old,zipfile.ZipFile(sources,'w') as z:
  for n in old.namelist():put(z,n,old.read(n))
  for f in sorted(work.rglob('*')):
   rel=f.relative_to(work)
   if f.is_file() and not any(s in ['runtime','candidate','__pycache__'] for s in rel.parts):put(z,'test7-su34/'+rel.as_posix(),f.read_bytes())
 for file in [archive,sources]:
  with zipfile.ZipFile(file) as z:assert z.testzip() is None
  payload=file.read_bytes()
  with request(release['url']+'/assets') as r:existing=json.load(r)
  asset=next((a for a in existing if a['name']==file.name),None)
  if asset is None:
   url='https://uploads.github.com/repos/'+OWNER+'/releases/'+ident+'/assets?name='+urllib.parse.quote(file.name)
   with request(url,payload,content_type='application/zip') as r:asset=json.load(r)
  with request(asset['url']+'?verify='+nonce,accept='application/octet-stream') as r:downloaded=r.read()
  assert sha(downloaded)==sha(payload),'Existing/re-downloaded asset differs; refusing overwrite'
  with zipfile.ZipFile(io.BytesIO(downloaded)) as z:assert z.testzip() is None
  if anonymous_status(asset['url'])!=404 or anonymous_status(asset['browser_download_url'])!=404:
   with request(asset['url'],method='DELETE') as r:pass
   raise RuntimeError('New asset withdrawn: privacy check failed')
  assets.append({'name':file.name,'url':asset['browser_download_url'],'bytes':len(payload),'sha256':sha(payload),'authenticated_download_verified':True,'anonymous_http_status':404});print('Verified personal asset:',file.name,len(payload),flush=True)
 (REPO/'reports/personal-playtest-7/STATUS.json').write_text(json.dumps({'draft':True,'release_url':release['html_url'],'assets':assets,'manifest':manifest},ensure_ascii=False,indent=2)+'\n');print('PASS: two-aircraft personal test ready.',flush=True)
