from pathlib import Path
import subprocess,sys,shutil
r=Path(__file__).resolve().parent
(r/'engine/YSFLIGHT/src/vehicle').mkdir(parents=True,exist_ok=True)
for name in ['convert.py','identical_nozzles.py','shape_stage.py','gear.py','flat_shading.py','finish.py']:
 subprocess.run([sys.executable,str(r/'model-source'/name)],check=True)
(r/'baseline').mkdir(exist_ok=True)
for ext in ['dnm','dat']:shutil.copy2(r/'runtime/aircraft'/('su30sm.'+ext),r/'baseline'/('su30sm.'+ext))
for name in ['revise.py','style_finish.py']:subprocess.run([sys.executable,str(r/'model-source'/name)],check=True)
