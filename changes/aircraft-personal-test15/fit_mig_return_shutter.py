"""Internal guided return cover. Outer source doors and exposed gear are retained."""
from pathlib import Path
import sys,numpy as np
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'runtime/aircraft/mig29.dnm');bp,bns=dnm.read(r/'baseline/mig29.dnm');bl={dnm.name(n):n for n in bns};ns=[n for n in ns if not dnm.name(n).startswith(('MainBayForwardReturn','MainBayInnerCover','MainBaySliding','ContinuousIntake','MainBayReturnStrip'))]
for key in list(p):
 if key.startswith(('MainBayForwardReturn','MainBayInnerCover','MainBaySliding','ContinuousIntake','MainBayReturnStrip')):p.pop(key)
for n in ns:
 if dnm.name(n).startswith(('Gear_gear1_','Gear_gear2_','Gear_wheel_','WheelHub','AxleFork')):n[:]=bl[dnm.name(n)].copy()
for sg,side in [(1,'L'),(-1,'R')]:
 d=dnm.mesh(p[dnm.fil(bl['Source_fwdgeardoor_'+side])]);segments=[]
 for ids,c,b in [( [ids[0],ids[k],ids[k+1]],c,b) for ids,c,b in d.f for k in range(1,len(ids)-1)]:
  q=np.array([d.v[i] for i in ids]);hits=[]
  for a,b in zip(q,np.roll(q,-1,axis=0)):
   if abs(b[1]-a[1])<1e-10:continue
   t=(.04-a[1])/(b[1]-a[1])
   if 0<=t<=1:hits.append(a+t*(b-a))
  if len(hits)>=2:segments.append((hits[0],hits[1]))
 def outer(z):
  xs=[]
  for a,b in segments:
   if abs(b[2]-a[2])<1e-10:continue
   t=(z-a[2])/(b[2]-a[2])
   if 0<=t<=1:xs.append(sg*(a+t*(b-a))[0])
  return (min(xs)-.003) if xs else 1.45
 zs=sorted(set(round(float(z),6) for z in list(np.linspace(-1.50,-.17,35))+[float(q[2]) for seg in segments for q in seg if -1.5<q[2]<-.17]))
 for k,(a,b) in enumerate(zip(zs[:-1],zs[1:])):
  if b-a<.00001:continue
  mid=(a+b)/2;aa,bb=outer(a),outer(b);m=Mesh();q=np.array([[sg*.52,.04,a],[sg*aa,.04,a],[sg*bb,.04,b],[sg*.52,.04,b]]);m.face(q,(111,133,132));m.face(q[::-1],(111,133,132));ss=[];c=np.array([0,.04,mid]);m.v=[tuple(np.array(v)-c) for v in m.v];front=-.13;rad=.065
  for g in np.linspace(0,1,101):
   f=np.clip((g-.04)/.16,0,1);z=mid+1.43*f
   if z<=front:R=np.eye(3);t=np.array([0,.04,z])
   else:
    angle=(z-front)/rad;rr=rad+.003*angle/(2*np.pi);R=Rotation.from_rotvec([-angle,0,0]).as_matrix();center=np.array([0,.04+rad-rr*np.cos(angle),front+rr*np.sin(angle)]);t=center
   ss.append(state(R,t))
  add(p,ns,f'MainBayReturnStrip{side}{k:02}',m,210,ss)
for file in ['mig29.dnm','mig29_coarse.dnm']:dnm.write(r/'runtime/aircraft'/file,p,ns)
