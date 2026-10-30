from pathlib import Path
import sys,numpy as np,json
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'))
from common import *
from ac_reference import AC
from envelope import Envelope
from shapely.geometry import Polygon,MultiPoint
from shapely import union_all
p,ns=dnm.read(r/'baseline/su27.dnm');ac=AC(r/'upstream/Su-27.ac');source=[{'v':(np.array(o['v'])+[0,0,10]).tolist(),'f':o['f']} for o in ac.objects if o['name'].startswith('HULL_Hull_Upper')];env=Envelope(source,step=.008)
for side in ['L','R']:
 meshes=[dnm.mesh(p[dnm.fil(n)]) for n in ns if dnm.name(n).startswith('RootDoor'+side)];foot=union_all([Polygon(np.array([m.v[i] for i in ids])[:,[0,2]]) for m in meshes for ids,c,b in m.f]).buffer(.006,join_style='mitre');samples=[]
 for n in ns:
  if not (dnm.name(n).startswith(('ConnectedMain','TorqueLink')) and (dnm.name(n).endswith(side) or ('Link'+side) in dnm.name(n))):continue
  vv=np.array(dnm.mesh(p[dnm.fil(n)]).v)
  for i in range(101):
   R,t=transform(n,i);v=vv@R.T+t;samples.extend(v[v[:,1]>-.36][:,[0,2]])
 for n in ns:
  if dnm.name(n)!='RootDoor'+side+'Strut':continue
  vv=np.array(dnm.mesh(p[dnm.fil(n)]).v)
  for i in range(101):
   R,t=transform(n,i);v=vv@R.T+t;samples.extend(v[v[:,1]>0][:,[0,2]])
 if samples:foot=foot.union(MultiPoint(samples).convex_hull.buffer(.035)).convex_hull
 de=Envelope([{'v':m.v,'f':[ids for ids,c,b in m.f]} for m in meshes],step=.006);wall=Mesh()
 for poly in (foot.geoms if hasattr(foot,'geoms') else [foot]):
  ring=np.array(poly.exterior.coords)
  for a,b in zip(ring[:-1],ring[1:]):
   pts=np.linspace(a,b,max(2,int(np.linalg.norm(b-a)/.035)+1))
   for a,b in zip(pts[:-1],pts[1:]):
    q=np.array([[a[0],0,a[1]],[b[0],0,b[1]]]);bounds=env.bounds(q);lo=np.maximum(de.bounds(q)[0]+.008,bounds[0]+.008);top=bounds[1]-.006
    if min(top-lo)<.005:continue
    v=[(a[0],lo[0],a[1]),(b[0],lo[1],b[1]),(b[0],top[1],b[1]),(a[0],top[0],a[1])];wall.face(v,(102,128,145));wall.face(v[::-1],(102,128,145))
 add(p,ns,'ConformalMainBayLiner'+side,wall)
(r/'runtime/aircraft').mkdir(parents=True,exist_ok=True)
for n in ['su27.dnm','su27_coarse.dnm']:dnm.write(r/'runtime/aircraft'/n,p,ns)
print('Added inside-only walls following original hatch outline')
