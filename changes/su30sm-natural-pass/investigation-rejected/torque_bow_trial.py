from pathlib import Path
import sys,json,numpy as np,hashlib
from model import Model
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm');lu={dnm.name(n):n for n in ns};reference=Model(r/'baseline/su30sm.dnm');reference.sample(.3225);audit={}
for side,sg in [('Left',-1),('Right',1)]:
 name='GearLink_TorqueUpper_'+side;n=lu[name];raw=dnm.mesh(p[dnm.fil(n)]);v=np.array(raw.v);L=float(v[:,1].max());R,t=reference.poses[name];d=R.T@np.array([sg,0,0]);d[1]=0;d/=np.linalg.norm(d);m=Mesh();N=12;steps=12;amp=float(sys.argv[1]) if len(sys.argv)>1 else .035
 rings=[]
 for u in np.linspace(0,1,steps+1):
  centre=np.array([0,u*L,0])+d*(16*u*u*(1-u)*(1-u)*amp);rings.append(np.array([centre+[.024*np.cos(2*np.pi*j/N),0,.024*np.sin(2*np.pi*j/N)] for j in range(N)]))
 for a,b in zip(rings,rings[1:]):
  for k in range(N):
   j=(k+1)%N;m.face([a[k],a[j],b[j],b[k]],(163,175,184))
 for k in range(N):
  j=(k+1)%N;m.face([[0,0,0],rings[0][j],rings[0][k]],(163,175,184));m.face([[0,L,0],rings[-1][k],rings[-1][j]],(163,175,184))
 p[dnm.fil(n)]=m.srf();audit[name]={'preserved_endpoint_centres':[[0,0,0],[0,L,0]],'radius_m':.024,'centre_bow_m':amp,'local_direction':d.tolist(),'all_motion_states_unchanged':True}
dnm.write(r/'bow-trial.dnm',p,ns);(r/'bow-audit.json').write_text(json.dumps(audit,indent=2));print(audit)
