"""Replace protruding auxiliary primitives by recessed, source-bounded surfaces."""
from pathlib import Path
import sys,numpy as np
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
from envelope import Envelope
p,ns=dnm.read(r/'baseline/su47.dnm');lu={dnm.name(n):n for n in ns};h=dnm.mesh(p[dnm.fil(lu['Hull'])]);env=Envelope([{'v':h.v,'f':[i for i,c,b in h.f]}],step=.008)
# The old squared backing exceeded the actual inlet-fan contour. A recessed
# 24-sided fan backing stays inside its original bounds and the source skin.
backs=Mesh()
for side in [-1,1]:
 old=dnm.mesh(p[dnm.fil(lu['IntakeBacks'])]);v=np.array(old.v);v=v[v[:,0]*side>0];a,b=v.min(0),v.max(0);c=(a+b)/2;radius=(b-a)/2
 ring=[]
 for th in np.linspace(0,2*np.pi,25)[:-1]:
  q=c.copy();q[0]+=max(radius[0]-.04,.01)*np.cos(th);q[1]+=max(radius[1]-.04,.01)*np.sin(th)
  low,top,_=env.bounds([q]);q[1]=np.clip(q[1],low[0]+.025,top[0]-.025);ring.append(q)
 backs.face(ring,(23,27,32));backs.face(ring[::-1],(23,27,32))
p[dnm.fil(lu['IntakeBacks'])]=backs.srf()
# Old 2.1 x .6 x 3m rectangle was not an exterior component: its flat side
# projected through the raked intake side. Keep only a recessed central seal,
# sampled on the original shell, without the old vertical outside panels.
m=Mesh()
for z0,z1 in zip(np.linspace(.05,3.05,101)[:-1],np.linspace(.05,3.05,101)[1:]):
 for x0,x1 in zip(np.linspace(-1.05,1.05,71)[:-1],np.linspace(-1.05,1.05,71)[1:]):
  q=np.array([[x0,0,z0],[x1,0,z0],[x1,0,z1],[x0,0,z1]]);lo,hi,d=env.bounds(q);bottom=lo+.04;top=np.minimum(hi-.04,-.12)
  if min(top-bottom)<.02 or max(d)>.01:continue
  q[:,1]=bottom;m.face(q,(33,38,44));m.face(q[::-1],(33,38,44))
p[dnm.fil(lu['InnerFuselageSeal'])]=m.srf()
for file in ['su47.dnm','su47_coarse.dnm']:dnm.write(r/'runtime/aircraft'/file,p,ns)
