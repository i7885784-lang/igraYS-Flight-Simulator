from pathlib import Path
import sys,numpy as np,collections
r=Path(__file__).parent;sys.path.insert(0,str(r));from model import Model
from common import dnm
m=Model(r/'baseline/su30sm.dnm');m.sample(1);p,ns=dnm.read(r/'baseline/su30sm.dnm')
for name in ['Fuselage_0_7','Fuselage_0_13']:
 n=m.lu[name];raw=dnm.mesh(p[dnm.fil(n)]);v=np.array(raw.v);R,t=m.poses[name];v=v@R.T+t
 ids=np.flatnonzero((v[:,2]>-1.3)&(abs(abs(v[:,0])-1.1845)<.02)&(abs(v[:,1]+.4477)<.02));print(name,'front cone apex unique',np.unique(np.round(v[ids],6),axis=0),'instances',len(ids))
for O in [np.array([-1.18,-.54,-1.24]),np.array([-1.18,-.30,-1.24]),np.array([-1.04,-.64,-1.24])]:
 D=np.array([0.,0,-1]);hits=[]
 for name,(v,f) in m.meshes.items():
  if name.startswith(('Su30Plume','Su30Dry')):continue
  R,t=m.poses[name];q=(v@R.T+t)[f];a=q[:,0];e=q[:,1]-a;j=q[:,2]-a;h=np.cross(D,j);det=np.einsum('ij,ij->i',e,h);ok=abs(det)>1e-12;inv=np.divide(1,det,out=np.zeros_like(det),where=ok);s=O-a;u=np.einsum('ij,ij->i',s,h)*inv;Q=np.cross(s,e);b=Q@D*inv;dist=np.einsum('ij,ij->i',j,Q)*inv;ids=np.flatnonzero(ok&(u>=0)&(b>=0)&(u+b<=1)&(dist>=0)&(dist<5))
  for i in ids:hits.append((float(dist[i]),name,int(i)))
 print('Ray',O,[(round(float(O[2]-d),5),n,i) for d,n,i in sorted(hits)[:14]])
