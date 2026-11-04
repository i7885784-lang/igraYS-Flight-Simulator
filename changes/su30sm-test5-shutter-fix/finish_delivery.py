"""Resume Report/STATUS upload without replacing the already verified Game/Sources assets."""
from pathlib import Path
import tempfile,subprocess,zipfile,json,hashlib,sys,os
repo='i7885784-lang/igraYS-Flight-Simulator';tag='personal-su30sm-test5-shutter-fix-20261104';report=Path('reports/su30sm-test5-shutter-fix').resolve();code=Path(__file__).resolve().parent
sys.path.insert(0,str(code/'model-source'));import dnm
def gh(*args):return subprocess.check_output(['gh',*args])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory() as td:
 t=Path(td);release=json.loads(gh('api','repos/'+repo+'/releases/'+os.environ['RELEASE_ID']));assert release['draft'] and release['tag_name']==tag;prefix=release['html_url'].replace('/tag/','/download/');assets=[]
 for kind in ['Game_Win32_Win64','Sources']:
  name='YSFlight_Su30SM_Test5_ShutterFix_'+kind+'.zip';gh('release','download',tag,'--repo',repo,'--pattern',name,'--dir',str(t));f=t/name
  with zipfile.ZipFile(f) as z:assert z.testzip() is None
  assets.append({'name':name,'sha256':sha(f),'bytes':f.stat().st_size,'url':prefix+'/'+name})
 old=json.loads(Path('reports/su30sm-test5-intake-fix/STATUS.json').read_text());base=next(x for x in old['assets'] if x['name'].endswith('_Game_Win32_Win64.zip'));gh('release','download','personal-su30sm-test5-intake-fix-20261104','--repo',repo,'--pattern',base['name'],'--dir',str(t));assert sha(t/base['name'])==base['sha256']
 with zipfile.ZipFile(t/base['name']) as a,zipfile.ZipFile(t/assets[0]['name']) as b:
  na={n for n in a.namelist() if not n.endswith('/')};nb={n for n in b.namelist() if not n.endswith('/')};assert na==nb;changed=[n for n in sorted(na) if a.read(n)!=b.read(n)];assert changed==['runtime/aircraft/su30sm.dnm'];oldbytes=a.read(changed[0]);newbytes=b.read(changed[0]);(t/'old.dnm').write_bytes(oldbytes);(t/'new.dnm').write_bytes(newbytes)
 p,ns=dnm.read(t/'old.dnm');q,nt=dnm.read(t/'new.dnm');assert ns==nt;packs=[k for k in p if p[k]!=q[k]];assert sorted(packs)==['MainWheelBayShutter_Left.srf','MainWheelBayShutter_Right.srf'];audit=json.loads((report/'refinement.json').read_text());assert hashlib.sha256(newbytes).hexdigest()==audit['sha256']
 with zipfile.ZipFile(t/assets[1]['name']) as z:
  root='sources/su30sm-test5-shutter-fix/';assert z.read(root+'baseline/su30sm.dnm')==oldbytes;assert z.read(root+'refine.py')==(code/'refine.py').read_bytes()
  for f in (code/'source-data').glob('*'):assert z.read(root+'source-data/'+f.name)==f.read_bytes()
  assert z.getinfo('sources/su30sm-test3/engine/YSFLIGHT/src/vehicle/fsairplaneproperty.cpp').file_size>100000;assert z.getinfo('sources/su30sm-test4/source/su-30sm.glb').file_size>1000000
 # The report archive records the final source/documentation revision; no game asset is overwritten.
 f=t/'YSFlight_Su30SM_Test5_ShutterFix_Report.zip'
 with zipfile.ZipFile(f,'w',zipfile.ZIP_DEFLATED,6) as z:
  for pth in sorted(report.rglob('*')):
   if pth.is_file() and pth.name!='STATUS.json':z.write(pth,report.name+'/'+pth.relative_to(report).as_posix())
 with zipfile.ZipFile(f) as z:assert z.testzip() is None
 gh('release','upload',tag,str(f),'--repo',repo);v=t/'verify';v.mkdir();gh('release','download',tag,'--repo',repo,'--pattern',f.name,'--dir',str(v));assert sha(f)==sha(v/f.name);assets.append({'name':f.name,'sha256':sha(f),'bytes':f.stat().st_size,'url':prefix+'/'+f.name})
 status={'draft':True,'baseline':'su30sm-test-5 + approved IntakeFix','rollback_current_version_unchanged':True,'changed_game_files':['aircraft/su30sm.dnm'],'changed_packs':packs,'all_nodes_transforms_states_parents_unchanged':True,'all_other_game_files_byte_identical':True,'unchanged_game_files':len(na)-1,'model_sha256':audit['sha256'],'release_id':release['id'],'release_url':release['html_url'],'assets':assets,'acceptance':json.loads((report/'acceptance.json').read_text()),'reproduction':'Exact refinement.json/model SHA assembled on Actions41881978070 from frozen verified surface layout. Raw --retriangulate can vary by platform. This continuation verifies existing Game/Sources and uploads Report/STATUS without replacing earlier assets.','scope_result':'201 sampled poses: no Fuselage_0_4 intersections; 54 inherited neighboring pair-pose intersections remain; not a complete gear fix'}
 (report/'STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2));gh('release','upload',tag,str(report/'STATUS.json'),'--repo',repo);print(json.dumps(status,ensure_ascii=False,indent=2))
