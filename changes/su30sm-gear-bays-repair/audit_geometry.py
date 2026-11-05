from pathlib import Path
import sys,json,numpy as np
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'baseline/su30sm.dnm');out=[]
for n in ns:
 name=dnm.name(n)
 if not any(x in name for x in ['Gear','Wheel','Bay','IntakeDuct']):continue
 m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v)
 if not len(v):continue
 R,t=transform(n,0);w=v@R.T+t
 if not len(v):continue
 out.append({'name':name,'vertices':len(v),'faces':len(m.f),'world0_bounds':[w.min(0).tolist(),w.max(0).tolist()],'colors':sorted({c for ids,c,b in m.f})})
(r/'baseline-bounds.json').write_text(json.dumps(out,indent=2));print('\n'.join(f"{d['name']} {np.array(d['world0_bounds']).round(3).tolist()} {d['faces']}faces" for d in out))
