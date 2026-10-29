from pathlib import Path
import sys,numpy as np,math,json
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'model-source'))
from common import *
p,ns=dnm.read(root/'runtime/aircraft/mig29.dnm');ns=[n for n in ns if not dnm.name(n).startswith(('WheelHub','NoseTire','NoseWheelHub')) and dnm.name(n) not in ['AxleForkL','AxleForkR']];original,original_nodes=dnm.read(root/'baseline/mig29.dnm');original_lu={dnm.name(n):n for n in original_nodes};lu={dnm.name(n):n for n in ns}
def wheel(center,radius,width):
 x,y,z=center;tire=Mesh();hub=Mesh();N=32
 profile=[(-.5,.57),(-.46,.74),(-.36,.92),(-.20,1.0),(.20,1.0),(.36,.92),(.46,.74),(.5,.57)]
 def pt(s,r,a):return (x+s*width,y+r*radius*math.cos(a),z+r*radius*math.sin(a))
 for (s0,r0),(s1,r1) in zip(profile[:-1],profile[1:]):
  for k in range(N):
   a,b=k*2*math.pi/N,(k+1)*2*math.pi/N;col=(35,39,43) if abs(s0)>.34 else (26,30,34)
   tire.face([pt(s0,r0,a),pt(s0,r0,b),pt(s1,r1,b),pt(s1,r1,a)],col)
 for sg in [-1,1]:
  for k in range(N):
   a,b=k*2*math.pi/N,(k+1)*2*math.pi/N
   hub.face([pt(sg*.5,.57,a),pt(sg*.5,.57,b),pt(sg*.48,.43,b),pt(sg*.48,.43,a)],(111,124,127))
   hub.face([pt(sg*.48,.43,a),pt(sg*.48,.43,b),pt(sg*.48,.15,b),pt(sg*.48,.15,a)],(85,105,98))
   hub.face([pt(sg*.48,.15,a),pt(sg*.48,.15,b),(x+sg*width*.48,y,z)],(145,153,155))
  for k in range(8):
   a=k*2*math.pi/8
   hub.box(x+sg*width*.485,y+radius*.33*math.cos(a),z+radius*.33*math.sin(a),.008,radius*.07,radius*.07,(42,49,50))
 return double(tire),double(hub)
for side in ['L','R']:
 n=lu['Gear_wheel_'+side+'_wheel'];m=dnm.mesh(original[dnm.fil(original_lu[dnm.name(n)])]);v=np.array(m.v);lo,hi=v.min(0),v.max(0);center=(lo+hi)/2;tire,hub=wheel(center,max(hi[1:]-lo[1:])/2,(hi-lo)[0]);p[dnm.fil(n)]=tire.srf();new=add(p,ns,'WheelHub'+side,hub,210,[s for s in n if s.startswith('STA ')])
# Separate front tires and hubs also receive separate diagnostic colors.
n=lu['Gear_nosewheels_leg'];m=dnm.mesh(original[dnm.fil(original_lu[dnm.name(n)])]);v=np.array(m.v);states=[s for s in n if s.startswith('STA ')]
for i,sg in enumerate([-1,1]):
 q=v[v[:,0]*sg>.02];lo,hi=q.min(0),q.max(0);center=(lo+hi)/2;tire,hub=wheel(center,max(hi[1:]-lo[1:])/2,(hi-lo)[0])
 if i==0:p[dnm.fil(n)]=tire.srf()
 else:add(p,ns,'NoseTireRight',tire,210,states)
 add(p,ns,'NoseWheelHub'+str(i),hub,210,states)
dnm.write(root/'runtime/aircraft/mig29.dnm',p,ns)
