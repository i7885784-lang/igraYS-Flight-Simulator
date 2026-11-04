"""Reproduce only two SRF changes over the verified complete test5+IntakeFix game."""
from pathlib import Path
import json,hashlib,zipfile,shutil,subprocess,tempfile,os,sys
repo='i7885784-lang/igraYS-Flight-Simulator'
tag='personal-su30sm-test5-shutter-fix-20261104'
code=Path(__file__).resolve().parent
report=Path('reports/su30sm-test5-shutter-fix').resolve()
def gh(*a):return subprocess.check_output(['gh',*a])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pack(root,p):
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,6) as z:
  for f in sorted(root.rglob('*')):
   if f.is_file() and '__pycache__' not in f.parts:z.write(f,root.name+'/'+f.relative_to(root).as_posix())
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
with tempfile.TemporaryDirectory() as td:
 t=Path(td);old=json.loads(Path('reports/su30sm-test5-intake-fix/STATUS.json').read_text());base={}
 for kind in ['Game_Win32_Win64','Sources']:
  asset=next(x for x in old['assets'] if x['name'].endswith('_'+kind+'.zip'));name=asset['name'];base[kind]=t/name
  gh('release','download','personal-su30sm-test5-intake-fix-20261104','--repo',repo,'--pattern',name,'--dir',str(t));assert sha(t/name)==asset['sha256']
  with zipfile.ZipFile(t/name) as z:
   assert z.testzip() is None;z.extractall(t)
 work=t/'work';shutil.copytree(code,work);shutil.move(str(t/'runtime'),work/'runtime');(work/'baseline').mkdir();shutil.copy2(work/'runtime/aircraft/su30sm.dnm',work/'baseline/su30sm.dnm')
 assert sha(work/'baseline/su30sm.dnm')=='17ddccbe820b4220463d2b4303f36460cb5effc7aa10973c7693dc1d1a68a504'
 for f in (work/'source-data').glob('support-*.srf'):shutil.copy2(f,work/'baseline'/f.name)
 subprocess.run([sys.executable,str(work/'refine.py')],check=True)
 audit=json.loads((work/'refinement.json').read_text());expected=json.loads((report/'refinement.json').read_text());assert audit==expected,'Reproduced model/audit mismatch'
 unchanged=0
 with zipfile.ZipFile(base['Game_Win32_Win64']) as z:
  original_names={n for n in z.namelist() if not n.endswith('/')}
  assert original_names=={'runtime/'+f.relative_to(work/'runtime').as_posix() for f in (work/'runtime').rglob('*') if f.is_file()}
  for n in sorted(original_names):
   if n=='runtime/aircraft/su30sm.dnm':continue
   assert z.read(n)==(work/n).read_bytes(),n;unchanged+=1
 source_root=t/'sources/su30sm-test5-shutter-fix'
 shutil.copytree(work,source_root,ignore=shutil.ignore_patterns('runtime','__pycache__','geometry-cache'))
 assert (t/'sources/su30sm-test3/engine/YSFLIGHT/src/vehicle/fsairplaneproperty.cpp').is_file()
 assert (t/'sources/su30sm-test4/source/su-30sm.glb').is_file()
 release=json.loads(gh('api','repos/'+repo+'/releases/'+os.environ['RELEASE_ID']));assert release['draft'] and release['tag_name']==tag
 prefix=release['html_url'].replace('/tag/','/download/');assets=[]
 for kind,root in [('Game_Win32_Win64',work/'runtime'),('Sources',t/'sources'),('Report',report)]:
  f=t/('YSFlight_Su30SM_Test5_ShutterFix_'+kind+'.zip');pack(root,f);gh('release','upload',tag,str(f),'--repo',repo)
  v=t/'verify';v.mkdir(exist_ok=True);gh('release','download',tag,'--repo',repo,'--pattern',f.name,'--dir',str(v));assert sha(f)==sha(v/f.name)
  with zipfile.ZipFile(v/f.name) as z:assert z.testzip() is None
  assets.append({'name':f.name,'sha256':sha(f),'bytes':f.stat().st_size,'url':prefix+'/'+f.name})
 status={'draft':True,'baseline':'su30sm-test-5 + approved IntakeFix','rollback_current_version_unchanged':True,'changed_game_files':['aircraft/su30sm.dnm'],'changed_packs':audit['changed_packs'],'all_nodes_transforms_states_parents_unchanged':True,'all_other_game_files_byte_identical':True,'unchanged_game_files':unchanged,'model_sha256':audit['sha256'],'release_id':release['id'],'release_url':release['html_url'],'assets':assets,'acceptance':json.loads((report/'acceptance.json').read_text()),'reproduction':'Exact full refinement.json and output SHA matched on Ubuntu Actions/Python3.12','scope_result':'Invalid loft and Fuselage_0_4 intersections removed in 201 sampled poses; 54 inherited neighboring pair-pose intersections remain; not a complete gear fix'}
 (report/'STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2));gh('release','upload',tag,str(report/'STATUS.json'),'--repo',repo)
 print(json.dumps({k:status[k] for k in ['release_id','assets','model_sha256','unchanged_game_files']},indent=2))
