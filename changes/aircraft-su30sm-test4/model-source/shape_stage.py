from pathlib import Path
import json,numpy as np
from common import dnm
r=Path(__file__).resolve().parent.parent
p,ns=dnm.read(r/'source-stage.dnm');meta=json.loads((r/'conversion.json').read_text());infos={q['name']:q for q in meta['components']}
# User-supplied front view explicitly dimensions 14.7 m across the wings.
old_span=14.38664;hinge=2.8;factor=(14.7/2-hinge)/(old_span/2-hinge)
def wing_x(x):return np.sign(x)*(hinge+np.maximum(abs(x)-hinge,0)*factor) if abs(x)>hinge else x
for n in ns:
 m=dnm.mesh(p[dnm.fil(n)]);pos=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);v=np.array(m.v)+pos
 if not len(v) or np.max(abs(v[:,0]))<=hinge:continue
 newpos=pos.copy();newpos[0]=wing_x(pos[0]);v[:,0]=[wing_x(x) for x in v[:,0]];m.v=list(map(tuple,v-newpos))
 # Retain imported per-vertex normals until flat_shading.py; gear.py checks them.
 normal_lines=[line for line in p[dnm.fil(n)] if line.startswith('V ') and ' R ' in line]
 m.normals=[tuple(map(float,line.split()[5:8])) for line in normal_lines]
 p[dnm.fil(n)]=m.srf();n[:]=dnm.edit(n,'POS ',' '.join(map(str,newpos))+' 0 0 0 1');infos[dnm.name(n)]['pivot']=newpos.tolist()
dnm.write(r/'source-stage.dnm',p,ns);(r/'conversion.json').write_text(json.dumps(meta,indent=2))
coll=r/'runtime/aircraft/su30smcoll.srf';m=dnm.mesh(coll.read_text().splitlines());m.v=[(wing_x(x),y,z) for x,y,z in m.v];coll.write_text('\n'.join(m.srf())+'\n')
(r/'drawing-dimensions.json').write_text(json.dumps({'reference':'User-supplied Su-30SM general arrangement sheet, title bottom right','length_m':21.9,'wingspan_m':14.7,'height_m':6.36,'wheelbase_m':5.57,'main_track_m':4.1,'note':'Explicit dimension arrows take precedence over contradictory/illegible table entries. No factory provenance claimed.'},indent=2))
print('Adjusted outer wings to 14.7m; original fin height retained (white tips included).',flush=True)
