from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent
(r/'runtime/aircraft').mkdir(parents=True,exist_ok=True)
subprocess.run([sys.executable,str(r/'fix_rear_closure.py')],check=True)
