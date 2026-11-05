from pathlib import Path
import sys,math,json,hashlib,numpy as np
import shapely
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import *
src=Path(sys.argv[1] if len(sys.argv)>1 else '/workspace/ysflight-dev/su30sm-test-4/source-stage.dnm');a,an=dnm.read(src);b,bn=dnm.read(r/'baseline/su30sm.dnm');al={dnm.name(n):n for n in an};bl={dnm.name(n):n for n in bn};aperture=unary_union([box(-2.4,-3.38,-1.03,-.41),box(1.03,-3.38,2.4,-.41)]);mesh=Mesh();seen=set();count=0;report=[]
def world(n,m):
 R,t=transform(n,0);pos=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);return np.array(m.v)@R.T+t+pos

def clip(poly,axis,t,sg):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  d=(a[axis]-t)*sg;e=(b[axis]-t)*sg
  if d>=-1e-10:out.append(a)
  if (d>=0)!=(e>=0):out.append(a+(b-a)*d/(d-e))
 return out

def signal(q):
 x,y,z=q;return math.sin(z*.86+x*.56)+.58*math.sin(x*1.7-z*.30)+.27*math.cos(z*1.9)

def paintclip(poly,level,positive):
 out=[]
 for (a,u),(b,v) in zip(poly,poly[1:]+poly[:1]):
  d=(u-level)*(1 if positive else -1);e=(v-level)*(1 if positive else -1)
  if d>=-1e-10:out.append((a,u))
  if (d>=0)!=(e>=0):out.append((a+(b-a)*d/(d-e),level))
 return out
for name in ['Fuselage_0_4','Fuselage_0_5']:
 old=dnm.mesh(a[dnm.fil(al[name])]);v=world(al[name],old);now=dnm.mesh(b[dnm.fil(bl[name])]);nv=world(bl[name],now);existing=[]
 for ids,c,k in now.f:
  q=nv[ids]
  if q[:,1].min()<.0249:continue
  p=Polygon(q[:,[0,2]])
  if p.is_valid and p.area>1e-10 and p.intersects(aperture):existing.append(p)
 occupied=unary_union(existing);area=0.;faces=0
 for fi,(ids,c,k) in enumerate(old.f):
  for j in range(1,len(ids)-1):
   q=v[[ids[0],ids[j],ids[j+1]]];n=np.cross(q[1]-q[0],q[2]-q[0]);key=tuple(sorted(tuple(np.round(t,6)) for t in q))
   if key in seen or abs(n[1])<np.linalg.norm(n)*.08:continue
   seen.add(key)
   poly=clip(list(q),1,.025,1)
   if len(poly)<3:continue
   p2=Polygon(np.array(poly)[:,[0,2]])
   if not p2.is_valid or p2.area<1e-10:continue
   missing=p2.intersection(aperture).difference(occupied.buffer(1e-7))
   if missing.area<1e-9:continue
   coeff=np.linalg.solve(np.c_[q[:,0],q[:,2],np.ones(3)],q[:,1]);parts=[]
   if c[:3] in [(57,50,115),(47,47,79)]:
    base=[(t,signal(t)) for t in poly]
    for lo,hi,color in [(-100,-.48,(77,139,163)),(-.48,.72,(118,166,185)),(.72,100,(147,163,172))]:
     cut=paintclip(base,lo,True);cut=paintclip(cut,hi,False) if len(cut)>=3 else []
     if len(cut)>=3:parts.append((Polygon(np.array([t for t,x in cut])[:,[0,2]]).intersection(missing),color))
   else:parts=[(missing,c)]
   for shape,color in parts:
    for region in shapely.get_parts(shape):
     if region.geom_type!='Polygon' or region.area<1e-10:continue
     for tri in shapely.get_parts(shapely.constrained_delaunay_triangles(region)):
      pts=np.array(tri.exterior.coords)[:3];t=np.c_[pts[:,0],np.c_[pts,np.ones(3)]@coeff,pts[:,1]]
      if np.cross(t[1]-t[0],t[2]-t[0])[1]<0:t=t[::-1]
      mesh.face(t,color);area+=tri.area;faces+=1
 report.append({'node':name,'restored_unique_triangles':faces,'restored_projected_area_m2':area})
mesh.v=[tuple(q) for q in np.round(mesh.v,6)];vv=np.array(mesh.v);mesh.f=[(ids,c,b) for ids,c,b in mesh.f if np.linalg.norm(np.cross(vv[ids[1]]-vv[ids[0]],vv[ids[2]]-vv[ids[0]]))>2e-12];mesh.f += [(ids[::-1],c,b) for ids,c,b in list(mesh.f)];(r/'source-data/upper-closure.srf').write_text('\n'.join(mesh.srf())+'\n');(r/'source-data/upper-closure-provenance.json').write_text(json.dumps({'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source_description':'Original pre-gear4 model, not test6/7; only missing upper patches over existing main-bay apertures, Y>=.025m. Exterior paint formula4 retained.','audit':report},indent=2));print(report)
