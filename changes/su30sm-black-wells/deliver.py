from pathlib import Path
import subprocess,json,zipfile,tempfile,hashlib,sys,struct,shutil,os
repo='i7885784-lang/igraYS-Flight-Simulator';tag='personal-su30sm-black-wells-20261106';report=Path('reports/su30sm-black-wells');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def gh(*a):return subprocess.check_output(['gh',*a])
with tempfile.TemporaryDirectory() as td:
 t=Path(td);old=json.loads(Path('reports/su30sm-natural-pass/STATUS.json').read_text());assets=[]
 for bits,cpu in [(32,0x14c),(64,0x8664)]:
  a=next(a for a in old['assets'] if a['name'].endswith(f'_Windows_x{86 if bits==32 else 64}.zip'));gh('release','download',old['tag'],'--repo',repo,'--pattern',a['name'],'--dir',str(t));p=t/a['name'];assert sha(p)==a['sha256'];root=t/str(bits)
  with zipfile.ZipFile(p) as z:z.extractall(root)
  rt=root/'runtime';base=t/f'baseline{bits}.dnm';shutil.copy2(rt/'aircraft/su30sm.dnm',base);subprocess.run([sys.executable,'changes/su30sm-black-wells/recolor.py',str(base),str(rt/'aircraft/su30sm.dnm')],check=True);audit=json.loads((rt/'aircraft/su30sm.json').read_text());(rt/'aircraft/su30sm.json').unlink()
  with zipfile.ZipFile(p) as z:assert [n for n in z.namelist() if not n.endswith('/') and z.read(n)!=(root/n).read_bytes()]==['runtime/aircraft/su30sm.dnm']
  exes=list(rt.glob('*.exe'));assert len(exes)==1;b=exes[0].read_bytes();assert struct.unpack_from('<H',b,struct.unpack_from('<I',b,0x3c)[0]+4)[0]==cpu
  arch=json.loads((rt/'ARCHITECTURE.json').read_text());arch['previous_native_windows_check_model_sha256']=arch['model_sha256'];arch['model_sha256']=audit['model_sha256'];arch['current_change']='Only RGB of GearWell_Left/Right/Nose changed; current visual check x64 Wine, EXEs unchanged';(rt/'ARCHITECTURE.json').write_text(json.dumps(arch,indent=2))
  (rt/'rollback-black-wells').mkdir();shutil.copy2(base,rt/'rollback-black-wells/su30sm.dnm');shutil.copy2(report/'REPORT_RU.md',rt/'BLACK_WELLS_REPORT_RU.md')
  name=f'YSFlight_Su30SM_BlackWells_Windows_x{86 if bits==32 else 64}.zip';dest=t/name
  with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,6) as z:
   for f in sorted(rt.rglob('*')):
    if f.is_file():z.write(f,'runtime/'+f.relative_to(rt).as_posix())
  with zipfile.ZipFile(dest) as z:assert z.testzip() is None
  gh('release','upload',tag,str(dest),'--repo',repo,'--clobber');verify=t/'verified';verify.mkdir(exist_ok=True);gh('release','download',tag,'--repo',repo,'--pattern',name,'--dir',str(verify));assert sha(dest)==sha(verify/name);assets.append({'name':name,'sha256':sha(dest),'machine':hex(cpu),'model_sha256':audit['model_sha256']})
 gh('release','upload',tag,str(report/'REPORT_RU.md'),'--repo',repo,'--clobber');release=json.loads(gh('api',f'repos/{repo}/releases/'+os.environ['RELEASE_ID']))
 for a in assets:a['url']=next(x['browser_download_url'] for x in release['assets'] if x['name']==a['name'])
 s={'release_id':release['id'],'draft':True,'tag':tag,'assets':assets,'only_three_mesh_colors_changed':True,'download_sha_crc_verified':True};f=t/'STATUS.json';f.write_text(json.dumps(s,indent=2));gh('release','upload',tag,str(f),'--repo',repo,'--clobber')
