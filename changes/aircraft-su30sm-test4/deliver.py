from pathlib import Path
import json,subprocess,shutil,tempfile,zipfile,hashlib,sys,os
repo='i7885784-lang/igraYS-Flight-Simulator';tag='personal-su30sm-test4-20261104';code=Path(__file__).resolve().parent;report=Path('reports/su30sm-test-4').resolve()
def gh(*a):return subprocess.check_output(['gh',*a])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pack(root,dest):
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,6) as z:
  for p in sorted(root.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and not any(q.startswith('user-') for q in p.relative_to(root).parts):z.write(p,root.name+'/'+p.relative_to(root).as_posix())
 with zipfile.ZipFile(dest) as z:assert z.testzip() is None
with tempfile.TemporaryDirectory() as td:
 t=Path(td);old=json.loads(Path('reports/su30sm-test-3/STATUS.json').read_text())
 for kind in ['Game_Win32_Win64','Sources']:
  name='YSFlight_Su30SM_Test_3_'+kind+'.zip';gh('release','download','personal-su30sm-test3-20261103','--repo',repo,'--pattern',name,'--dir',str(t));assert sha(t/name)==next(a['sha256'] for a in old['assets'] if a['name']==name)
  with zipfile.ZipFile(t/name) as z:z.extractall(t)
 oldsource=t/'sources/su30sm-test3';work=t/'work';shutil.copytree(code,work,ignore=shutil.ignore_patterns('__pycache__'))
 shutil.move(str(t/'runtime'),str(work/'runtime'));game=work/'runtime';shutil.copytree(oldsource/'source',work/'source')
 subprocess.run([sys.executable,str(work/'pipeline.py')],check=True);subprocess.run([sys.executable,str(work/'measure.py')],check=True)
 manifest=json.loads((report/'CHECKS.json').read_text())
 for name,digest in manifest['expected_models'].items():assert sha(game/'aircraft'/name)==digest,'Model reproduction mismatch: '+name
 assert (work/'engine/YSFLIGHT/src/vehicle/su30_exhaust_profile.h').read_bytes()==(oldsource/'engine/YSFLIGHT/src/vehicle/su30_exhaust_profile.h').read_bytes(),'Changed exhaust calibration would require a new engine build'
 with zipfile.ZipFile(t/'YSFlight_Su30SM_Test_3_Game_Win32_Win64.zip') as z:
  for name in z.namelist():
   if name.endswith('/'):continue
   rel=name.split('/',1)[1]
   if '/aircraft/' in name and not Path(rel).name.startswith('su30sm') and Path(rel).name!='air_su30sm.lst':assert z.read(name)==(game/rel).read_bytes(),rel
   if rel in ['ysflight32_gl1.exe','ysflight64_gl1.exe']:assert z.read(name)==(game/rel).read_bytes(),rel
 shutil.copytree(code/'runtime-template',game,dirs_exist_ok=True);(game/'SU30SM_TEST_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 newsource=t/'sources/su30sm-test4';shutil.copytree(code,newsource,ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(oldsource/'source',newsource/'source')
 for n in ['drawing-dimensions.json','dimensions.json','nose-revision.json','revision.json','profiles-test3.json']:shutil.copy2(work/n,newsource/n)
 (t/'sources/README_RU.txt').write_text('Текущая доработка: su30sm-test4/. Неизменённый полный соответствующий движок находится в su30sm-test3/engine/. GLB и конвертер текущей версии в su30sm-test4/. Все предыдущие версии и лицензии сохранены.\n')
 release=json.loads(gh('api','repos/'+repo+'/releases/'+os.environ['RELEASE_ID']));assert release['draft'] and release['tag_name']==tag;prefix=release['html_url'].replace('/tag/','/download/')
 (game/'SOURCE_DOWNLOADS.txt').write_text('Complete corresponding source:\n'+prefix+'/YSFlight_Su30SM_Test_4_Sources.zip\n\nhttps://github.com/'+repo+'/tree/ysflight-center-download/reports/su30sm-test-4\n')
 outputs=[]
 for name,root in [('YSFlight_Su30SM_Test_4_Game_Win32_Win64.zip',game),('YSFlight_Su30SM_Test_4_Sources.zip',t/'sources'),('YSFlight_Su30SM_Test_4_Report.zip',report)]:
  p=t/name;pack(root,p);gh('release','upload',tag,str(p),'--repo',repo,'--clobber');verify=t/'verify';verify.mkdir(exist_ok=True);gh('release','download',tag,'--repo',repo,'--pattern',name,'--dir',str(verify),'--clobber');assert sha(p)==sha(verify/name)
  outputs.append({'name':name,'bytes':p.stat().st_size,'sha256':sha(p),'url':prefix+'/'+name,'download_verified':True})
 status={'draft':True,'baseline':'su30sm-test-3','engine_unchanged':True,'release_id':release['id'],'release_url':release['html_url'],'assets':outputs,'checks':manifest,'windows_x86':{'passed':False,'status':'pending'}}
 (report/'STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2));gh('release','upload',tag,str(report/'STATUS.json'),'--repo',repo,'--clobber')
