from pathlib import Path
import sys,numpy as np,json,fcl
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *

def arrays(m):
 v,idx=np.unique(np.round(m.v,6),axis=0,return_inverse=True);faces=[]
 for ids,c,b in m.f:
  for k in range(1,len(ids)-1):
   q=idx[[ids[0],ids[k],ids[k+1]]]
   if np.linalg.norm(np.cross(v[q[1]]-v[q[0]],v[q[2]]-v[q[0]]))>1e-10:faces.append(q)
 return v,np.unique(np.sort(faces,axis=1),axis=0).astype(np.int32)
def obj(v,f):
 b=fcl.BVHModel();b.beginModel(len(v),len(f));b.addSubModel(v,f);b.endModel();return fcl.CollisionObject(b)
def interpolate(n,u):
 ss=[s for s in n if s.startswith('STA ')];x=u*(len(ss)-1);i=min(len(ss)-2,int(x));f=x-i
 R,t=transform(n,i);S,v=transform(n,i+1);z=(1-f)*R[:,2]+f*S[:,2];z/=np.linalg.norm(z);y=(1-f)*R[:,1]+f*S[:,1];a=np.cross(y,z);a/=np.linalg.norm(a);y=np.cross(z,a);return fcl.Transform(np.c_[a,y,z],(1-f)*t+f*v)
