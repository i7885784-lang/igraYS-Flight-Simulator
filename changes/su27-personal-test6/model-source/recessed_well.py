"""Recessed well: a small skin aperture flares to the internal storage volume."""
import numpy as np
from shapely.geometry import Polygon,box,LineString
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
from mesh import Mesh

def make_well(env,opening,storage,cap):
 x0,x1,z0,z1=storage;low=env.footprint.intersection(box(*[opening[0],opening[2],opening[1],opening[3]]));high=env.footprint.intersection(box(x0,z0,x1,z1));m=Mesh()
 def parts(g):return list(g.geoms) if hasattr(g,'geoms') else [g]
 def roof(x,z):return min(float(env.bounds(np.array([[x,0,z]]))[1][0])-.003,cap)
 for i in range(20):
  for k in range(28):
   patch=high.intersection(box(x0+(x1-x0)*i/20,z0+(z1-z0)*k/28,x0+(x1-x0)*(i+1)/20,z0+(z1-z0)*(k+1)/28))
   for poly in parts(patch):
    if not isinstance(poly,Polygon) or poly.area<1e-10:continue
    for tri in constrained_delaunay_triangles(poly).geoms:m.face([(x,roof(x,z),z) for x,z in list(tri.exterior.coords)[:-1]],(37,48,56))
 def perimeter(poly,n=128):
  coords=list(orient(poly,sign=1).exterior.coords)[:-1];j=min(range(len(coords)),key=lambda i:(coords[i][1],coords[i][0]));coords=coords[j:]+coords[:j];line=LineString(coords+[coords[0]])
  return np.array([line.interpolate(t,normalized=True).coords[0] for t in np.linspace(0,1,n,endpoint=False)])
 lp=max([p for p in parts(low) if isinstance(p,Polygon)],key=lambda p:p.area);hp=max([p for p in parts(high) if isinstance(p,Polygon)],key=lambda p:p.area);a=perimeter(lp);b=perimeter(hp)
 layers=[]
 for t in np.linspace(0,1,9):
  xz=a*(1-t)+b*t;lowpoints=np.c_[a[:,0],np.zeros(len(a)),a[:,1]];lo0=env.bounds(lowpoints)[0];hi1=np.array([roof(x,z) for x,z in b]);y=lo0*(1-t)+hi1*t
  pts=np.c_[xz[:,0],y,xz[:,1]];lo,hi,d=env.bounds(pts);pts[:,1]=np.minimum(np.maximum(y,lo+.001),hi-.003);layers.append(pts)
 for a,b in zip(layers,layers[1:]):
  for i in range(len(a)):
   j=(i+1)%len(a);m.face([tuple(a[i]),tuple(a[j]),tuple(b[j]),tuple(b[i])],(43,55,64))
 return m
