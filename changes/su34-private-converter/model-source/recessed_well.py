"""Internal wells use clipped source skin, not a new exterior box or height grid."""
import numpy as np
from shapely.geometry import Polygon,box,LineString
from shapely import constrained_delaunay_triangles
from mesh import Mesh
from gear_v3 import clip

def make_well(env,opening,storage,cap):
 high=env.footprint.intersection(box(storage[0],storage[2],storage[1],storage[3]));low=env.footprint.intersection(box(opening[0],opening[2],opening[1],opening[3]));m=Mesh()
 def polys(g):return list(g.geoms) if hasattr(g,'geoms') else [g]
 def skin(region,upper):
  for o in env.objects:
   vertices=np.array(o['v'])
   for ids in o['f']:
    for k in range(1,len(ids)-1):
     q=vertices[[ids[0],ids[k],ids[k+1]]];n=np.cross(q[1]-q[0],q[2]-q[0]);ln=np.linalg.norm(n)
     if ln<1e-10 or abs(n[1])/ln<.025:continue
     centre=q.mean(0);lo,hi,d=env.bounds(centre.reshape(1,3));edge=hi[0] if upper else lo[0]
     if abs(centre[1]-edge)>.065:continue
     shape=Polygon(q[:,[0,2]]).intersection(region)
     for poly in polys(shape):
      if not isinstance(poly,Polygon) or poly.area<1e-10:continue
      for tri in constrained_delaunay_triangles(poly).geoms:
       xz=np.array(list(tri.exterior.coords)[:-1]);y=q[0,1]-(n[0]*(xz[:,0]-q[0,0])+n[2]*(xz[:,1]-q[0,2]))/n[1];points=[tuple(v) for v in np.c_[xz[:,0],y,xz[:,1]]]
       if upper:
        below=clip(points,1,cap,False);above=clip(points,1,cap,True)
        if len(below)>=3:m.face([(x,y-.003,z) for x,y,z in below],(37,48,56))
        if len(above)>=3:m.face([(x,cap-.003,z) for x,y,z in above],(37,48,56))
       else:m.face([(x,y+.005,z) for x,y,z in points],(43,55,64))
 skin(high,True);skin(high.difference(low),False)
 # Vertical walls leave the entire interior storage footprint free for wheels.
 for poly in polys(high):
  if not isinstance(poly,Polygon):continue
  line=LineString(poly.exterior.coords);xz=np.array([line.interpolate(t,normalized=True).coords[0] for t in np.linspace(0,1,256,endpoint=False)]);q=np.c_[xz[:,0],np.zeros(len(xz)),xz[:,1]];lo,hi,d=env.bounds(q);a=np.c_[xz[:,0],lo+.005,xz[:,1]];b=np.c_[xz[:,0],np.minimum(hi-.003,cap-.003),xz[:,1]]
  for i in range(len(a)):
   j=(i+1)%len(a);m.face([tuple(a[i]),tuple(a[j]),tuple(b[j]),tuple(b[i])],(43,55,64))
 return m
