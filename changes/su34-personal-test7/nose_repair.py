"""Fit the preserved nose motion to the aperture; do not replace the good leg rig."""
import numpy as np
from scipy.spatial.transform import Rotation

def apply(p,ns,dnm,sta,body_env):
 seen={};out=[]
 for n in ns:
  name=dnm.name(n)
  if name in seen:
   assert n==seen[name], 'Non-identical duplicate '+name
   continue
  seen[name]=n;out.append(n)
 ns=out
 for n in ns:
  name=dnm.name(n)
  if name=='InternalWellN':
   m=dnm.mesh(p[dnm.fil(n)]);m.v=[(x,y,1.15+(z-1.30)*(4.38-1.15)/(4.38-1.30)) for x,y,z in m.v];p[dnm.fil(n)]=m.srf()
  if name.startswith('FlushDoorN'):
   m=dnm.mesh(p[dnm.fil(n)]);old=np.array(m.v);sx=.46/.398;sz=(4.34-1.18)/(4.288-1.392);offset=1.18-1.392*sz
   def cv(q):return np.asarray(q)*[sx,1,sz]+[0,0,offset]
   new=cv(old);rim=new[abs(new[:,0])>.455];zs=np.unique(np.round(rim[:,2],6));old_y=np.array([rim[abs(rim[:,2]-z)<1e-5,1].min() for z in zs]);sg=-1 if new[:,0].mean()<0 else 1
   points=np.c_[np.full(len(zs),sg*.468),np.zeros(len(zs)),zs];target_y,_,_=body_env.bounds(points);dy=target_y-old_y
   new[:,1]+=np.interp(new[:,2],zs,dy)*np.minimum(1,abs(new[:,0])/.46);m.v=[tuple(v) for v in new];p[dnm.fil(n)]=m.srf()
   states=[s.split()[1:] for s in n if s.startswith('STA ')];v=states[-1];h,pit,b=np.array(v[3:6],float)*np.pi/32768;R=Rotation.from_euler('YXZ',[-h,-pit,b]).as_matrix();t=np.array(v[:3],float);pivot=np.linalg.lstsq(np.eye(3)-R,t,rcond=None)[0];axis=Rotation.from_matrix(R).as_rotvec();axis=axis*[sx,1,sz];axis/=np.linalg.norm(axis);pivot=cv(pivot);pivot[1]+=float(np.interp(pivot[2],zs,dy))
   poses=[]
   for g in np.linspace(0,1,101):
    A=Rotation.from_rotvec(axis*np.deg2rad(112)*min(1,g/.18)).as_matrix();poses.append(sta(A,pivot-A@pivot))
   i=next(i for i,s in enumerate(n) if s.startswith('NST '));j=next(i for i,s in enumerate(n) if s.startswith('POS '));n[i:j]=['NST 101']+poses
 return p,ns
