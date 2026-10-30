from pathlib import Path
import sys,json,numpy as np,fcl
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
def make_mesh(m):
 vertices,index=np.unique(np.round(m.v,6),axis=0,return_inverse=True);faces=[]
 for ids,col,b in m.f:
  for k in range(1,len(ids)-1):
   tri=index[[ids[0],ids[k],ids[k+1]]]
   q=vertices[tri]
   if np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))>1e-10:faces.append(tri)
 faces=np.unique(np.sort(faces,axis=1),axis=0).astype(np.int32);model=fcl.BVHModel();model.beginModel(len(vertices),len(faces));model.addSubModel(vertices,faces);model.endModel();return model



p,ns=dnm.read(r/'runtime/aircraft/su34.dnm');bp,bns=dnm.read(r/'baseline/su34.dnm');lu={dnm.name(n):n for n in ns};checks={'all_original_mesh_packs_unchanged':all(p[k]==v for k,v in bp.items()),'all_original_nodes_states_unchanged':all(n==lu[dnm.name(n)] for n in bns)};hits=[]
for n in ns:
 if not dnm.name(n).startswith('Su34RearBayInnerWall'):continue
 a=fcl.CollisionObject(make_mesh(dnm.mesh(p[dnm.fil(n)])))
 for other in ns:
  if not dnm.name(other).startswith(('InsideIntake','Source_prop_')):continue
  b=fcl.CollisionObject(make_mesh(dnm.mesh(p[dnm.fil(other)])));res=fcl.CollisionResult()
  if fcl.collide(a,b,fcl.CollisionRequest(),res):hits.append([dnm.name(n),dnm.name(other)])
checks['airduct_and_compressor_intersections']=hits;assert not hits and all(checks[k] for k in ['all_original_mesh_packs_unchanged','all_original_nodes_states_unchanged']),checks
(r/'preservation-checks.json').write_text(json.dumps(checks,indent=2));print(checks)
