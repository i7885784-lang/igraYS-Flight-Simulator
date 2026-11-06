"""Reproduce the tested asset, preserve full source history, package true separate PE32/PE32+ games."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile,zipfile,struct
REPO='i7885784-lang/igraYS-Flight-Simulator';TAG='personal-su30sm-bay-seams-20261106';CODE=Path(__file__).resolve().parent;REPORT=Path('reports/su30sm-bay-seams').resolve()
def gh(*args):return subprocess.check_output(['gh',*args])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def machine(p):
 b=p.read_bytes();assert b[:2]==b'MZ';off=struct.unpack_from('<I',b,0x3c)[0];assert b[off:off+4]==b'PE\0\0';return struct.unpack_from('<H',b,off+4)[0]
def pack(root,p):
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,6) as z:
  for f in sorted(root.rglob('*')):
   if f.is_file() and '__pycache__' not in f.parts:z.write(f,root.name+'/'+f.relative_to(root).as_posix())
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
with tempfile.TemporaryDirectory() as td:
 t=Path(td);old=json.loads(Path('reports/su30sm-intake-artifacts/STATUS.json').read_text())
 for kind in ['Game_Win32_Win64','Sources']:
  a=next(a for a in old['assets'] if a['name'].endswith('_'+kind+'.zip'));gh('release','download',old['tag'],'--repo',REPO,'--pattern',a['name'],'--dir',str(t));p=t/a['name'];assert sha(p)==a['sha256']
  with zipfile.ZipFile(p) as z:z.extractall(t)
 rt=t/'runtime';dark=t/'work-dark';new=t/'work-new'
 for source,work,baseline in [(Path('changes/su30sm-dark-channel'),dark,rt/'aircraft/su30sm.dnm'),(CODE,new,dark/'runtime/aircraft/su30sm.dnm')]:
  shutil.copytree(source,work,ignore=shutil.ignore_patterns('__pycache__'));(work/'baseline').mkdir(exist_ok=True);shutil.copy2(baseline,work/'baseline/su30sm.dnm');subprocess.run([sys.executable,str(work/'build.py')],check=True)
 manifest=json.loads((new/'manifest.json').read_text());assert sha(new/'runtime/aircraft/su30sm.dnm')==manifest['model_sha256'];shutil.copy2(new/'runtime/aircraft/su30sm.dnm',rt/'aircraft/su30sm.dnm')
 with zipfile.ZipFile(t/next(a['name'] for a in old['assets'] if a['name'].endswith('_Game_Win32_Win64.zip'))) as z:
  names=[n for n in z.namelist() if not n.endswith('/')];changed=[n for n in names if z.read(n)!=(t/n).read_bytes()];assert changed==['runtime/aircraft/su30sm.dnm'];unchanged=len(names)-1
 source=t/'sources';shutil.copytree(dark,source/'su30sm-dark-channel',ignore=shutil.ignore_patterns('runtime','__pycache__','geometry-cache'));shutil.copytree(new,source/'su30sm-bay-seams',ignore=shutil.ignore_patterns('runtime','__pycache__','geometry-cache'))
 assert (source/'su30sm-test3/engine/YSFLIGHT/src/vehicle/fsairplaneproperty.cpp').is_file();assert (source/'su30sm-test4/source/su-30sm.glb').is_file()
 release=json.loads(gh('api',f'repos/{REPO}/releases/'+os.environ['RELEASE_ID']));assert release['draft'] and release['tag_name']==TAG
 paths=[];architectures={}
 for bits,cpu in [(32,0x14c),(64,0x8664)]:
  game=t/('game'+str(bits))/'runtime';shutil.copytree(rt,game);opposite=64 if bits==32 else 32;(game/f'ysflight{opposite}_gl1.exe').unlink();(game/f'Play_Su30SM_{opposite}.bat').unlink(missing_ok=True)
  for p in (game/'plugin').glob('*'+str(opposite)+'.dll'):p.unlink()
  for p in game.glob('Play_*.bat'):
   text=p.read_text().replace(f'ysflight{opposite}_gl1.exe',f'ysflight{bits}_gl1.exe');p.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode())
  (game/'Play_Su30SM.bat').write_bytes(f'@echo off\r\ncd /d "%~dp0"\r\ncall Play_Su30SM_{bits}.bat\r\n'.encode())
  exes=list(game.glob('*.exe'));assert len(exes)==1 and machine(exes[0])==cpu
  for dll in (game/'plugin').glob('*.dll'):assert machine(dll)==cpu
  proof={'architecture':f'Windows x{bits if bits==64 else 86}','machine':hex(cpu),'exe':exes[0].name,'exe_sha256':sha(exes[0]),'model_sha256':manifest['model_sha256'],'engine_recompiled':False,'model_asset_updated':True,'native_launch_verified':bits==64,'x86_wine_attempt_failed':bits==32};architectures[str(bits)]=proof;(game/'ARCHITECTURE.json').write_text(json.dumps(proof,indent=2));(game/'SU30SM_BAY_SEAMS_README_RU.txt').write_text(f'Windows {bits}-bit. Распакуйте отдельно и запустите Play_Su30SM.bat.\nМодель {manifest["model_sha256"]}\nДвижок прежний; исправлен только ресурс модели. Подробные проверки/остаточные дефекты в отдельном отчёте.\n',encoding='utf-8-sig')
  p=t/f'YSFlight_Su30SM_BaySeams_Windows_x{86 if bits==32 else 64}.zip';pack(game,p);paths.append(p)
 for root,name in [(source,'YSFlight_Su30SM_BaySeams_FullSources.zip'),(REPORT,'Su30SM_BaySeams_Report_Photos_Videos.zip')]:
  p=t/name;pack(root,p);paths.append(p)
 paths.append(REPORT/'Su30SM_BaySeams_Report_RU.pdf')
 for p in paths:gh('release','upload',TAG,str(p),'--repo',REPO)
 verify=t/'verified';verify.mkdir();gh('release','download',TAG,'--repo',REPO,'--dir',str(verify))
 for p in paths:
  assert sha(p)==sha(verify/p.name)
  if p.suffix=='.zip':
   with zipfile.ZipFile(verify/p.name) as z:assert z.testzip() is None
 release=json.loads(gh('api',f'repos/{REPO}/releases/'+os.environ['RELEASE_ID']));status={'draft':True,'release_id':release['id'],'release_url':release['html_url'],'tag':TAG,'source_commit':os.environ['GITHUB_SHA'],'model_sha256':manifest['model_sha256'],'baseline_sha256':manifest['baseline_sha256'],'all_other_runtime_files_exact_before_architecture_packaging':unchanged,'architecture_packaging_changes':'Remove opposite EXE/plugin DLLs/architecture BAT, adapt launchers, add architecture/readme metadata only.','architectures':architectures,'download_sha_crc_verified':True,'full_previous_sources_preserved':True,'assets':[{'name':p.name,'size':p.stat().st_size,'sha256':sha(p),'url':next(a['browser_download_url'] for a in release['assets'] if a['name']==p.name)} for p in paths]};p=t/'STATUS.json';p.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n');gh('release','upload',TAG,str(p),'--repo',REPO);print(json.dumps(status,indent=2))
