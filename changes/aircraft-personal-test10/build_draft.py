"""Reproduce test 10, include an offline mobile report, upload only to a private draft."""
from pathlib import Path
import os,sys,json,hashlib,zipfile,tempfile,subprocess,shutil,runpy,urllib.parse,urllib.error,io,struct
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];helper=runpy.run_path(str(REPO/'changes/su34-private-converter/build_private_draft.py'),run_name='helpers');request=helper['request'];OWNER=helper['OWNER'];sha=lambda b:hashlib.sha256(b).hexdigest();api='https://api.github.com/repos/'+OWNER;nonce=os.environ['GITHUB_RUN_ID'];ident=os.environ['RELEASE_ID'];expected=json.loads((HERE/'expected.json').read_text())
with request(api+'/releases/'+ident) as f:release=json.load(f)
assert release['draft'] is True

def anonymous(url):
 try:
  with request(url+('?v=' if '?' not in url else '&v=')+nonce,auth=False) as f:return f.status
 except urllib.error.HTTPError as e:return e.code
assert anonymous(release['url'])==404

def put(z,name,data):
 info=zipfile.ZipInfo(name,(2026,10,30,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data,compresslevel=6)
with tempfile.TemporaryDirectory(prefix='personal-test10-') as tmp:
 tmp=Path(tmp);work=tmp/'test10';bundle=tmp/'YSFlight_Test_10';game=bundle/'Game';game.mkdir(parents=True)
 for what in ['archive','sources']:
  with request(api+'/releases/assets/'+str(expected['baseline_'+what+'_asset'])+'?base='+nonce,accept='application/octet-stream') as f:data=f.read()
  assert sha(data)==expected['baseline_'+what+'_sha256'];(tmp/(what+'.zip')).write_bytes(data)
 with zipfile.ZipFile(tmp/'archive.zip') as old:
  assert old.testzip() is None;prefix=old.namelist()[0].split('/')[0]
  for n in old.namelist():
   rel=n.split('/',1)[1] if '/' in n else ''
   if rel and not n.endswith('/'):
    assert '..' not in Path(rel).parts;p=game/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old.read(n))
 shutil.copytree(HERE,work,ignore=shutil.ignore_patterns('bin','__pycache__'));(work/'baseline').mkdir()
 for n,digest in expected['baseline_models'].items():
  data=(game/'aircraft'/n).read_bytes();assert sha(data)==digest;(work/'baseline'/n).write_bytes(data)
 result=subprocess.run([sys.executable,str(work/'build.py')],capture_output=True,text=True,env=dict(os.environ,OPENBLAS_NUM_THREADS='1'));assert result.returncode==0,result.stderr[-2500:]
 assert sha((work/'fsexhaustprofile.h').read_bytes())==expected['profile_header_sha256'],'Profile/engine table mismatch'
 result=subprocess.run([sys.executable,str(work/'validate.py')],capture_output=True,text=True,env=dict(os.environ,OPENBLAS_NUM_THREADS='1'));assert result.returncode==0,result.stderr[-2500:];print(result.stdout,flush=True)
 for n,digest in expected['models'].items():
  data=(work/'runtime/aircraft'/n).read_bytes();assert sha(data)==digest,'Model mismatch '+n;(game/'aircraft'/n).write_bytes(data)
 exe=(HERE/'bin/ysflight32_gl1.exe').read_bytes();assert sha(exe)==expected['win32_exe_sha256'];off=struct.unpack_from('<I',exe,60)[0];assert exe[off:off+4]==b'PE\0\0' and struct.unpack_from('<H',exe,off+4)[0]==0x14c and b'MODELPOSE' not in exe;(game/'ysflight32_gl1.exe').write_bytes(exe)
 unchanged=0
 with zipfile.ZipFile(tmp/'archive.zip') as old:
  for n in old.namelist():
   rel=n[len(prefix)+1:]
   if rel.startswith('aircraft/') and not n.endswith('/') and Path(rel).name not in expected['models']:assert (game/rel).read_bytes()==old.read(n);unchanged+=1
 for p in game.glob('TEST_*_MANIFEST.json'):
  (game/'history').mkdir(exist_ok=True);p.rename(game/'history'/p.name)
 report=REPO/'reports/personal-playtest-10/mobile';report_files=json.loads((HERE/'report-files.json').read_text())
 for rel,digest in report_files.items():
  data=(report/rel).read_bytes();assert sha(data)==digest,'Report mismatch '+rel;p=bundle/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 (bundle/'SOURCE_DOWNLOADS.txt').write_text(release['html_url']+'\nYSFlight_Personal_Test_10_Sources.zip\n')
 (game/'SOURCE_DOWNLOADS.txt').write_text(release['html_url']+'\nYSFlight_Personal_Test_10_Sources.zip\n')
 (game/'READ_ME_RU.txt').write_text('Личный тест №10. Струя следует за выходным сечением сопла на Су-27, МиГ-29, Су-34, Су-47 и Су-57; у Су-57 также за отклонением. Остальная геометрия и анимации сохранены из №9.\nОтчёт REPORT.pdf, фотографии Photos и видео Video находятся на уровень выше папки Game.\nQ/A — газ, Tab — форсаж. Ctrl+Shift+F9 — диагностика вкл/выкл. Windows 32-bit; игровые проверки Win64/Wine, Windows x86 напрямую не запускался.\nПрава распространения геометрии Су-34 не подтверждены: сборка только личная. Авторы и лицензии сохранены. Источник Су-34: fantazer_rnd / DEVBenSon/FiveM-Plane-Pack. Новых текстур/звуков/систем GTA нет.\n',encoding='utf-8-sig');shutil.copy2(HERE/'NOTICE.txt',game/'licenses/personal-test10-NOTICE.txt')
 manifest={'test':10,'baseline':9,'models_sha256':expected['models'],'win32_exe_sha256':expected['win32_exe_sha256'],'profile_header_sha256':expected['profile_header_sha256'],'unchanged_other_aircraft_files':unchanged,'offline_report':True,'all_non_plume_meshes_and_all_nodes_unchanged':True,'report_files':report_files,'validation_platform':'Win64/Wine; Windows 10 x86 not directly executed','private_only_due_to_su34_rights':True}
 (game/'TEST_10_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 archive=tmp/'YSFlight_Test_10_All_In_One.zip'
 with zipfile.ZipFile(archive,'w') as z:
  for p in sorted(bundle.rglob('*')):
   if p.is_file():put(z,bundle.name+'/'+p.relative_to(bundle).as_posix(),p.read_bytes())
 # The complete source snapshot and all older converters remain available.
 with zipfile.ZipFile(tmp/'sources.zip') as old:
  assert old.testzip() is None and not any(n.lower().endswith('.ytd') for n in old.namelist())
  for n in old.namelist():
   if n.startswith('engine/') and not n.endswith('/'):
    assert '..' not in Path(n).parts;p=tmp/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old.read(n))
 result=subprocess.run(['patch','--batch','-p1','-i',str(HERE/'native.patch')],cwd=tmp/'engine',capture_output=True,text=True);assert result.returncode==0,result.stdout+result.stderr
 patched=json.loads((HERE/'engine-files.json').read_text())
 for rel,digest in patched.items():assert sha((tmp/'engine'/rel).read_bytes())==digest,rel
 sources=tmp/'YSFlight_Personal_Test_10_Sources.zip'
 with zipfile.ZipFile(tmp/'sources.zip') as old,zipfile.ZipFile(sources,'w') as z:
  old_names=set(old.namelist())
  for n in old.namelist():
   if n=='README_RU.md':put(z,'history/test9_README_RU.md',old.read(n))
   elif n=='SOURCE_MANIFEST.json':put(z,'history/test9_SOURCE_MANIFEST.json',old.read(n))
   elif n.startswith('engine/') and n[7:] in patched:put(z,n,(tmp/n).read_bytes())
   else:put(z,n,old.read(n))
  for rel in patched:
   if 'engine/'+rel not in old_names:put(z,'engine/'+rel,(tmp/'engine'/rel).read_bytes())
  for p in sorted(work.rglob('*')):
   rel=p.relative_to(work)
   if p.is_file() and not any(v in ['runtime','__pycache__'] for v in rel.parts):put(z,'test10/'+rel.as_posix(),p.read_bytes())
  put(z,'SOURCE_MANIFEST.json',json.dumps({'test':10,'base_source_archive_sha256':expected['baseline_sources_sha256'],'engine_changed_files':patched,'models':expected['models'],'profile_header_sha256':expected['profile_header_sha256']},indent=2).encode())
  put(z,'README_RU.md','Исходники теста №10. engine/ — полный движок. test10/ — конвертер и пять исходных DNM №9. Прежние конвертеры и исходный YFT сохранены в старых каталогах.\nПересборка: pip install -r test10/requirements.txt; python test10/build.py. Генерируется fsexhaustprofile.h из реальных выходных кромок моделей: он должен совпадать с engine/YSFLIGHT/src/vehicle/fsexhaustprofile.h. При дальнейших изменениях сопел обновляйте и модели, и этот заголовок.\nПроверка геометрии: python test10/validate.py (нужен g++). Движок: test10/BUILD_ENGINE.md.\n'.encode())
 assets=[]
 for f in [archive,sources]:
  payload=f.read_bytes()
  with zipfile.ZipFile(io.BytesIO(payload)) as z:assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
  with request(release['url']+'/assets') as response:existing=json.load(response)
  asset=next((a for a in existing if a['name']==f.name),None)
  if asset is None:
   url='https://uploads.github.com/repos/'+OWNER+'/releases/'+ident+'/assets?name='+urllib.parse.quote(f.name)
   with request(url,payload,content_type='application/zip') as response:asset=json.load(response)
  with request(asset['url']+'?verify='+nonce,accept='application/octet-stream') as response:downloaded=response.read()
  assert sha(downloaded)==sha(payload),'Existing asset differs; never overwrite'
  with zipfile.ZipFile(io.BytesIO(downloaded)) as z:assert z.testzip() is None
  if anonymous(asset['url'])!=404 or anonymous(asset['browser_download_url'])!=404:
   with request(asset['url'],method='DELETE'):pass
   raise RuntimeError('New asset withdrawn: privacy check failed')
  assets.append({'name':f.name,'url':asset['browser_download_url'],'asset_id':asset['id'],'bytes':len(payload),'sha256':sha(payload),'authenticated_download_verified':True,'anonymous_http_status':404});print('Verified',f.name,len(payload),flush=True)
 (REPO/'reports/personal-playtest-10/STATUS.json').write_text(json.dumps({'draft':True,'release_url':release['html_url'],'assets':assets,'manifest':manifest},ensure_ascii=False,indent=2)+'\n')
 print('PASS exact model reproduction, geometry coupling, complete sources and both private downloads')
