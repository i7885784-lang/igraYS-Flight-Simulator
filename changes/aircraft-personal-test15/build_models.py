from pathlib import Path
import sys,subprocess,shutil
r=Path(__file__).resolve().parent
(r/'runtime/aircraft').mkdir(parents=True,exist_ok=True)
for k in ['su27','su34','su47','mig29','su57']:shutil.copy2(r/'baseline'/f'{k}.dnm',r/'runtime/aircraft'/f'{k}.dnm')
for script in ['fix_controls.py','fix_su47.py','fit_su_seams.py','clamp_su27_seam.py','fit_su47_controls.py','fit_su47_inner_hull.py','fit_mig_cheeks.py','fit_mig_upper_cheek.py','fit_mig_return_shutter.py']:
 subprocess.run([sys.executable,str(r/script)],check=True)
