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
