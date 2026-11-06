from pathlib import Path
import subprocess,json,zipfile,tempfile,hashlib,struct,os
repo='i7885784-lang/igraYS-Flight-Simulator';tag='su30sm-rear-seams-20261106';code=Path(__file__).parent
m=json.loads((code/'manifest.json').read_text());gh=lambda *a:subprocess.check_output(['gh',*a]);sha=lambda b:hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(code/'model-update.zip') as z:model=z.read('aircraft/su30sm.dnm')
assert sha(model)==m['model_sha256']
old=json.loads(Path('reports/su30sm-black-wells/STATUS.json').read_text());assets=[]
with tempfile.TemporaryDirectory() as td:
 t=Path(td)
 for bits,cpu in [(32,0x14c),(64,0x8664)]:
  a=next(a for a in old['assets'] if a['machine']==hex(cpu));gh('release','download',old['tag'],'--repo',repo,'--pattern',a['name'],'--dir',str(t));src=t/a['name'];out=t/f'Su30SM_RearSeams_Windows_{bits}bit.zip'
  with zipfile.ZipFile(src) as before,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,3) as after:
   baseline=before.read('runtime/aircraft/su30sm.dnm');assert sha(baseline)==m['baseline_sha256'];exes=[n for n in before.namelist() if n.endswith('.exe')];assert len(exes)==1;b=before.read(exes[0]);assert struct.unpack_from('<H',b,struct.unpack_from('<I',b,0x3c)[0]+4)[0]==cpu
   for entry in before.infolist():
    data=before.read(entry.filename)
    if entry.filename=='runtime/aircraft/su30sm.dnm':data=model
    elif entry.filename=='runtime/ARCHITECTURE.json':
     proof=json.loads(data);proof['previous_model_sha256']=proof['model_sha256'];proof['model_sha256']=m['model_sha256'];proof['current_model_visual_check']='x64 OpenGL Wine';proof['current_model_native_windows_launch_retested']=False;data=json.dumps(proof,indent=2).encode()
    after.writestr(entry.filename,data)
   after.writestr('runtime/rollback-rear-seams/su30sm.dnm',baseline)
   after.writestr('runtime/REAR_SEAMS_README_RU.txt','Задние ниши Су-30СМ: уменьшенные стыки закрытых панелей. Запуск Play_Su30SM.bat. Откат: при закрытой игре вернуть rollback-rear-seams/su30sm.dnm в aircraft/su30sm.dnm. Анимационные узлы и EXE прежние.\n')
  gh('release','upload',tag,str(out),'--repo',repo);assets.append({'name':out.name,'machine':hex(cpu),'sha256':sha(out.read_bytes())})
 gh('release','upload',tag,str(code/'model-update.zip'),'--repo',repo)
 gh('release','edit',tag,'--draft=false','--prerelease','--latest=false','--repo',repo)
 release=json.loads(gh('api',f'repos/{repo}/releases/'+os.environ['RELEASE_ID']));assert not release['draft']
 for a in assets:a['url']=next(v['browser_download_url'] for v in release['assets'] if v['name']==a['name'])
 status={'release_id':release['id'],'release_url':release['html_url'],'draft':False,'tag':tag,'model_sha256':m['model_sha256'],'assets':assets,'output_download_check_skipped_by_user_request':True,'model_fallback':next(v['browser_download_url'] for v in release['assets'] if v['name']=='model-update.zip')};f=t/'STATUS.json';f.write_text(json.dumps(status,indent=2));gh('release','upload',tag,str(f),'--repo',repo);print(json.dumps(status,indent=2))
