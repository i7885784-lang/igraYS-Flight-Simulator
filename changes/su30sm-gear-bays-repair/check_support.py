from pathlib import Path
import sys,json,hashlib
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root))
from model import Model
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
from common import dnm
import numpy as np
m=Model();result={}
for side in ['Left','Right']:
 raw=dnm.mesh((root/'source-data'/('support-'+side+'.srf')).read_text().splitlines());v=np.array(raw.v);polys=[]
 for ids,c,b in raw.f:
  p=Polygon(v[ids][:,[0,2]])
  if p.area>1e-12:polys.append(p)
 domain=unary_union(polys).buffer(2e-6)
 name='MainWheelBayShutter_'+side;v,f=m.meshes[name];R,t=m.poses[name];v=v@R.T+t
 outside=[i for i,q in enumerate(v) if not domain.covers(Point(q[0],q[2]))]
 area=sum(Polygon(v[ids][:,[0,2]]).difference(domain).area for ids in f if Polygon(v[ids][:,[0,2]]).area>1e-12)
 result[side]={'vertices':len(v),'outside_valid_source_projection_points':len(outside),'projected_triangle_area_outside_m2':area,'projection_tolerance_m':2e-6}
 assert not outside and area<1e-10,result[side]
out={'model_sha256':hashlib.sha256(m.path.read_bytes()).hexdigest(),'checks':result}
(root/'final-support.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
