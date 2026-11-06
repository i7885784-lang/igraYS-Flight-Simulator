"""Conservative protection of the ORIGINAL externally visible F4 skin.
A clipped source face is protected if any interior sample lies on the original outside-X or bottom-Y envelope.
Queries use exact projected source triangles, never nearest/extrapolated heights.
"""
import numpy as np
from shapely.geometry import Polygon,Point
import shapely
class Envelope:
 def __init__(self,v,faces):
  self.charts=[]
  for axis,coords in [(0,[1,2]),(1,[0,2])]:
   polys=[];tri=[]
   for ids,c,b in faces:
    for j in range(1,len(ids)-1):
     q=v[[ids[0],ids[j],ids[j+1]]];p=Polygon(q[:,coords])
     if p.area>1e-11:polys.append(p);tri.append(q)
   # Reverse rendering copies have identical projected location and do not affect the envelope.
   self.charts.append((axis,coords,shapely.STRtree(polys),np.array(tri)))
 def external(self,q,tolerance=.001):
  # Mid-edge / centroid samples stay inside the source triangle; edge samples avoid chart ambiguities.
  samples=[q.mean(0)]+[.8*x+.2*q.mean(0) for x in q]
  for point in samples:
   for axis,coords,tree,tri in self.charts:
    ids=tree.query(Point(point[coords]),predicate='covered_by')
    if not len(ids):return True
    t=tri[ids];a=t[:,0];u=t[:,1]-a;v=t[:,2]-a;x,z=coords;det=u[:,x]*v[:,z]-u[:,z]*v[:,x];B=((point[x]-a[:,x])*v[:,z]-(point[z]-a[:,z])*v[:,x])/det;C=(u[:,x]*(point[z]-a[:,z])-u[:,z]*(point[x]-a[:,x]))/det;hits=a[:,axis]+B*u[:,axis]+C*v[:,axis]
    if axis==0:
     side=1 if point[0]>0 else -1
     if max(hits*side)-point[0]*side<tolerance:return True
    elif point[1]-min(hits)<tolerance:return True
  return False
