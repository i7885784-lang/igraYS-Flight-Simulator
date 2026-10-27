from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
import numpy as np
from scipy.ndimage import map_coordinates,distance_transform_edt
class Envelope:
 def __init__(self,objects,step=.025):
  self.objects=objects
  points=np.concatenate([np.array(o['v']) for o in objects]);self.low=points[:,[0,2]].min(0)-.05;self.step=step;self.shape=np.ceil((points[:,[0,2]].max(0)-self.low+.05)/step).astype(int)+1
  projected=[]
  self.bottom=np.full(self.shape,np.inf);self.top=np.full(self.shape,-np.inf)
  for o in objects:
   v=np.array(o['v'])
   for f in o['f']:
    for k in range(1,len(f)-1):
     p=v[[f[0],f[k],f[k+1]]];A=np.array([[p[0,0]-p[2,0],p[1,0]-p[2,0]],[p[0,2]-p[2,2],p[1,2]-p[2,2]]]);det=np.linalg.det(A)
     if abs(det)<1e-10:continue
     projected.append(Polygon(p[:,[0,2]]))
     lo=np.maximum(np.floor((p[:,[0,2]].min(0)-self.low)/step).astype(int),0);hi=np.minimum(np.ceil((p[:,[0,2]].max(0)-self.low)/step).astype(int),self.shape-1)
     ii,jj=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1),indexing='ij');x=self.low[0]+ii*step;z=self.low[1]+jj*step
     u=(A[1,1]*(x-p[2,0])-A[0,1]*(z-p[2,2]))/det;w=(-A[1,0]*(x-p[2,0])+A[0,0]*(z-p[2,2]))/det;mask=(u>=-1e-5)&(w>=-1e-5)&(u+w<=1.00001)
     y=u*p[0,1]+w*p[1,1]+(1-u-w)*p[2,1];i=ii[mask];j=jj[mask];val=y[mask]
     self.bottom[i,j]=np.minimum(self.bottom[i,j],val);self.top[i,j]=np.maximum(self.top[i,j],val)
  self.footprint=unary_union(projected).buffer(0)
  valid=np.isfinite(self.bottom);self.valid=valid.astype(float);dist,idx=distance_transform_edt(~valid,return_indices=True);self.distance=dist*step
  self.bottom[~valid]=self.bottom[tuple(idx[:,~valid])];self.top[~valid]=self.top[tuple(idx[:,~valid])]
 def bounds(self,p):
  co=((np.array(p)[:,[0,2]]-self.low)/self.step).T
  return tuple(map_coordinates(a,co,order=1,mode='nearest') for a in [self.bottom,self.top,self.distance])
 def residual(self,p,clearance=.015):
  b,t,d=self.bounds(p);return np.stack([np.maximum(b+clearance-p[:,1],0),np.maximum(p[:,1]+clearance-t,0),np.maximum(d-.015,0)*4],1)
