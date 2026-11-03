from pathlib import Path
import json,subprocess,shutil,tempfile,zipfile,hashlib,sys,os
repo='i7885784-lang/igraYS-Flight-Simulator';tag='personal-su30sm-test2-20261103';code=Path(__file__).resolve().parent
report=Path('reports/su30sm-test-2').resolve()
def gh(*a):return subprocess.check_output(['gh',*a])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pack(root,dest):
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,6) as z:
  for p in sorted(root.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and not any(q.startswith('user-') for q in p.relative_to(root).parts):z.write(p,root.name+'/'+p.relative_to(root).as_posix())
 with zipfile.ZipFile(dest) as z:assert z.testzip() is None
with tempfile.TemporaryDirectory() as td:
 t=Path(td);old=json.loads(Path('reports/su30sm-test-1/STATUS.json').read_text())
 for kind in ['Game_32bit','Sources']:
  name='YSFlight_Su30SM_Test_1_'+kind+'.zip';gh('release','download','personal-su30sm-test1-20261103','--repo',repo,'--pattern',name,'--dir',str(t))
  assert sha(t/name)==next(x['sha256'] for x in old['assets'] if x['name']==name)
  with zipfile.ZipFile(t/name) as z:z.extractall(t)
 game=t/'YSFlight_Su30SM_Test_1_Game';work=t/'work';work.mkdir()
 shutil.move(str(game),str(work/'runtime'));game=work/'runtime'
 oldsource=t/'sources/su30sm-test1';shutil.copytree(oldsource/'source',work/'source');(work/'engine/YSFLIGHT/src/vehicle').mkdir(parents=True)
 shutil.copytree(code/'model-source',work/'model-source')
 for script in ['convert.py','identical_nozzles.py','gear.py','flat_shading.py','finish.py']:subprocess.run([sys.executable,str(work/'model-source'/script)],check=True)
 for name,digest in json.loads((report/'CHECKS.json').read_text())['expected_models'].items():assert sha(game/'aircraft'/name)==digest,'Model reproduction mismatch: '+name
 # Preserve every other aircraft from the delivered baseline.
 with zipfile.ZipFile(t/'YSFlight_Su30SM_Test_1_Game_32bit.zip') as z:
  for name in z.namelist():
   if name.endswith('/') or '/aircraft/' not in name:continue
   rel=name.split('/',1)[1]
   if not Path(rel).name.startswith('su30sm') and Path(rel).name!='air_su30sm.lst':assert z.read(name)==(game/rel).read_bytes(),rel
 with zipfile.ZipFile(code/'engine-binaries.zip') as z:z.extractall(game)
 shutil.copytree(code/'runtime-template',game,dirs_exist_ok=True)
 manifest=json.loads((report/'CHECKS.json').read_text());(game/'SU30SM_TEST_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 # Current full engine, raw model, reproducible converter, and all prior source history.
 newsource=t/'sources/su30sm-test2';shutil.copytree(code,newsource,ignore=shutil.ignore_patterns('__pycache__','engine-binaries.zip'))
 shutil.copytree(oldsource/'engine',newsource/'engine');shutil.copytree(code/'engine-overrides',newsource/'engine',dirs_exist_ok=True)
 shutil.copytree(work/'source',newsource/'source');shutil.copytree(code/'runtime-template',newsource/'runtime-template',dirs_exist_ok=True)
 for name in ['conversion.json','gear.json','nozzle-profile.json','nozzle-limits.json','nozzle-symmetry.json']:shutil.copy2(work/name,newsource/name)
 (t/'sources/README_RU.txt').write_text('Текущая версия: su30sm-test2/. Полный движок, GLB, конвертер и изменения приложены. su30sm-test1/ и history/ сохранены.\n')
 # Pin a real tag before creating the draft, keeping existing versions untouched.
 commit=os.environ['GITHUB_SHA']
 try:gh('api','repos/'+repo+'/git/ref/tags/'+tag)
 except subprocess.CalledProcessError:gh('api','repos/'+repo+'/git/refs','-f','ref=refs/tags/'+tag,'-f','sha='+commit)
 try:release=json.loads(gh('api','repos/'+repo+'/releases/tags/'+tag))
 except subprocess.CalledProcessError:
  gh('release','create',tag,'--repo',repo,'--draft','--title','Су-30СМ: тест 2, Windows 32 и 64 бит','--notes-file',str(report/'RELEASE.md'))
  release=json.loads(gh('api','repos/'+repo+'/releases/tags/'+tag))
 assert release['draft'];prefix=release['html_url'].replace('/tag/','/download/')
 source_url=prefix+'/YSFlight_Su30SM_Test_2_Sources.zip'
 (game/'SOURCE_DOWNLOADS.txt').write_text('Complete corresponding source:\n'+source_url+'\n\nhttps://github.com/'+repo+'/tree/ysflight-center-download/reports/su30sm-test-2\n')
 outputs=[]
 for name,root in [('YSFlight_Su30SM_Test_2_Game_Win32_Win64.zip',game),('YSFlight_Su30SM_Test_2_Sources.zip',t/'sources'),('YSFlight_Su30SM_Test_2_Report.zip',report)]:
  p=t/name;pack(root,p);gh('release','upload',tag,str(p),'--repo',repo,'--clobber')
  verify=t/'verify';verify.mkdir(exist_ok=True);gh('release','download',tag,'--repo',repo,'--pattern',name,'--dir',str(verify),'--clobber');assert sha(p)==sha(verify/name)
  outputs.append({'name':name,'bytes':p.stat().st_size,'sha256':sha(p),'url':prefix+'/'+name,'download_verified':True})
 status={'draft':True,'release_id':release['id'],'release_url':release['html_url'],'assets':outputs,'checks':manifest,'windows_x86':{'passed':False,'status':'pending'}}
 (report/'STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2));gh('release','upload',tag,str(report/'STATUS.json'),'--repo',repo,'--clobber')
