"""Reproduce personal test 9 from all five preserved final-test8 DNMs."""
from pathlib import Path
import subprocess,sys,shutil,hashlib,json
r=Path(__file__).resolve().parent;(r/'runtime/aircraft').mkdir(parents=True,exist_ok=True)
for k in ['su27','su34','mig29','su47','su57']:shutil.copy2(r/'baseline'/f'{k}.dnm',r/'runtime/aircraft'/f'{k}.dnm')
for f in ['source_reference.py','wheels_su34.py','su34_bays.py','intake_internals.py','apply_su34_path.py','mig_bays.py','exhaust.py']:subprocess.run([sys.executable,str(r/f)],check=True)
for k in ['su27','su34','mig29','su47','su57']:shutil.copy2(r/'runtime/aircraft'/f'{k}.dnm',r/'runtime/aircraft'/f'{k}_coarse.dnm')
files={name:hashlib.sha256((r/'runtime/aircraft'/name).read_bytes()).hexdigest() for k in ['su27','su34','mig29','su47','su57'] for name in [k+'.dnm',k+'_coarse.dnm']};(r/'generated-models.json').write_text(json.dumps(files,indent=2));print('Rebuilt',len(files),'models')
