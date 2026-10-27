from pathlib import Path
import subprocess,shutil,hashlib,json
lab=Path(__file__).resolve().parent;results={}
for name in ['model-source','su57-source']:
 src=lab/name;dst=lab/'independent-rebuild'/name;shutil.copytree(src,dst,dirs_exist_ok=True,ignore=shutil.ignore_patterns('runtime','__pycache__','model-stats.json'))
 subprocess.run(['python3',str(dst/'build_model.py')],check=True,stdout=subprocess.DEVNULL)
 for p in (dst/'runtime/aircraft').iterdir():
  assert p.read_bytes()==(lab/'runtime/aircraft'/p.name).read_bytes(),p
  results[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
(lab/'source-rebuild-checks.json').write_text(json.dumps({'passed':True,'byte_identical_files':results},indent=2));print('PASS: 15 files rebuilt from separate source directories')
