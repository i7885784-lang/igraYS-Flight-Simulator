from pathlib import Path
import sys,numpy as np,json,fcl
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
from collision import arrays,obj,interpolate
p,ns=dnm.read(r/'runtime/aircraft/mig29.dnm');lu={dnm.name(n):n for n in ns};hits=[];counts={}
for side in ['L','R']:
 n=lu['MainBayRearClosure'+side];o=lu['Source_reargeardoor_'+side];m=dnm.mesh(p[dnm.fil(n)]);proxy=Mesh()
 # Exclude only the intended common mating boundary: 1% inset per small facet.
 for ids,c,b in m.f:
  q=np.array([m.v[i] for i in ids]);proxy.face(.99*q+.01*q.mean(0),c,b)
 a=obj(*arrays(proxy));b=obj(*arrays(dnm.mesh(p[dnm.fil(o)])))
 for g in np.linspace(0,1,401):
  a.setTransform(interpolate(n,float(g)));b.setTransform(interpolate(o,float(g)));res=fcl.CollisionResult()
  if fcl.collide(a,b,fcl.CollisionRequest(num_max_contacts=1,enable_contact=True),res):hits.append({'side':side,'g':float(g),'point':np.array(res.contacts[0].pos).tolist()})
(r/'parent-interior-check.json').write_text(json.dumps({'passed':not hits,'poses':401,'method':'facet interiors inset1%, shared edge intentionally excluded','hits':hits},indent=2));print('PARENT INTERIOR HITS',len(hits))
