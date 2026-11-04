from pathlib import Path
import json,hashlib,zipfile,shutil,subprocess,tempfile,os,sys
repo='i7885784-lang/igraYS-Flight-Simulator';tag='personal-su30sm-test5-intake-fix-20261104';code=Path(__file__).resolve().parent;report=Path('reports/su30sm-test5-intake-fix').resolve()
def gh(*a):return subprocess.check_output(['gh',*a])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pack(root,p):
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,6) as z:
  for f in sorted(root.rglob('*')):
   if f.is_file() and '__pycache__' not in f.parts:z.write(f,root.name+'/'+f.relative_to(root).as_posix())
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
with tempfile.TemporaryDirectory() as td:
 t=Path(td);old=json.loads(Path('reports/su30sm-test-5/STATUS.json').read_text())
 for kind in ['Game_Win32_Win64','Sources']:
  name='YSFlight_Su30SM_Test_5_'+kind+'.zip';gh('release','download','personal-su30sm-test5-20261104','--repo',repo,'--pattern',name,'--dir',str(t));assert sha(t/name)==next(x['sha256'] for x in old['assets'] if x['name']==name)
  with zipfile.ZipFile(t/name) as z:z.extractall(t)
 work=t/'work';shutil.copytree(code,work);shutil.move(str(t/'runtime'),work/'runtime');(work/'baseline').mkdir();shutil.copy2(work/'runtime/aircraft/su30sm.dnm',work/'baseline/su30sm.dnm');subprocess.run([sys.executable,str(work/'fix.py')],check=True)
 audit=json.loads((work/'audit.json').read_text());assert audit==json.loads((report/'audit.json').read_text())
 with zipfile.ZipFile(t/'YSFlight_Su30SM_Test_5_Game_Win32_Win64.zip') as z:
  for n in z.namelist():
   if n.endswith('/') or n=='runtime/aircraft/su30sm.dnm':continue
   assert z.read(n)==(work/n).read_bytes(),n
 shutil.copytree(work,t/'sources/su30sm-test5-intake-fix',ignore=shutil.ignore_patterns('runtime','__pycache__'));assert (t/'sources/su30sm-test3/engine/YSFLIGHT/src/vehicle/fsairplaneproperty.cpp').is_file()
 release=json.loads(gh('api','repos/'+repo+'/releases/'+os.environ['RELEASE_ID']));assert release['draft'];prefix=release['html_url'].replace('/tag/','/download/');assets=[]
 for kind,root in [('Game_Win32_Win64',work/'runtime'),('Sources',t/'sources'),('Report',report)]:
  f=t/('YSFlight_Su30SM_Test5_IntakeFix_'+kind+'.zip');pack(root,f);gh('release','upload',tag,str(f),'--repo',repo);v=t/'verify';v.mkdir(exist_ok=True);gh('release','download',tag,'--repo',repo,'--pattern',f.name,'--dir',str(v));assert sha(f)==sha(v/f.name);assets.append({'name':f.name,'sha256':sha(f),'bytes':f.stat().st_size,'url':prefix+'/'+f.name})
 status={'draft':True,'baseline':'su30sm-test-5','changed_game_files':['aircraft/su30sm.dnm'],'all_other_game_files_byte_identical':True,'model_audit':audit,'release_id':release['id'],'release_url':release['html_url'],'assets':assets,'validation':'Native OpenGL64 visual before/after via Wine; exact mesh/node/file comparison; binaries unchanged; no new Windows32 run'};(report/'STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2));gh('release','upload',tag,str(report/'STATUS.json'),'--repo',repo)
