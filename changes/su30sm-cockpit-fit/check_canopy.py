"""Sample the unchanged native canopy interpolation against the repaired interior."""
import sys,json,numpy as np,fcl
from pathlib import Path
from scipy.spatial.transform import Rotation
from check import dnm,geometry,obj,classify
path=Path(sys.argv[1]);p,ns=dnm.read(path/'su30sm.dnm');audit=json.loads((path/'audit.json').read_text());result={'samples':201,'collisions':[]}
parts={name:geometry(p,ns,'Su30Interior.srf',set(range(a,b))) for name,(a,b) in audit['parts'].items()};objects={k:obj(v,ix) for k,(v,ix,src) in parts.items()}
for name in ['Cockpit_cover_6_30.srf','Cockpit_cover_6_31.srf']:
 n=next(n for n in ns if dnm.fil(n)==name);pos=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);m=dnm.mesh(p[name]);v=np.array(m.v);ix=np.array([q for q,c,b in m.f]);o=obj(v,ix);st=[s.split()[1:] for s in n if s.startswith('STA ')]
 def rotation(s):
  h,p,b=np.array(s[3:6],float)*np.pi/32768;return Rotation.from_euler('YXZ',[-h,-p,b]).as_matrix()
 A=rotation(st[0]);B=rotation(st[1])
 for step,u in enumerate(np.linspace(0,1,201)):
  z=(1-u)*A[:,2]+u*B[:,2];z/=np.linalg.norm(z);y=(1-u)*A[:,1]+u*B[:,1];x=np.cross(y,z);x/=np.linalg.norm(x);R=np.c_[x,np.cross(z,x),z];T=pos+(1-u)*np.array(st[0][:3],float)+u*np.array(st[1][:3],float);o.setTransform(fcl.Transform(R,T));tv=v@R.T+T
  for part,static in objects.items():
   res=fcl.CollisionResult();fcl.collide(static,o,fcl.CollisionRequest(num_max_contacts=5000,enable_contact=True),res)
   for c in res.contacts:
    pv,pi,src=parts[part];k=classify(pv[pi[c.b1]],tv[ix[c.b2]],tol=2e-6)
    if k in ['cross','coplanar_overlap']:
     result['collisions'].append(dict(canopy=name,part=part,pose=round(float(u),4),kind=k,part_face=src[c.b1],canopy_face=int(c.b2)));break
  if step%50==0:print(name,step,'collisions',len(result['collisions']),flush=True)
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print('TOTAL',len(result['collisions']))
