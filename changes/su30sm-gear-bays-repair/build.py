"""Assemble the exact tested asset from editable SRF/state resources; no platform-dependent retessellation."""
from pathlib import Path
import sys,json,hashlib
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));import dnm
manifest=json.loads((r/'manifest.json').read_text());baseline=r/'baseline/su30sm.dnm';assert hashlib.sha256(baseline.read_bytes()).hexdigest()==manifest['baseline_sha256'];p,ns=dnm.read(baseline);old={k:list(v) for k,v in p.items()};oldnodes={dnm.name(n):list(n) for n in ns}
for k in manifest['changed_packs']+manifest['added_packs']:
 f=r/'patches'/k;assert hashlib.sha256(f.read_bytes()).hexdigest()==manifest['patch_sha256'][k];p[k]=f.read_text().splitlines()
replace={dnm.name(n):n for n in manifest['changed_nodes']};assert set(replace)=={'MainWheelBayShutter_Left','MainWheelBayShutter_Right'}
for name,n in replace.items():assert [s for s in n if not s.startswith('STA ')]==[s for s in oldnodes[name] if not s.startswith('STA ')]
ns=[replace.get(dnm.name(n),n) for n in ns]+manifest['added_nodes'];assert len({dnm.name(n) for n in ns})==len(ns)
for k in old:
 if k not in manifest['changed_packs']:assert p[k]==old[k]
for n in ns:
 name=dnm.name(n)
 if name in oldnodes and name not in replace:assert n==oldnodes[name]
path=r/'runtime/aircraft/su30sm.dnm';path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.dnm.building');dnm.write(tmp,p,ns);tmp.write_bytes(tmp.read_bytes().replace(b'\r\n',b'\n'));digest=hashlib.sha256(tmp.read_bytes()).hexdigest();assert digest==manifest['model_sha256'],(digest,manifest['model_sha256']);tmp.replace(path);print('Exact verified model assembled:',digest)
