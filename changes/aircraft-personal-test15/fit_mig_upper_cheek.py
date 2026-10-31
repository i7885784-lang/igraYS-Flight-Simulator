"""Join the existing main cover's top rim to the fixed wing-root skin."""
from pathlib import Path
import sys,numpy as np
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
from envelope import Envelope
p,ns=dnm.read(r/'runtime/aircraft/mig29.dnm');lu={dnm.name(n):n for n in ns};h=dnm.mesh(p[dnm.fil(lu['Hull'])]);env=Envelope([{'v':h.v,'f':[i for i,c,b in h.f]}],step=.008);m=Mesh()
for sg in [-1,1]:
 doors=[dnm.mesh(p[dnm.fil(n)]) for n in ns if dnm.name(n).startswith(('Source_fwdgeardoor','Source_reargeardoor')) and dnm.name(n).endswith('L' if sg>0 else 'R')];edges=[]
 for d in doors:
  for ids,c,b in d.f:
   q=np.array([d.v[i] for i in ids]);edges.extend(zip(q,np.roll(q,-1,axis=0)))
 def edge_at(z):
  hits=[]
  for a,b in edges:
   if abs(a[2]-b[2])<1e-9:continue
   t=(z-a[2])/(b[2]-a[2])
   if -.00001<=t<=1.00001:hits.append(a+(b-a)*t)
  if not hits:return None
  return max(hits,key=lambda q:sg*q[0])
 rows=[]
 for z in np.linspace(-2.387,-.004,150):
  q=edge_at(z)
  if q is None:rows.append(None);continue
  q[0]+=sg*.003;q[1]+=.004;top=q.copy();top[0]+=sg*.035;top[1]=env.bounds([top])[1][0]-.015;rows.append((q,top))
 for a,b in zip(rows[:-1],rows[1:]):
  if a is None or b is None:continue
  q=[a[0],b[0],b[1],a[1]]
  if min(a[1][1]-a[0][1],b[1][1]-b[0][1])>.01:m.face(q,(112,134,133));m.face(q[::-1],(112,134,133))
p[dnm.fil(lu['MainBayOuterWalls'])]=m.srf()
for name in ['mig29.dnm','mig29_coarse.dnm']:dnm.write(r/'runtime/aircraft'/name,p,ns)
