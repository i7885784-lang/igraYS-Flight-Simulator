"""Reproduce personal test 8 from the preserved five test-7 DNM files."""
from pathlib import Path
import subprocess,sys,hashlib,json
r=Path(__file__).resolve().parent
(r/'runtime/aircraft').mkdir(parents=True,exist_ok=True)
for f in ['repair_mig.py','carve_mig.py','apply_mig_path.py','wheels_mig.py','louvers_mig.py','nozzles.py','seal_su34.py','palette.py']:
 subprocess.run([sys.executable,str(r/f)],check=True)
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'runtime/aircraft').glob('*.dnm')}
(r/'generated-models.json').write_text(json.dumps(files,indent=2))
print('Rebuilt',len(files),'models')
