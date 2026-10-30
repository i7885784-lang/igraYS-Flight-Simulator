from pathlib import Path
import sys,json,numpy as np,fcl
from scipy.spatial.transform import Rotation
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));import dnm
from common import transform

def make_mesh(m):
 vertices,index=np.unique(np.round(m.v,6),axis=0,return_inverse=True);faces=[]
 for ids,col,b in m.f:
  for k in range(1,len(ids)-1):
   tri=index[[ids[0],ids[k],ids[k+1]]]
   q=vertices[tri]
   if np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))>1e-10:faces.append(tri)
 faces=np.unique(np.sort(faces,axis=1),axis=0).astype(np.int32);model=fcl.BVHModel();model.beginModel(len(vertices),len(faces));model.addSubModel(vertices,faces);model.endModel();return model


p,ns=dnm.read(r/'runtime/aircraft/su27.dnm');walls=[n for n in ns if dnm.name(n).startswith('ConformalMainBayLiner')];moving=[n for n in ns if dnm.cla(n)==210];objects={dnm.name(n):fcl.CollisionObject(make_mesh(dnm.mesh(p[dnm.fil(n)]))) for n in walls+moving};hits=[];req=fcl.CollisionRequest(num_max_contacts=1,enable_contact=True)
for u in np.linspace(0,1,401):
 for n in moving:
  count=sum(s.startswith('STA ') for s in n);s=u*(count-1);i=min(count-2,int(s));f=s-i;R,t=transform(n,i);S,v=transform(n,i+1);z=R[:,2]*(1-f)+S[:,2]*f;z/=np.linalg.norm(z);y=R[:,1]*(1-f)+S[:,1]*f;x=np.cross(y,z);x/=np.linalg.norm(x);y=np.cross(z,x);objects[dnm.name(n)].setTransform(fcl.Transform(np.c_[x,y,z],t*(1-f)+v*f))
 for n in moving:
  for wall in walls:
   res=fcl.CollisionResult()
   if fcl.collide(objects[dnm.name(n)],objects[dnm.name(wall)],req,res):hits.append({'gear':float(u),'part':dnm.name(n),'wall':dnm.name(wall)})
result={'passed':not hits,'poses':401,'moving_nodes':len(moving),'hits':hits};(r/'collision-checks.json').write_text(json.dumps(result,indent=2));print('PASS',not hits,'hits',len(hits));print(hits[:10])
