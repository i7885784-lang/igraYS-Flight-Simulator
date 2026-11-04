from pathlib import Path
import numpy as np,json,fcl
from model import Model
r=Path(__file__).parent;m=Model();m.sample(1)
def inside(p,t):
 u=t[1]-t[0];v=t[2]-t[0];w=p-t[0];a=u@u;b=u@v;c=v@v;d=w@u;e=w@v;det=a*c-b*b
 if abs(det)<1e-20:return False
 s=(d*c-e*b)/det;q=(e*a-d*b)/det;return s>=-1e-7 and q>=-1e-7 and s+q<=1.0000001
def segment(A,B):
 pts=[]
 for T,U in [(A,B),(B,A)]:
  n=np.cross(U[1]-U[0],U[2]-U[0]);n/=np.linalg.norm(n)
  for a,b in zip(T,np.roll(T,-1,axis=0)):
   da=(a-U[0])@n;db=(b-U[0])@n
   if abs(da-db)>1e-12 and da*db<=1e-12:
    u=da/(da-db)
    if -1e-7<=u<=1.0000001:
     p=a+u*(b-a)
     if inside(p,U):pts.append(p)
 if not pts:return None
 pts=np.array(pts);i,j=np.unravel_index(np.linalg.norm(pts[:,None]-pts[None,:],axis=2).argmax(),(len(pts),len(pts)));return [pts[i].tolist(),pts[j].tolist()]
def edge_distance(q,t):
 ds=[]
 for a,b in zip(t,np.roll(t,-1,axis=0)):
  v=b-a;u=np.clip((q-a)@v/(v@v),0,1);ds.append(np.linalg.norm(q-a-u*v))
 return min(ds)
