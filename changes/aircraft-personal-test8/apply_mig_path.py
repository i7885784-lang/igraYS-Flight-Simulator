from pathlib import Path
import sys,json,math,numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'model-source'))
from common import *
p,ns=dnm.read(root/'runtime/aircraft/mig29.dnm');bp,bn=dnm.read(root/'baseline/mig29.dnm');bl={dnm.name(n):n for n in bn};pivot=np.array([1.348,.07,-2.09]);axle=np.array([1.61,-1.30,-1.80]);Rend=transform(bl['Gear_gear1_L_leg'],0)[0];Qend=transform(bl['Gear_wheel_L_wheel'],0)[0];rv=Rotation.from_matrix(Rend).as_rotvec();wv=Rotation.from_matrix(Qend@Rend.T).as_rotvec()
legnames=['Gear_gear1_L_leg','Gear_gear2_L_leg','AxleForkL'];wname='Gear_wheel_L_wheel'
def poses(f,yaw,w):
 R=Rotation.from_rotvec([0,yaw,0]).as_matrix()@Rotation.from_rotvec(rv*f).as_matrix();t=pivot-R@pivot;center=R@axle+t;W=Rotation.from_rotvec(wv*w).as_matrix();return (R,t),(W@R,center+W@(t-center))
r=json.loads((root/'mig-path.json').read_text());grid=np.array(r['fold']);track=np.array(r['track'])
for n in ns:
 name=dnm.name(n)
 if name not in legnames+[wname]+[s.replace('_L_','_R_').replace('ForkL','ForkR') for s in legnames+[wname]]:continue
 mirrored='_R_' in name or name.endswith('ForkR');wheel='_wheel' in name;states=[]
 for g in np.linspace(0,1,101):
  fold=1-np.clip((g-.24)/.76,0,1);yaw=np.interp(fold,grid,track[:,0]);w=np.interp(fold,grid,track[:,1]);T,U=poses(fold,yaw,w);A=U if wheel else T;R,t=A
  if mirrored:M=np.diag([-1.,1,1]);R=M@R@M;t=M@t
  states.append(state(R,t))
 i=next(i for i,s in enumerate(n) if s.startswith('NST '));j=next(i for i,s in enumerate(n) if s.startswith('POS '));n[i:j]=['NST 101']+states
# No shallow source well: it intersected the visible stored gear. The cavity
# is enclosed by the preserved original fixed skin, not an external housing.
ns=[n for n in ns if not dnm.name(n).startswith('Source_GearWell')]
dnm.write(root/'runtime/aircraft/mig29.dnm',p,ns)
