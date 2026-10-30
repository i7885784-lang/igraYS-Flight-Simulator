from pathlib import Path
import sys,numpy as np
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'))
from common import *
from envelope import Envelope
from shapely import union_all,constrained_delaunay_triangles
from shapely.geometry import Polygon
(r/'runtime/aircraft').mkdir(parents=True,exist_ok=True);p,ns=dnm.read(r/'baseline/su34.dnm');orig=dnm.mesh((r/'baseline/uncut-su34.srf').read_text().splitlines());env=Envelope([{'v':orig.v,'f':[ids for ids,c,b in orig.f]}],step=.01)
for n in ns:
 if dnm.name(n).startswith('InsideIntake'):
  m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v);b,t,d=env.bounds(v);v[:,1]=np.minimum(np.maximum(v[:,1],b+.018),t-.018);m.v=[tuple(q) for q in v];p[dnm.fil(n)]=m.srf()
# Internal stepped overlap seats: cover the seam without moving the door skin.
for prefix,title in [('FlushDoorN','Nose'),('OriginalSideDoor','Main')]:
 meshes=[dnm.mesh(p[dnm.fil(n)]) for n in ns if dnm.name(n).startswith(prefix)];faces=[]
 for m in meshes:
  for ids,c,b in m.f:
   if c[0]<130:continue
   q=np.array([m.v[i] for i in ids]);poly=Polygon(q[:,[0,2]])
   if poly.is_valid and poly.area>1e-10:faces.append(poly)
 foot=union_all(faces).buffer(.006,join_style='mitre').buffer(-.006,join_style='mitre');region=foot.buffer(.045,join_style='mitre').difference(foot.buffer(.018 if title=='Nose' else -.010,join_style='mitre'));de=Envelope([{'v':m.v,'f':[ids for ids,c,b in m.f if c[0]>=130]} for m in meshes],step=.006);rim=Mesh()
 for tri in constrained_delaunay_triangles(region).geoms:
  xz=np.array(tri.exterior.coords)[:-1];v=np.c_[xz[:,0],np.zeros(3),xz[:,1]];v[:,1]=de.bounds(v)[0]+.010;rim.face(v,(112,139,153));rim.face(v[::-1],(112,139,153));top=v+[0,.18,0];rim.face(top,(112,139,153));rim.face(top[::-1],(112,139,153))
  for a,b in zip(v,np.roll(v,-1,axis=0)):
   rim.face([a,b,b+[0,.18,0],a+[0,.18,0]],(112,139,153));rim.face([a+[0,.18,0],b+[0,.18,0],b,a],(112,139,153))
 add(p,ns,'InternalSeamSeat'+title,rim)
# Recess the nose-well lower edge above the closed cover instead of leaving
# coplanar dark wall fragments visible along its outer skin.
nose=[dnm.mesh(p[dnm.fil(n)]) for n in ns if dnm.name(n).startswith('FlushDoorN')]
ne=Envelope([{'v':m.v,'f':[ids for ids,c,b in m.f if c[0]>=130]} for m in nose],step=.006)
for n in ns:
 if dnm.name(n)=='InternalWellN':
  m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v);v[:,1]=np.maximum(v[:,1],ne.bounds(v)[0]+.018);m.v=[tuple(q) for q in v];p[dnm.fil(n)]=m.srf()
for n in ['su34.dnm','su34_coarse.dnm']:dnm.write(r/'runtime/aircraft'/n,p,ns)
print('Fitted internal lining and overlapping seats; door animation unchanged')
