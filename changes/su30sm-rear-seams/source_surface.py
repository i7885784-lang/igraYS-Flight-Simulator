"""Extract actual lower source skin; a planar arrangement resolves multiple layers, never nearest-vertex fill."""
from pathlib import Path
import sys,numpy as np,json,hashlib
import shapely
from shapely.geometry import Polygon,box
from shapely.strtree import STRtree
from shapely.ops import unary_union
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import *

def parts(g):return [x for x in shapely.get_parts(g) if x.geom_type=='Polygon' and x.area>1e-12]
def clip2(poly,n,c):
 out=[]
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  da=a@n+c;db=b@n+c
  if da>=-1e-12:out.append(a)
  if (da>=0)!=(db>=0):out.append(a+(b-a)*da/(da-db))
 return np.array(out)
def envelope(tris):
 polys=[Polygon(q[:,[0,2]]) for q,c in tris];co=[np.linalg.solve(np.c_[q[:,[0,2]],np.ones(3)],q[:,1]) for q,c in tris];tree=STRtree(polys);out=[]
 for i,(poly,a) in enumerate(zip(polys,co)):
  domain=poly
  for j in tree.query(poly,predicate='intersects'):
   if i==j:continue
   inter=poly.intersection(polys[j])
   if inter.area<1e-12:continue
   d=a-co[j]
   if np.max(abs(d))<1e-8:
    if j<i:domain=domain.difference(inter)
   else:
    for cut in parts(inter):
     # Remove where this face is higher (inside), keeping the real lowest surface.
     xy=clip2(np.array(cut.exterior.coords)[:-1],d[:2],d[2]-1e-9)
     if len(xy)>=3:domain=domain.difference(Polygon(xy))
   if domain.is_empty:break
  for poly in parts(domain):out.append((poly,a,tris[i][1]))
 return out

def extract():
 source=Path('/workspace/ysflight-dev/su30sm-test-4/source-stage.dnm');p,ns=dnm.read(source);region=box(-2.425,-3.41,-1.005,-.38).union(box(1.005,-3.41,2.425,-.38)).union(box(-.41,1.96,.41,4.48));tris=[];seen=set()
 for n in ns:
  if dnm.name(n) not in ['Fuselage_0_4','Fuselage_0_5']:continue
  m=dnm.mesh(p[dnm.fil(n)]);R,t=transform(n,0);P=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);v=np.array(m.v)@R.T+t+P
  for ids,c,b in m.f:
   for j in range(1,len(ids)-1):
    q=v[[ids[0],ids[j],ids[j+1]]];normal=np.cross(q[1]-q[0],q[2]-q[0]);length=np.linalg.norm(normal)
    if length<1e-12 or normal[1]>=-.08*length:continue
    poly=Polygon(q[:,[0,2]])
    if not poly.intersects(region):continue
    key=tuple(sorted(tuple(a) for a in np.round(q,6)))
    if key in seen:continue
    seen.add(key);a=np.linalg.solve(np.c_[q[:,[0,2]],np.ones(3)],q[:,1])
    for poly in parts(poly.intersection(region)):
     for tri in shapely.get_parts(shapely.constrained_delaunay_triangles(poly)):
      xy=np.array(tri.exterior.coords)[:3];t=np.c_[xy[:,0],np.c_[xy,np.ones(3)]@a,xy[:,1]]
      if np.cross(t[1]-t[0],t[2]-t[0])[1]>0:t=t[::-1]
      tris.append((t,c))
 lower=envelope(tris);m=Mesh()
 for poly,a,c in lower:
  for tri in shapely.get_parts(shapely.constrained_delaunay_triangles(poly)):
   xy=np.array(tri.exterior.coords)[:3];q=np.c_[xy[:,0],np.c_[xy,np.ones(3)]@a,xy[:,1]]
   if np.cross(q[1]-q[0],q[2]-q[0])[1]>0:q=q[::-1]
   m.face(q,c)
 (r/'source-data').mkdir(exist_ok=True);(r/'source-data/original-lower-skin.srf').write_text('\n'.join(m.srf())+'\n');(r/'source-data/provenance.json').write_text(json.dumps({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'original_cropped_triangles':len(tris),'lower_envelope_faces':len(m.f),'no_nearest_vertex_fill':True},indent=2));print('source lower faces',len(m.f),flush=True)
if __name__=='__main__':extract()
