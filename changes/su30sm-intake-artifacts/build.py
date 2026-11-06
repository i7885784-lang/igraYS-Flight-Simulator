"""Exact single-asset delivery; every original node/state/parent and unrelated pack is preserved."""
from pathlib import Path
import sys,json,hashlib
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));import dnm
m=json.loads((r/'manifest.json').read_text());b=r/'baseline/su30sm.dnm';assert hashlib.sha256(b.read_bytes()).hexdigest()==m['baseline_sha256'];p,ns=dnm.read(b);old={k:list(v) for k,v in p.items()}
for k in m['changed_packs']:
 f=r/'patches'/k;assert hashlib.sha256(f.read_bytes()).hexdigest()==m['patch_sha256'][k];p[k]=f.read_text().splitlines()
for k in old:
 if k not in m['changed_packs']:assert old[k]==p[k]
out=r/'runtime/aircraft/su30sm.dnm';out.parent.mkdir(parents=True,exist_ok=True);tmp=out.with_suffix('.building');dnm.write(tmp,p,ns);tmp.write_bytes(tmp.read_bytes().replace(b'\r\n',b'\n'));h=hashlib.sha256(tmp.read_bytes()).hexdigest();assert h==m['model_sha256'],h;tmp.replace(out);print('Exact model:',h)
