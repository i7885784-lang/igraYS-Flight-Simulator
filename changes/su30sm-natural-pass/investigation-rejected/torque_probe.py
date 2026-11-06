from pathlib import Path
import sys,numpy as np,json,fcl,collections
from model import Model
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'baseline/su30sm.dnm');m=Model(r/'baseline/su30sm.dnm')
for side in ['Left','Right']:
 name='GearLink_TorqueUpper_'+side;n=next(n for n in ns if dnm.name(n)==name);mesh=dnm.mesh(p[dnm.fil(n)]);v=np.array(mesh.v);print(name,'bounds',v.min(0),v.max(0),'uniqueY',np.unique(v[:,1]),'colors',collections.Counter(c for ids,c,b in mesh.f))
 for g in [.32,.325]:
  m.sample(g);res=fcl.CollisionResult();fcl.collide(m.objects['MainBayFixedSkin_'+side],m.objects[name],fcl.CollisionRequest(num_max_contacts=20,enable_contact=True),res)
  for c in res.contacts[:3]:
   v,f=m.meshes['MainBayFixedSkin_'+side];q=v[f[c.b1]];print(g,c.pos,'skintriangle',q.tolist())
