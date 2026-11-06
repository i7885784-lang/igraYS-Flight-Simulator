from pathlib import Path
import sys,numpy as np,shapely
from shapely.geometry import Polygon,Point
from shapely.strtree import STRtree
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import *
PAINT={(142,169,181),(77,139,163),(118,166,185),(147,163,172)}
def surfaces(path):
 p,ns=dnm.read(path);lu={dnm.name(n):n for n in ns};out={}
 for name,n in lu.items():
  m=dnm.mesh(p[dnm.fil(n)]);R,t=transform(n,0);P=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);v=np.array(m.v)@R.T+t+P if m.v else np.empty((0,3));s=[]
  for ids,c,b in m.f:
   if c not in PAINT:continue
   for j in range(1,len(ids)-1):
    q=v[[ids[0],ids[j],ids[j+1]]];a=np.cross(q[1]-q[0],q[2]-q[0]);
    if a[1]<-1e-10:s.append((q,c))
  if s:out[name]=s
 return p,ns,lu,out
