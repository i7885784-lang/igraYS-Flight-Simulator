"""Apply the reviewed connected path. No optimizer is needed for a rebuild."""
from pathlib import Path
import sys,numpy as np,json,math
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'runtime/aircraft/su34.dnm');params=np.array(json.loads((r/'su34-fit.json').read_text())['parameters']);track=np.array(json.loads((r/'su34-motion-track.json').read_text())['fold_swivel_bogie']);up=np.array([0.,.996677,.081453]);up/=np.linalg.norm(up);lu={dnm.name(n):n for n in ns}
for side,sg in [('L',1),('R',-1)]:
 D=np.diag([sg,1,1]);P=np.array([sg*1.911626166666667,params[6],params[7]]);J=np.array([sg*1.9215752346986938,-2.041623961098528,-2.3626928481477196]);F=np.array([sg*1.912,-1.1,-2.40]);ss={nm:[] for nm in ['MainCylinder','MainInnerStem','TandemTruck']}
 for g in np.linspace(0,1,101):
  t=1-np.clip((g-.24)/.76,0,1);s=np.interp(t,track[:,0],track[:,1]);b=np.interp(t,track[:,0],track[:,2]);R=D@Rotation.from_euler('XYZ',params[:3]*t,degrees=True).as_matrix()@D;rt=P-R@P;S=Rotation.from_rotvec(up*math.radians(sg*params[3]*s)).as_matrix();A=R@S;u=R@(F-S@F+up*params[4]*t)+rt;B=A@Rotation.from_euler('X',params[5]*b,degrees=True).as_matrix()
  for nm,rot,tr in [('MainCylinder',R,rt),('MainInnerStem',A,u),('TandemTruck',B,A@J+u-B@J)]:ss[nm].append(state(rot,tr))
 for nm,states in ss.items():
  n=lu[nm+side];i=next(i for i,s in enumerate(n) if s.startswith('NST '));j=next(i for i,s in enumerate(n) if s.startswith('POS '));n[i:j]=['NST 101']+states
dnm.write(r/'runtime/aircraft/su34.dnm',p,ns)
