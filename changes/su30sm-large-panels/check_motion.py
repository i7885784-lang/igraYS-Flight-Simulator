from pathlib import Path
import sys,runpy,json
root=Path(__file__).resolve().parent.parent/'su30sm-local-skin'
sys.path.insert(0,str(root/'validation'));out=Path(sys.argv[3])
runpy.run_path(str(root/'validation/motion_compare.py'),run_name='__main__')
assert not json.loads((out/'motion-diff.json').read_text())['added_pairs_poses']
