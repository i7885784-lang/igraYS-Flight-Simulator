from pathlib import Path
import runpy,json,hashlib
r=Path(__file__).parent
runpy.run_path(str(r/"repair.py"),run_name="__main__")
m=json.loads((r/"manifest.json").read_text())
assert hashlib.sha256((r/"runtime/aircraft/su30sm.dnm").read_bytes()).hexdigest()==m["model_sha256"]
