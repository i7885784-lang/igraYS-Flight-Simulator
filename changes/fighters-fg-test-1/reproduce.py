from pathlib import Path
import subprocess,shutil,hashlib,json
lab=Path(__file__).resolve().parent;src=lab/'model-source';out=lab/'rebuild-independent';out.mkdir(exist_ok=True)
for p in src.iterdir():
 if p.name in ['runtime','__pycache__','model-stats.json']:continue
 if p.is_dir():shutil.copytree(p,out/p.name,dirs_exist_ok=True)
 else:shutil.copy2(p,out/p.name)
subprocess.run(['python3',str(out/'build_model.py')],check=True)
results={}
for p in (out/'runtime/aircraft').iterdir():
 assert p.read_bytes()==(src/'runtime/aircraft'/p.name).read_bytes(),p.name
 results[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
(lab/'source-rebuild-checks.json').write_text(json.dumps({'passed':True,'byte_identical':results,'independent_source_directory':True},indent=2))
print('Rebuilt',len(results),'files, byte identical')
