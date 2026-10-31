from pathlib import Path
import sys,numpy as np
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'runtime/aircraft/su47.dnm')
for n in ns:
 name=dnm.name(n)
 if name.startswith('Slat'):
  v=np.unique(np.array(dnm.mesh(p[dnm.fil(n)]).v),axis=0);ends=[]
  for x in [v[:,0].min(),v[:,0].max()]:
   q=v[abs(v[:,0]-x)<.001];z=q[:,2].min();edge=q[abs(q[:,2]-z)<.002];ends.append(edge.mean(0))
  axis=ends[1]-ends[0];axis/=np.linalg.norm(axis);i=n.index('NST 3');j=next(i for i,s in enumerate(n) if s.startswith('POS '));n[i:j]=['NST 3']+[state(Rotation.from_rotvec(axis*a).as_matrix()) for a in [0,.20,-.20]]
 if name=='IntakeBacks':
  m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v)
  for sg in [-1,1]:
   ix=v[:,0]*sg>0;c=(v[ix].min(0)+v[ix].max(0))/2;v[ix,0]=c[0]+(v[ix,0]-c[0])*.82;v[ix,1]=c[1]+(v[ix,1]-c[1])*.82
  v[:,2]-=.65;m.v=[tuple(q) for q in v];p[dnm.fil(n)]=m.srf()
for name in ['su47.dnm','su47_coarse.dnm']:dnm.write(r/'runtime/aircraft'/name,p,ns)
