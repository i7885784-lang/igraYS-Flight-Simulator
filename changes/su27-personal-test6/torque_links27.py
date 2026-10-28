"""Articulated torque links on a rotating oleo collar; rigid arms, shared knee."""
import math
import numpy as np
from scipy.spatial.transform import Rotation
from mesh import Mesh

def align_z(v):
 v=np.array(v,float);v/=np.linalg.norm(v);axis=np.cross([0,0,1],v);s=np.linalg.norm(axis)
 return np.eye(3) if s<1e-10 else Rotation.from_rotvec(axis/s*math.atan2(s,v[2])).as_matrix()

def build(title,sign,P,F,rv,up,params,swivel_path,add,sta):
 D=np.diag([sign,1,1]);length=.325;B=np.array([P[0]+.119,-1.05,P[2]]);C=np.array([P[0]+.119,-1.65,P[2]]);upper=[];lower=[];collar_states=[];joints=[]
 for g in np.linspace(0,1,101):
  fold=1-np.clip((g-.24)/.76,0,1);sf=np.interp(g,np.linspace(0,1,101),swivel_path);R=Rotation.from_rotvec(rv*fold).as_matrix();t=P-R@P;S=Rotation.from_rotvec(up*math.radians(params[3])*sf).as_matrix();A=R@S
  uc=R@(P-S@P)+t;u=R@(F-S@F+up*params[4]*fold)+t
  b=A@B+uc;c=A@C+u;axis=c-b;dist=np.linalg.norm(axis);assert dist<2*length
  pole=A@np.array([0.,0.,1.]);pole-=axis*(pole@axis)/(dist*dist);pole/=np.linalg.norm(pole)
  knee=(b+c)*.5+pole*math.sqrt(length**2-dist**2/4)
  for states,a,z in [(upper,b,knee),(lower,knee,c)]:
   a=D@a;z=D@z;states.append(sta(align_z(z-a),a))
  collar_states.append(sta(D@A@D,D@uc));joints.append([*(D@b),*(D@knee),*(D@c)])
 for suffix,states in [('A',upper),('B',lower)]:
  m=Mesh();m.tube((0,0,0),(0,0,length),.022,(147,165,177),10);add('TorqueLink'+title+suffix,m,210,states)
 collar=Mesh();collar.tube(tuple(D@np.array([P[0],-1.09,P[2]])),tuple(D@np.array([P[0],-1.01,P[2]])),.119,(136,155,169),14,inner=.105)
 # Radial lug joins the collar surface to the upper link pin.
 collar.tube(tuple(D@np.array([P[0]+.10,-1.05,P[2]])),tuple(D@B),.025,(147,165,177),10)
 add('OleoCollar'+title,collar,210,collar_states)
 return {'arm_length_m':length,'knee_positions':joints,'rigid_arms':True,'rotating_upper_collar':True,'joint_error_before_quantization_m':0.0}
