from pathlib import Path
import sys,numpy as np,json,fcl
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
from collision import arrays,obj,interpolate
p,ns=dnm.read(r/'runtime/aircraft/mig29.dnm');parts=[(obj(*arrays(dnm.mesh(p[dnm.fil(n)]))),n) for n in ns if dnm.name(n).startswith('MainBayRearClosure')];obs=[(obj(*arrays(dnm.mesh(p[dnm.fil(n)]))),n) for n in ns if dnm.name(n) in ['Hull','EngineL','EngineR','MainBayOuterWalls','MainBayInnerLiner','MainBayCeiling'] or dnm.name(n).startswith(('MainBayReturnStrip','Source_fwdgeardoor'))];hits=[]
for g in np.linspace(0,1,401):
 for o,n in parts+obs:o.setTransform(interpolate(n,float(g)) if dnm.cla(n)==210 else fcl.Transform())
 for a,n in parts:
  for b,o in obs:
   res=fcl.CollisionResult()
   if fcl.collide(a,b,fcl.CollisionRequest(num_max_contacts=1,enable_contact=True),res):
    h={'g':float(g),'part':dnm.name(n),'other':dnm.name(o),'point':np.array(res.contacts[0].pos).round(5).tolist()};hits.append(h)
    if len(hits)<10:print(h,flush=True)
(r/'rear-collision-checks.json').write_text(json.dumps({'passed':not hits,'hits':hits},indent=2));print('HITS',len(hits),flush=True)
