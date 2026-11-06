"""Package the exact tested resource over the complete preserved Game/Sources baseline."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile,zipfile
REPO='i7885784-lang/igraYS-Flight-Simulator'
TAG='personal-su30sm-polish-20261106'
CODE=Path(__file__).resolve().parent
REPORT=Path('reports/su30sm-visual-polish').resolve()
def gh(*args):return subprocess.check_output(['gh',*args])
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def pack(root,path):
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,6) as z:
  for f in sorted(root.rglob('*')):
   if not f.is_file() or '__pycache__' in f.parts:continue
   info=zipfile.ZipInfo(root.name+'/'+f.relative_to(root).as_posix(),(2026,11,6,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
   z.writestr(info,f.read_bytes(),compresslevel=6)
 with zipfile.ZipFile(path) as z:assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
def upload(path):gh('release','upload',TAG,str(path),'--repo',REPO)
with tempfile.TemporaryDirectory() as td:
 t=Path(td);old=json.loads(Path('reports/su30sm-gear-bays-repair/STATUS.json').read_text());base={}
 for kind in ['Game_Win32_Win64','Sources']:
  a=next(a for a in old['assets'] if a['name'].endswith('_'+kind+'.zip'));p=t/a['name'];base[kind]=p
  gh('release','download','personal-su30sm-gearbays-20261105','--repo',REPO,'--pattern',a['name'],'--dir',str(t));assert sha(p)==a['sha256']
  with zipfile.ZipFile(p) as z:assert z.testzip() is None;z.extractall(t)
 work=t/'work';shutil.copytree(CODE,work,ignore=shutil.ignore_patterns('__pycache__'));shutil.move(str(t/'runtime'),work/'runtime');(work/'baseline').mkdir();
 for filename in ['su30sm.dnm','su30smcockpit.dnm']:shutil.copy2(work/'runtime/aircraft'/filename,work/'baseline'/filename)
 subprocess.run([sys.executable,str(work/'build.py')],check=True)
 manifest=json.loads((work/'manifest.json').read_text());assert all(sha(work/'runtime/aircraft'/fn)==m['output_sha256'] for fn,m in manifest['models'].items())
 # Both original EXEs, DAT, physics, all other aircraft, scenery and controls must be exact.
 with zipfile.ZipFile(base['Game_Win32_Win64']) as z:
  names={n for n in z.namelist() if not n.endswith('/')};new={'runtime/'+f.relative_to(work/'runtime').as_posix() for f in (work/'runtime').rglob('*') if f.is_file()};assert names==new
  different=[n for n in sorted(names) if z.read(n)!=(work/n).read_bytes()];assert different==['runtime/aircraft/su30sm.dnm','runtime/aircraft/su30smcockpit.dnm'];unchanged=len(names)-2
 source=t/'sources/su30sm-visual-polish';shutil.copytree(work,source,ignore=shutil.ignore_patterns('runtime','__pycache__','geometry-cache'))
 for name in ['su30sm-test3/engine/YSFLIGHT/src/vehicle/fsairplaneproperty.cpp','su30sm-test4/source/su-30sm.glb','su30sm-visual-polish/baseline/su30sm.dnm','su30sm-visual-polish/baseline/su30smcockpit.dnm']:
  assert (t/'sources'/name).is_file(),name
 release=json.loads(gh('api','repos/'+REPO+'/releases/'+os.environ['RELEASE_ID']));assert release['draft'] and release['tag_name']==TAG
 # Never PATCH draft metadata during uploads: the initial release identity stays fixed.
 prefix=release['html_url'].replace('/tag/','/download/');assets=[]
 for kind,root in [('Game_Win32_Win64',work/'runtime'),('Sources',t/'sources'),('Report',REPORT)]:
  if kind=='Report':(REPORT/'DOWNLOADS.json').write_text(json.dumps({'release_id':release['id'],'assets':assets},indent=2)+'\n')
  p=t/('YSFlight_Su30SM_Test5_VisualPolish_'+kind+'.zip');pack(root,p);upload(p)
  verify=t/'verify';verify.mkdir(exist_ok=True);gh('release','download',TAG,'--repo',REPO,'--pattern',p.name,'--dir',str(verify));assert sha(p)==sha(verify/p.name)
  with zipfile.ZipFile(verify/p.name) as z:assert z.testzip() is None
  assets.append({'name':p.name,'sha256':sha(p),'bytes':p.stat().st_size,'url':prefix+'/'+p.name})
 status={'draft':True,'release_id':release['id'],'release_url':release['html_url'],'tag':TAG,'source_commit':os.environ.get('GITHUB_SHA'),'baseline_release_id':old['release_id'],'model_sha256':manifest['models']['su30sm.dnm']['output_sha256'],'cockpit_sha256':manifest['models']['su30smcockpit.dnm']['output_sha256'],'models':manifest['models'],'changed_game_files':['aircraft/su30sm.dnm','aircraft/su30smcockpit.dnm'],'unchanged_game_files':unchanged,'all_other_game_files_byte_identical':True,'stable_current_version_unchanged':True,'assets':assets,'acceptance':json.loads((REPORT/'acceptance.json').read_text()),'reproduction':'Exact tested SRF/state assembly for both DNM files; complete raw algorithm included','remaining_defects':['Legacy faceted shading on doors/skin remains.','Original main gear/intake volume overlap during parts of stow remains; unchanged mechanism.'],'full_sources_engine_glb_history_preserved':True}
 (REPORT/'STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n');upload(REPORT/'STATUS.json');upload(REPORT/'DOWNLOADS.json')
 print(json.dumps(status,ensure_ascii=False,indent=2),flush=True)
