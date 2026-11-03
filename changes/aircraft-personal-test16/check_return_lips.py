from pathlib import Path
import sys,numpy as np,json,fcl
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
from collision import arrays,obj,interpolate
p,ns=dnm.read(r/'runtime/aircraft/mig29.dnm');lips=[]
for n in ns:
 if not dnm.name(n).startswith('MainBayReturnStrip'):continue
 m=dnm.mesh(p[dnm.fil(n)]);lips.append((obj(*arrays(m)),n))
obs=[(obj(*arrays(dnm.mesh(p[dnm.fil(n)]))),n) for n in ns if dnm.name(n) in ['Hull','EngineL','EngineR','MainBayInnerLiner','MainBayOuterWalls','MainBayCeiling'] or dnm.name(n).startswith(('OpenIntakeDuct','ContinuousIntake','Source_reargeardoor','Source_fwdgeardoor'))];hits=[];closed_contacts=[]
for g in np.linspace(0,1,401):
 for o,n in lips+obs:o.setTransform(interpolate(n,float(g)) if dnm.cla(n)==210 else fcl.Transform())
 for a,n in lips:
  for b,o in obs:
   res=fcl.CollisionResult()
   if fcl.collide(a,b,fcl.CollisionRequest(num_max_contacts=1,enable_contact=True),res):
    h={'g':float(g),'part':dnm.name(n),'other':dnm.name(o),'point':np.array(res.contacts[0].pos).round(5).tolist()}
    if g==0 and dnm.name(o).startswith('Source_fwdgeardoor'):closed_contacts.append(h);continue
    hits.append(h)
    if len(hits)<8:print(h,flush=True)
(r/'return-lip-collision-checks.json').write_text(json.dumps({'passed':not hits,'poses':401,'hits':hits,'closed_mating_contacts':closed_contacts},indent=2));print('HITS',len(hits))
