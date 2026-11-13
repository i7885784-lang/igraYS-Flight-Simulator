from pathlib import Path
import sys,runpy
root=Path(__file__).resolve().parent.parent/'su30sm-local-skin'
sys.path.insert(0,str(root));sys.path.insert(0,str(root/'validation'))
runpy.run_path(str(root/'validation/self_intersections.py'),run_name='__main__')
