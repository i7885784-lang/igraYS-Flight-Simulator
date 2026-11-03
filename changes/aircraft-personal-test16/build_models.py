from pathlib import Path
import shutil,subprocess,sys
r=Path(__file__).resolve().parent
(r/'runtime/aircraft').mkdir(parents=True,exist_ok=True)
shutil.copy2(r/'baseline/mig29.dnm',r/'runtime/aircraft/mig29.dnm')
for name in ['fit_mig_upper_cheek.py','trim_mig_cap.py']:subprocess.run([sys.executable,str(r/name)],check=True)
