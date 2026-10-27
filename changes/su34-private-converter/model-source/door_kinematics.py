"""Sample fixed pivots and linked two-panel gear doors in world coordinates."""
from pathlib import Path
import json,math,warnings
import numpy as np
from scipy.spatial.transform import Rotation

def state(R,t):
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');h,p,b=Rotation.from_matrix(R).as_euler('YXZ')
 return 'STA '+' '.join(map(str,[*np.round(t,7),round(-h*32768/math.pi),round(-p*32768/math.pi),round(b*32768/math.pi),1]))

def base(n):
 s=[x.split()[1:] for x in n if x.startswith('STA ')][-1];t=np.array(s[:3],float);h,p,b=np.array(s[3:6],float)*math.pi/32768;R=Rotation.from_euler('YXZ',[-h,-p,b]).as_matrix();rv=Rotation.from_matrix(R).as_rotvec();return rv/np.linalg.norm(rv),np.linalg.lstsq(np.eye(3)-R,t,rcond=1e-4)[0]

def apply(kind,nodes,root,packs=None):
 path=Path(root)/'door-kinematics.json'
 if not path.exists():return
 settings=json.loads(path.read_text()).get(kind,{});lookup={n[0][5:].strip('"'):n for n in nodes};bases={name:base(n) for name,n in lookup.items() if name.startswith(('FlushGearDoor','FlushDoor'))}
 for name,cfg in settings.items():
  n=lookup[name];axis,pivot=bases[cfg.get('parent',name)];axis=np.array(cfg.get('axis',axis));pivot=np.array(cfg.get('pivot',pivot));angle=cfg.get('parent_angle',cfg.get('angle',97));poses=[]
  if cfg.get('flat'):
   import dnm
   mesh=dnm.mesh(packs[next(s[4:].strip('"') for s in n if s.startswith('FIL '))]);bright=max(sum(c[:3]) for f,c,b in mesh.f);v=np.array([mesh.v[i] for f,c,b in mesh.f if sum(c[:3])==bright for i in f]);gap=abs(v[:,0]-pivot[0]);edge=v[gap<gap.min()+.006];pivot=np.array([pivot[0],edge[:,1].max()+cfg.get('lift',.008),0.]);axis=np.array([0.,0.,np.sign(axis[2])])
  for g in np.linspace(0,1,101):
   phase=np.clip((g-cfg.get('start',0))/(cfg.get('end',.20)-cfg.get('start',0)),0,1);R=Rotation.from_rotvec(axis*math.radians(angle)*phase).as_matrix();t=pivot-R@pivot
   if 'parent' in cfg:
    childaxis=np.array(cfg['child_axis']);childpivot=np.array(cfg['child_pivot']);f=np.clip((g-.10)/.12,0,1);Q=Rotation.from_rotvec(childaxis*math.radians(cfg['child_angle'])*f).as_matrix();t=R@(childpivot-Q@childpivot)+t;R=R@Q
   poses.append(state(R,t))
  i=next(i for i,s in enumerate(n) if s.startswith('NST '));j=next(i for i,s in enumerate(n) if s.startswith('POS '));n[i:j]=['NST 101']+poses
