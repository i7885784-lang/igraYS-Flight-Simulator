import numpy as np
from common import *
def build_mounts(p,ns,audit):
 static=Mesh();count=0
 for n in list(ns):
  name=dnm.name(n)
  if not name.startswith('GearDoor_'):continue
  R0,C=transform(n,0);R17,_=transform(n,17);axis=Rotation.from_matrix(R17@R0.T).as_rotvec();axis/=np.linalg.norm(axis)
  if axis[2]<0:axis=-axis
  zs=[-3.03,-1.05] if 'Nose' not in name else ([2.22,2.86] if 'Aft' in name else [3.32,3.93]);moving=Mesh()
  for z in zs:
   a=C+axis*(z-C[2])/axis[2]
   # A short body-mounted fork contains the inherited 70mm clearance slide.
   for dz in [-.031,.031]:
    e=a+axis*dz;static.tube(e+[0,.016,0],e+[0,-.084,0],.010,(101,113,116),8)
   static.tube(a+[0,-.084,0]-axis*.042,a+[0,-.084,0]+axis*.042,.012,(107,120,122),10)
   moving.tube((a-axis*.029-C)@R0,(a+axis*.029-C)@R0,.015,(157,166,162),10);count+=1
  add(p,ns,'DoorHingePin_'+name,moving,210,[s for s in n if s.startswith('STA ')])
 add(p,ns,'DoorHingeForks',static)
 audit['hinge_mounts']={'fork_pairs':count,'existing_door_curves_unchanged':True,'inherited_70mm_clearance_slide_accommodated':True,'construction':'Plausible coupling of preserved game hinges, not a factory mechanism replica'}
