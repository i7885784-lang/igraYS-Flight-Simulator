"""Thicken only the true projected perimeter, never individual clipped triangle edges."""
import numpy as np,collections
import shapely
from shapely.geometry import Polygon,Point
from shapely.strtree import STRtree
from shapely.ops import unary_union
from common import Mesh

def panel(surface,R,C,thickness=.008):
 m=Mesh();polys=[];coeff=[];seen=set();kept=[]
 for q,c in surface:
  n=np.cross(q[1]-q[0],q[2]-q[0])
  if abs(n[1])<1e-10:continue
  key=tuple(sorted(tuple(a) for a in np.round(q,6)))
  if key in seen:continue
  seen.add(key)
  if n[1]>0:q=q[::-1]
  poly=Polygon(q[:,[0,2]]);polys.append(poly);coeff.append(np.linalg.solve(np.c_[q[:,[0,2]],np.ones(3)],q[:,1]));kept.append((q,c))
  m.face((q-C)@R,c);m.face((q[::-1]+[0,thickness,0]-C)@R,(148,153,148))
 tree=STRtree(polys);coeff=np.array(coeff)
 # Micrometre precision joins rounding slivers; the outer outline is not convex-hulled or filled.
 domain=shapely.union_all([shapely.set_precision(p,1e-6) for p in polys],grid_size=1e-6);rims=[]
 def point(xz):
  ids=tree.query(Point(*xz).buffer(3e-6),predicate='intersects');assert len(ids),xz
  y=float((coeff[ids]@np.r_[xz,1]).min());return np.array([xz[0],y,xz[1]])
 for shape in shapely.get_parts(shapely.orient_polygons(domain,exterior_cw=False)):
  if shape.geom_type!='Polygon':continue
  for ring in [shape.exterior,*shape.interiors]:
   xy=np.array(ring.coords)
   for x,z in zip(xy[:-1],xy[1:]):
    a,b=point(x),point(z)
    if np.linalg.norm(a-b)<1e-7:continue
    m.face((np.array([b,a,a+[0,thickness,0],b+[0,thickness,0]])-C)@R,(105,118,123));rims.append([a.tolist(),b.tolist()])
 return m,{'original_surface_triangles':len(surface),'surface_triangles':len(kept),'rim_boundary_segments':len(rims),'boundary_segments':rims,'only_union_perimeter_thickened':True,'micrometre_outline_grid':1e-6,'projected_area_m2':domain.area}
