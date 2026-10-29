"""Reproduce test 8 and upload game/source ONLY to an owner-only draft."""
from pathlib import Path
import os,sys,json,hashlib,zipfile,tempfile,subprocess,shutil,runpy,urllib.parse,urllib.error,io,struct
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
h=runpy.run_path(str(REPO/'changes/su34-private-converter/build_private_draft.py'),run_name='helpers');request=h['request'];OWNER=h['OWNER'];sha=lambda b:hashlib.sha256(b).hexdigest();api='https://api.github.com/repos/'+OWNER;nonce=os.environ['GITHUB_RUN_ID'];ident=os.environ['RELEASE_ID'];expected=json.loads((HERE/'expected.json').read_text())
with request(api+'/releases/'+ident) as response:release=json.load(response)
assert release['draft'] is True

def anonymous(url):
 try:
  with request(url+('?v=' if '?' not in url else '&v=')+nonce,auth=False) as response:return response.status
 except urllib.error.HTTPError as e:return e.code
assert anonymous(release['url'])==404,'Refusing to upload geometry to a visible release'
def put(z,name,data):
 info=zipfile.ZipInfo(name,(2026,10,29,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data,compresslevel=6)
with tempfile.TemporaryDirectory(prefix='personal-test8-') as tmp:
 tmp=Path(tmp);work=tmp/'converter';game=tmp/'YSFlight_Personal_Test_8_32bit';game.mkdir()
 for what in ['archive','sources']:
  with request(api+'/releases/assets/'+str(expected['baseline_'+what+'_asset'])+'?base='+nonce,accept='application/octet-stream') as response:data=response.read()
  assert sha(data)==expected['baseline_'+what+'_sha256'];(tmp/(what+'.zip')).write_bytes(data)
 with zipfile.ZipFile(tmp/'archive.zip') as old:
  assert old.testzip() is None;prefix=old.namelist()[0].split('/')[0]
  for name in old.namelist():
   rel=name.split('/',1)[1] if '/' in name else ''
   if rel and not name.endswith('/'):
    assert '..' not in Path(rel).parts;p=game/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old.read(name))
 shutil.copytree(HERE,work,ignore=shutil.ignore_patterns('__pycache__','bin'))
 (work/'baseline').mkdir()
 for name,digest in expected['baseline_models'].items():
  data=(game/'aircraft'/name).read_bytes();assert sha(data)==digest; (work/'baseline'/name).write_bytes(data)
 result=subprocess.run([sys.executable,str(work/'build.py')],env=dict(os.environ,OPENBLAS_NUM_THREADS='1'),capture_output=True,text=True)
 assert result.returncode==0,result.stderr[-2400:]
 for name,digest in expected['models'].items():
  data=(work/'runtime/aircraft'/name).read_bytes();assert sha(data)==digest,'Model mismatch: '+name;(game/'aircraft'/name).write_bytes(data)
 exe=(HERE/'bin/ysflight32_gl1.exe').read_bytes();assert sha(exe)==expected['win32_exe_sha256'];off=struct.unpack_from('<I',exe,60)[0];assert exe[off:off+4]==b'PE\0\0' and struct.unpack_from('<H',exe,off+4)[0]==0x14c and b'MODELPOSE' not in exe;(game/'ysflight32_gl1.exe').write_bytes(exe)
 with zipfile.ZipFile(tmp/'archive.zip') as old:
  unchanged=[]
  for name in old.namelist():
   rel=name[len(prefix)+1:]
   if rel.startswith('aircraft/') and not name.endswith('/') and Path(rel).name not in expected['models']:
    assert (game/rel).read_bytes()==old.read(name),'Unrelated aircraft data changed: '+rel;unchanged.append(rel)
 # Add straightforward launchers without altering previous flights or airframes.
 for label,identifier in [('MiG29','MIG-29_FULCRUM'),('Su47','SU-47_BERKUT'),('Su57','SU-57_FELON')]:
  (game/('Play_'+label+'.bat')).write_bytes(('@echo off\r\ncd /d "%~dp0"\r\nstart "" ysflight32_gl1.exe -script Start_'+label+'.script\r\n').encode())
  (game/('Start_'+label+'.script')).write_text((game/'Start_Su27.script').read_text().replace('Su27_Play.yfs',label+'_Play.yfs'))
  (game/(label+'_Play.yfs')).write_text((game/'Su27_Play.yfs').read_text().replace('SU-27_FLANKER',identifier).replace('Su27_PLAYTEST',label+'_PLAYTEST'))
 for old_manifest in game.glob('TEST_*_MANIFEST.json'):
  (game/'history').mkdir(exist_ok=True);old_manifest.rename(game/'history'/old_manifest.name)
 manifest={'test':8,'models_sha256':expected['models'],'win32_exe_sha256':expected['win32_exe_sha256'],'engine':'new Win32 PE i386 GUI, no validation-only model-pose commands','baseline':7,'unrelated_aircraft_files_preserved':len(unchanged),'geometry_and_animations':'game approximation; not factory-certified','validation_platform':'Win64/Wine; native Windows 10 x86 not executed','private_only_due_to_su34_rights':True,'diagnostic_toggle':'Ctrl+Shift+F9; default OFF; press again to restore; hold does not repeat'}
 (game/'TEST_8_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 (game/'READ_ME_RU.txt').write_text('Личный тест №8: МиГ-29, Су-27, Су-34, Су-47 и Су-57.\nРаспаковать ПОЛНОСТЬЮ в новую папку. Запуск: Play_MiG29.bat, Play_Su27.bat, Play_Su34.bat, Play_Su47.bat, Play_Su57.bat.\nG — шасси, B — воздушное торможение, Q/A — газ, Tab — форсаж. Ctrl+Shift+F9 — включить/выключить цвета деталей самолёта игрока; по умолчанию выключено. Обычная окраска сохранена, снизу есть небольшие различия тонов.\nМиГ: створки и проёмы согласованы, низ двигателей неподвижен; колёса с округлыми боковинами и отдельными ступицами; пять настоящих впускных створок с каждой стороны открываются внутрь вокруг неподвижных шарниров, вместе с защитой основных входов. Сопла пяти самолётов регулируются по режиму; отклонение оси оставлено только Су-57. Су-34: внутреннее закрытие стыков ниш без препятствий для тележек.\nЭто тест, а не подтверждение заводской точности механизмов. Проверки выполнены в Win64/Wine; прямой запуск на Windows 10 x86 здесь не выполнялся.\nСу-34: геометрия fantazer_rnd / DEVBenSon/FiveM-Plane-Pack. Текстуры, звуки и системы GTA не перенесены. Права продажи/распространения не подтверждены: НЕ ПУБЛИКОВАТЬ эту сборку. Сведения об авторах остальных моделей сохранены в licenses/.\nИсходники: YSFlight_Personal_Test_8_Sources.zip в '+release['html_url']+'\n',encoding='utf-8-sig')
 (game/'SOURCE_DOWNLOADS.txt').write_text(release['html_url']+'\nYSFlight_Personal_Test_8_Sources.zip\n');shutil.copy2(HERE/'NOTICE.txt',game/'licenses/personal-test8-NOTICE.txt')
 archive=tmp/'YSFlight_Personal_Test_8_32bit.zip'
 with zipfile.ZipFile(archive,'w') as z:
  for f in sorted(game.rglob('*')):
   if f.is_file():put(z,game.name+'/'+f.relative_to(game).as_posix(),f.read_bytes())
 # Apply the public delta to the exact complete engine snapshot, not a fresh upstream.
 with zipfile.ZipFile(tmp/'sources.zip') as old:
  assert old.testzip() is None and not any(n.lower().endswith('.ytd') for n in old.namelist())
  for n in old.namelist():
   if n.startswith('engine/') and not n.endswith('/'):
    rel=Path(n);assert '..' not in rel.parts;p=tmp/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old.read(n))
 result=subprocess.run(['patch','--batch','-p1','-i',str(HERE/'native.patch')],cwd=tmp/'engine',capture_output=True,text=True);assert result.returncode==0,result.stdout+result.stderr
 patched=json.loads((HERE/'engine-files.json').read_text())
 for rel,digest in patched.items():assert sha((tmp/'engine'/rel).read_bytes())==digest,'Patched engine mismatch: '+rel
 sources=tmp/'YSFlight_Personal_Test_8_Sources.zip'
 with zipfile.ZipFile(tmp/'sources.zip') as old,zipfile.ZipFile(sources,'w') as z:
  for n in old.namelist():
   if n=='README_RU.md':put(z,'history/test7_README_RU.md',old.read(n))
   elif n=='SOURCE_MANIFEST.json':put(z,'history/test7_SOURCE_MANIFEST.json',old.read(n))
   elif n.startswith('engine/') and n[7:] in patched:put(z,n,(tmp/n).read_bytes())
   else:put(z,n,old.read(n))
  for f in sorted(work.rglob('*')):
   rel=f.relative_to(work)
   if f.is_file() and not any(x in ['runtime','__pycache__'] for x in rel.parts):put(z,'test8/'+rel.as_posix(),f.read_bytes())
  put(z,'SOURCE_MANIFEST.json',json.dumps({'test':8,'base_source_archive_sha256':expected['baseline_sources_sha256'],'engine_changed_files':patched,'models':expected['models'],'new_converter_files':{f.relative_to(work).as_posix():sha(f.read_bytes()) for f in work.rglob('*') if f.is_file() and not any(x in ['runtime','__pycache__'] for x in f.relative_to(work).parts)}},indent=2).encode())
  put(z,'README_RU.md',('Исходники личного теста №8. engine/ — полный изменённый движок; test8/ — воспроизводимый конвертер от пяти исходных DNM теста №7, GPL-уведомления и данные. Старые конвертеры и первичные источники, включая YFT Су-34, сохранены в прежних каталогах. Текстур YTD нет.\nСборка моделей: pip install -r test8/requirements.txt; python test8/build.py. Движок: инструкции test8/BUILD_ENGINE.md; проверочные команды доступны только при -DV861_VALIDATION, этот флаг НЕ задан в поставляемом Win32 EXE.\n').encode())
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
  assert sha(downloaded)==sha(payload),'Refusing to overwrite an existing different asset'
  with zipfile.ZipFile(io.BytesIO(downloaded)) as z:assert z.testzip() is None
  if anonymous(asset['url'])!=404 or anonymous(asset['browser_download_url'])!=404:
   with request(asset['url'],method='DELETE'):pass
   raise RuntimeError('New asset withdrawn: privacy check failed')
  assets.append({'name':f.name,'url':asset['browser_download_url'],'asset_id':asset['id'],'bytes':len(payload),'sha256':sha(payload),'authenticated_download_verified':True,'anonymous_http_status':404});print('Verified',f.name,len(payload),flush=True)
 (REPO/'reports/personal-playtest-8/STATUS.json').write_text(json.dumps({'draft':True,'release_url':release['html_url'],'assets':assets,'manifest':manifest},ensure_ascii=False,indent=2)+'\n')
 print('PASS private test8 build, source patch and both downloads')
