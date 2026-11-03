from pathlib import Path
import json,subprocess,shutil,tempfile,zipfile,hashlib,sys,os
repo='i7885784-lang/igraYS-Flight-Simulator';tag='personal-su30sm-test3-20261103';code=Path(__file__).resolve().parent
report=Path('reports/su30sm-test-3').resolve()
def gh(*a):return subprocess.check_output(['gh',*a])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pack(root,dest):
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,6) as z:
  for p in sorted(root.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and not any(q.startswith('user-') for q in p.relative_to(root).parts):z.write(p,root.name+'/'+p.relative_to(root).as_posix())
 with zipfile.ZipFile(dest) as z:assert z.testzip() is None
with tempfile.TemporaryDirectory() as td:
 t=Path(td);old=json.loads(Path('reports/su30sm-test-2/STATUS.json').read_text())
 for kind in ['Game_Win32_Win64','Sources']:
  name='YSFlight_Su30SM_Test_2_'+kind+'.zip';gh('release','download','personal-su30sm-test2-20261103','--repo',repo,'--pattern',name,'--dir',str(t))
  assert sha(t/name)==next(x['sha256'] for x in old['assets'] if x['name']==name)
  with zipfile.ZipFile(t/name) as z:z.extractall(t)
 work=t/'work';work.mkdir();shutil.move(str(t/'runtime'),str(work/'runtime'));game=work/'runtime';(work/'baseline').mkdir()
 for ext in ['dnm','dat']:shutil.copy2(game/'aircraft'/('su30sm.'+ext),work/'baseline'/('su30sm.'+ext))
 shutil.copytree(code/'model-source',work/'model-source');shutil.copy2(code/'nozzle-profile.json',work/'nozzle-profile.json');(work/'engine/YSFLIGHT/src/vehicle').mkdir(parents=True)
 subprocess.run([sys.executable,str(work/'model-source/revise.py')],check=True)
 manifest=json.loads((report/'CHECKS.json').read_text())
 for name,digest in manifest['expected_models'].items():assert sha(game/'aircraft'/name)==digest,'Model reproduction mismatch: '+name
 with zipfile.ZipFile(t/'YSFlight_Su30SM_Test_2_Game_Win32_Win64.zip') as z:
  for name in z.namelist():
   if name.endswith('/') or '/aircraft/' not in name:continue
   rel=name.split('/',1)[1]
   if not Path(rel).name.startswith('su30sm') and Path(rel).name!='air_su30sm.lst':assert z.read(name)==(game/rel).read_bytes(),rel
 with zipfile.ZipFile(code/'engine-binaries.zip') as z:z.extractall(game)
 shutil.copytree(code/'runtime-template',game,dirs_exist_ok=True)
 (game/'SU30SM_TEST_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 oldsource=t/'sources/su30sm-test2';newsource=t/'sources/su30sm-test3'
 shutil.copytree(code,newsource,ignore=shutil.ignore_patterns('__pycache__','engine-binaries.zip'))
 shutil.copytree(oldsource/'engine',newsource/'engine');shutil.copytree(code/'engine-overrides',newsource/'engine',dirs_exist_ok=True)
 shutil.copytree(oldsource/'source',newsource/'source');shutil.copytree(work/'baseline',newsource/'baseline');shutil.copy2(work/'profiles-test3.json',newsource/'profiles-test3.json')
 assert (newsource/'engine/YSFLIGHT/src/vehicle/su30_exhaust_profile.h').read_bytes()==(work/'engine/YSFLIGHT/src/vehicle/su30_exhaust_profile.h').read_bytes()
 (t/'sources/README_RU.txt').write_text('Текущая доработка: su30sm-test3/. Полный соответствующий движок, исходный GLB, конвертер и baseline приложены. История тестов1/2 и их лицензии сохранены.\n')
 release=json.loads(gh('api','repos/'+repo+'/releases/'+os.environ['RELEASE_ID']));assert release['draft'] and release['tag_name']==tag
 prefix=release['html_url'].replace('/tag/','/download/')
 (game/'SOURCE_DOWNLOADS.txt').write_text('Complete corresponding source:\n'+prefix+'/YSFlight_Su30SM_Test_3_Sources.zip\n\nhttps://github.com/'+repo+'/tree/ysflight-center-download/reports/su30sm-test-3\n')
 outputs=[]
 for name,root in [('YSFlight_Su30SM_Test_3_Game_Win32_Win64.zip',game),('YSFlight_Su30SM_Test_3_Sources.zip',t/'sources'),('YSFlight_Su30SM_Test_3_Report.zip',report)]:
  p=t/name;pack(root,p);gh('release','upload',tag,str(p),'--repo',repo,'--clobber')
  verify=t/'verify';verify.mkdir(exist_ok=True);gh('release','download',tag,'--repo',repo,'--pattern',name,'--dir',str(verify),'--clobber');assert sha(p)==sha(verify/name)
  outputs.append({'name':name,'bytes':p.stat().st_size,'sha256':sha(p),'url':prefix+'/'+name,'download_verified':True})
 status={'draft':True,'release_id':release['id'],'release_url':release['html_url'],'assets':outputs,'checks':manifest,'windows_x86':{'passed':False,'status':'pending'}}
 (report/'STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2));gh('release','upload',tag,str(report/'STATUS.json'),'--repo',repo,'--clobber')
