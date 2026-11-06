"""Assemble exactly the two tested DNM resources from editable packs/state records."""
from pathlib import Path
import sys,json,hashlib
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));import dnm
for filename,m in json.loads((r/'manifest.json').read_text())['models'].items():
 base=r/'baseline'/filename;assert hashlib.sha256(base.read_bytes()).hexdigest()==m['baseline_sha256'];p,ns=dnm.read(base);oldn={dnm.name(n):n for n in ns}
 for fn in m['changed_packs']:
  f=r/'patches'/filename/fn;assert hashlib.sha256(f.read_bytes()).hexdigest()==m['patch_sha256'][fn];p[fn]=f.read_text().splitlines()
 replace={dnm.name(n):n for n in m['changed_nodes']}
 for name,n in replace.items():assert [s for s in n if not s.startswith('STA ')]==[s for s in oldn[name] if not s.startswith('STA ')]
 ns=[replace.get(dnm.name(n),n) for n in ns];f=r/'runtime/aircraft'/filename;f.parent.mkdir(parents=True,exist_ok=True);tmp=f.with_suffix('.building');dnm.write(tmp,p,ns);tmp.write_bytes(tmp.read_bytes().replace(b'\r\n',b'\n'));h=hashlib.sha256(tmp.read_bytes()).hexdigest();assert h==m['output_sha256'],(filename,h);tmp.replace(f);print(filename,h)
