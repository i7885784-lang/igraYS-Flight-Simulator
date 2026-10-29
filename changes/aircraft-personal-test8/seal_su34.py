from pathlib import Path
import sys,numpy as np,json
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'model-source'))
from common import *
from shapely.geometry import Polygon,box
from shapely import union_all,constrained_delaunay_triangles
from envelope import Envelope
p,ns=dnm.read(root/'runtime/aircraft/su34.dnm');ns=[n for n in ns if dnm.name(n)!='RecessedGearBaySeals'];lu={dnm.name(n):n for n in ns};rim=Mesh();areas={}
for title,prefix in [('main','OriginalSideDoor'),('nose','FlushDoorN')]:
 meshes=[dnm.mesh(p[dnm.fil(n)]) for n in ns if dnm.name(n).startswith(prefix)];patches=[]
 for m in meshes:
  for ids,col,bright in m.f:
   if col[:3]!=(135,167,180):continue
   q=np.array([m.v[i] for i in ids]);poly=Polygon(q[:,[0,2]])
   if poly.area>1e-10:patches.append(poly)
 footprint=union_all(patches)
 if title=='main':region=footprint.buffer(.024).difference(footprint.buffer(.0085))
 else:region=footprint.buffer(.028).difference(footprint.buffer(.024))
 if title=='nose':env=Envelope([{'v':m.v,'f':[ids for ids,col,b in m.f if col[:3]==(135,167,180)]} for m in meshes],step=.005)
 for poly in (region.geoms if hasattr(region,'geoms') else [region]):
  if poly.geom_type!='Polygon' or poly.area<1e-10:continue
  for tri in constrained_delaunay_triangles(poly).geoms:
   xz=np.array(tri.exterior.coords)[:-1]
   if title=='main':y=-.245+.095*np.clip((-xz[:,1]-.8)/.8,0,1)+.017
   else:y=env.bounds(np.c_[xz[:,0],np.zeros(len(xz)),xz[:,1]])[0]+.018
   q=np.c_[xz[:,0],y,xz[:,1]];rim.face(q,(94,117,132));rim.face(q[::-1],(69,88,101))
 areas[title]=float(region.area)
add(p,ns,'RecessedGearBaySeals',rim);dnm.write(root/'runtime/aircraft/su34.dnm',p,ns);(root/'su34-seals.json').write_text(json.dumps({'internal_lips_only':True,'areas_m2':areas},indent=2))
