from pathlib import Path
import json,subprocess,shutil,tempfile,zipfile,hashlib,sys,os
repo='i7885784-lang/igraYS-Flight-Simulator';tag='personal-su30sm-test7-20261104';code=Path(__file__).resolve().parent;report=Path('reports/su30sm-test-7').resolve()
def gh(*a):return subprocess.check_output(['gh',*a])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pack(root,dest):
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,6) as z:
  for p in sorted(root.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and not any(q.startswith('user-') for q in p.relative_to(root).parts):z.write(p,root.name+'/'+p.relative_to(root).as_posix())
 with zipfile.ZipFile(dest) as z:assert z.testzip() is None
with tempfile.TemporaryDirectory() as td:
 t=Path(td);old=json.loads(Path('reports/su30sm-test-6/STATUS.json').read_text())
 for kind in ['Game_Win32_Win64','Sources']:
  name='YSFlight_Su30SM_Test_6_'+kind+'.zip';gh('release','download','personal-su30sm-test6-20261104','--repo',repo,'--pattern',name,'--dir',str(t));assert sha(t/name)==next(a['sha256'] for a in old['assets'] if a['name']==name)
  with zipfile.ZipFile(t/name) as z:z.extractall(t)
 work=t/'work';shutil.copytree(code,work,ignore=shutil.ignore_patterns('__pycache__'));shutil.move(str(t/'runtime'),str(work/'runtime'));game=work/'runtime';(work/'baseline').mkdir()
 for ext in ['dnm','dat']:shutil.copy2(game/'aircraft'/('su30sm.'+ext),work/'baseline'/('su30sm.'+ext))
 shutil.copy2(game/'aircraft/su30smcockpit.dnm',work/'baseline/su30smcockpit.dnm');shutil.copy2(code/'repair-input/upper-wing-repair.srf',work/'baseline/upper-wing-repair.srf');subprocess.run([sys.executable,str(work/'model-source/refine.py')],check=True);manifest=json.loads((report/'CHECKS.json').read_text())
 for name,digest in manifest['expected_models'].items():assert sha(game/'aircraft'/name)==digest,'Model reproduction mismatch: '+name
 with zipfile.ZipFile(t/'YSFlight_Su30SM_Test_6_Game_Win32_Win64.zip') as z:
  for name in z.namelist():
   if name.endswith('/'):continue
   rel=name.split('/',1)[1]
   if ('/aircraft/' in name and Path(rel).name not in ['su30sm.dnm','su30smcockpit.dnm']) or rel in ['ysflight32_gl1.exe','ysflight64_gl1.exe']:assert z.read(name)==(game/rel).read_bytes(),rel
 shutil.copytree(code/'runtime-template',game,dirs_exist_ok=True);(game/'SU30SM_TEST_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 newsource=t/'sources/su30sm-test7';shutil.copytree(code,newsource,ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(work/'baseline',newsource/'baseline');shutil.copy2(work/'refinement.json',newsource/'refinement.json')
 assert (t/'sources/su30sm-test3/engine/YSFLIGHT/src/vehicle/fsairplaneproperty.cpp').is_file();assert (t/'sources/su30sm-test4/source/su-30sm.glb').is_file()
 (t/'sources/README_RU.txt').write_text('Текущая версия: su30sm-test7. Её проверенный входной DNM6 в baseline/. Полный неизменённый соответствующий движок — su30sm-test3/engine, исходный GLB и полный предыдущий конвертер — su30sm-test4. Вся история и лицензии сохранены.\n')
 release=json.loads(gh('api','repos/'+repo+'/releases/'+os.environ['RELEASE_ID']));assert release['draft'] and release['tag_name']==tag;prefix=release['html_url'].replace('/tag/','/download/')
 (game/'SOURCE_DOWNLOADS.txt').write_text('Complete corresponding source:\n'+prefix+'/YSFlight_Su30SM_Test_7_Sources.zip\n\nhttps://github.com/'+repo+'/tree/ysflight-center-download/reports/su30sm-test-7\n')
 outputs=[]
 for name,root in [('YSFlight_Su30SM_Test_7_Game_Win32_Win64.zip',game),('YSFlight_Su30SM_Test_7_Sources.zip',t/'sources'),('YSFlight_Su30SM_Test_7_Report.zip',report)]:
  p=t/name;pack(root,p);gh('release','upload',tag,str(p),'--repo',repo,'--clobber');verify=t/'verify';verify.mkdir(exist_ok=True);gh('release','download',tag,'--repo',repo,'--pattern',name,'--dir',str(verify),'--clobber');assert sha(p)==sha(verify/name)
  outputs.append({'name':name,'bytes':p.stat().st_size,'sha256':sha(p),'url':prefix+'/'+name,'download_verified':True})
 status={'draft':True,'baseline':'su30sm-test-6','engine_unchanged':True,'release_id':release['id'],'release_url':release['html_url'],'assets':outputs,'checks':manifest,'windows_x86':{'passed':False,'status':'pending'}}
 (report/'STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2));gh('release','upload',tag,str(report/'STATUS.json'),'--repo',repo,'--clobber')
