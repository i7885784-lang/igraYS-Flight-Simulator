from pathlib import Path
import sys,json,numpy as np,hashlib
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import *
base=r/'runtime/aircraft/su30sm.dnm';p,ns=dnm.read(base);lu={dnm.name(n):n for n in ns};degrees=float(sys.argv[1]);audit={}
for side,sg in [('Left',-1),('Right',1)]:
 leg=lu['GearUpper_'+side]
 for kind in ['Upper','Lower']:
  n=lu['GearLink_Torque'+kind+'_'+side];ss=[i for i,x in enumerate(n) if x.startswith('STA ')];states=[]
  for k,j in enumerate(ss):
   R,t=transform(n,k);A,P=transform(leg,k);G=A@Rotation.from_rotvec([0,sg*np.deg2rad(degrees),0]).as_matrix()@A.T;states.append(state(G@R,P+G@(t-P)))
  for j,s in zip(ss,states):n[j]=s
  audit[dnm.name(n)]={'rotation_about_leg_axis_deg':sg*degrees,'all_mesh_resources_unchanged':True,'state_count':len(states)}
path=r/('links-'+str(degrees)+'.dnm');dnm.write(path,p,ns);print(path)
