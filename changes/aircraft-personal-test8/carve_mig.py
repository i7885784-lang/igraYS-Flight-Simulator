from pathlib import Path
import sys,numpy as np
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'model-source'))
from common import *
from shapely.geometry import Polygon
from shapely import union_all,constrained_delaunay_triangles
from ac_reference import AC
from envelope import Envelope
ac=AC(root/'upstream/mig29/mesh_airframe.ac')
for o in ac.objects:o['v']=(np.array(o['v'])+[0,0,8.05]).tolist()
env=Envelope([o for o in ac.objects if o['name'] in ['fuselage','WingL','WingR'] or 'geardoor' in o['name']],step=.008)
p,ns=dnm.read(root/'runtime/aircraft/mig29.dnm');foot=[];original_foot=[];door_meshes={}
for n in ns:
 if dnm.name(n).startswith(('Source_fwdgeardoor','Source_reargeardoor','FlushGearDoorN')):
  m=dnm.mesh(p[dnm.fil(n)]);door_meshes[dnm.name(n)]=(n,m)
  original_foot.extend(Polygon(np.array([m.v[i] for i in ids])[:,[0,2]]).buffer(.000001) for ids,_,_ in m.f)
  foot.extend(Polygon(np.array([m.v[i] for i in ids])[:,[0,2]]).buffer(.008 if dnm.name(n).startswith('FlushGearDoorN') else .070) for ids,_,_ in m.f)
cut=union_all(foot);original=union_all(original_foot);m=dnm.mesh(p['Hull.srf']);m.f=[([ids[0],ids[k],ids[k+1]],c,b) for ids,c,b in m.f for k in range(1,len(ids)-1)];out=Mesh();removed=0
for ids,c,b in m.f:
 q=np.array([m.v[i] for i in ids]);xz=Polygon(q[:,[0,2]])
 if not xz.is_valid:xz=xz.buffer(0)
 samples=np.concatenate([q,q.mean(0)[None]]);_,roof,_=env.bounds(samples);upper=(np.median(roof-samples[:,1])<.018 and q[:,1].mean()>.04)
 if upper or q[:,1].min()>.34 or q[:,1].max()<-.32 or xz.area<1e-10 or not xz.intersects(cut):out.face(q,c,b);continue
 # Remove only the projected skin aperture below the original upper wing skin.
 A=np.c_[q[:,0],q[:,2],np.ones(len(q))];coef=np.linalg.lstsq(A,q[:,1],rcond=None)[0]
 if abs((A@coef-q[:,1])).max()>.008:out.face(q,c,b);continue
 rest=xz.difference(cut);removed+=1
 taken=xz.intersection(cut).difference(original)
 for poly in (taken.geoms if hasattr(taken,'geoms') else [taken]):
  if poly.area<1e-10 or poly.geom_type!='Polygon':continue
  for tr in constrained_delaunay_triangles(poly).geoms:
   x=np.array(tr.exterior.coords)[:-1];v=np.c_[x[:,0],np.c_[x,np.ones(len(x))]@coef,x[:,1]]
   normal=np.cross(q[1]-q[0],q[2]-q[0]);nn=np.cross(v[1]-v[0],v[2]-v[0]);v=v if normal@nn>=0 else v[::-1]
   side='L' if v[:,0].mean()>0 else 'R';kind='fwd' if v[:,2].mean()>-1.50 else 'rear';key=('FlushGearDoorN1' if side=='L' else 'FlushGearDoorN0') if v[:,2].mean()>.20 else 'Source_'+kind+'geardoor_'+side;door_meshes[key][1].face(v,(111,133,132))
 for poly in (rest.geoms if hasattr(rest,'geoms') else [rest]):
  if poly.area<1e-10 or poly.geom_type!='Polygon':continue
  for tr in constrained_delaunay_triangles(poly).geoms:
   x=np.array(tr.exterior.coords)[:-1];v=np.c_[x[:,0],np.c_[x,np.ones(len(x))]@coef,x[:,1]]
   normal=np.cross(q[1]-q[0],q[2]-q[0]);nn=np.cross(v[1]-v[0],v[2]-v[0]);v=v if normal@nn>=0 else v[::-1];out.face(v,c,b)
for name,(n,m) in door_meshes.items():p[dnm.fil(n)]=m.srf()
p['Hull.srf']=out.srf();dnm.write(root/'runtime/aircraft/mig29.dnm',p,[n for n in ns if not dnm.name(n).startswith('Source_GearWell')]);print('carved',removed)
