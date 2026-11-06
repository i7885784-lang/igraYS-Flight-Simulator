from pathlib import Path
import json,hashlib,numpy as np,collections
from scipy.spatial import cKDTree
from model import Model
r=Path(__file__).parent;m=Model();old=Model(r/'baseline/su30sm.dnm');m.sample(0);stats={};ext=[]
for n,(v,f) in m.meshes.items():
 assert np.isfinite(v).all() and f.min()>=0 and f.max()<len(v)
 q=v[f];zero=int(np.sum(np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)<1e-12));R,t=m.poses[n];world=v@R.T+t;ext.append(world)
 if n in ['Fuselage_0_4','IntakeDuct_-1','IntakeDuct_1'] or zero:stats[n]={'triangles':len(f),'degenerate_triangles_including_unchanged_source':zero}
v=np.concatenate(ext);sym={}
for n in ['Fuselage_0_4']:
 v0=m.meshes[n][0];R,t=m.poses[n];v0=np.unique(np.round(v0@R.T+t,6),axis=0);mir=v0.copy();mir[:,0]*=-1;dist,_=cKDTree(v0).query(mir);sym[n]={'max_reflected_vertex_distance_m':float(dist.max()),'p99_m':float(np.percentile(dist,99))}
left=m.meshes['IntakeDuct_-1'][0];right=m.meshes['IntakeDuct_1'][0]
a=left@m.poses['IntakeDuct_-1'][0].T+m.poses['IntakeDuct_-1'][1];b=right@m.poses['IntakeDuct_1'][0].T+m.poses['IntakeDuct_1'][1];a[:,0]*=-1;d,_=cKDTree(b).query(a);sym['new_intake_pair']={'max_reflection_m':float(d.max())}
contacts=[]
for g in np.linspace(0,1,201):
 m.sample(float(g))
 for side in ['Left','Right']:
  a='GearLink_TorqueUpper_'+side;b='MainBayFixedSkin_'+side;q=m.collide(a,b)
  if q is not None:contacts.append({'gear':round(float(g),3),'a':a,'b':b,'point':q.tolist()})
base=Path('/workspace/ysflight-dev/su30sm-intake-depth/runtime');rt=r/'runtime';names=[x.relative_to(base) for x in base.rglob('*') if x.is_file()];diff=[str(x) for x in names if (base/x).read_bytes()!=(rt/x).read_bytes()];assert diff==['aircraft/su30sm.dnm'],diff
out={'model_sha256':hashlib.sha256(m.path.read_bytes()).hexdigest(),'finite_coordinates_valid_indices_all_meshes':True,'unchanged_other_runtime_file_count':len(names)-1,'changed_runtime_files':diff,'symmetry':sym,'sampled_geometry':stats,'inherited_torque_contacts_201_samples':contacts,'notes':'Global finite/index/vertex-symmetry inventory; not a proof of absence of all old intersections or factory-dimensional accuracy.'};(r/'global-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='sampled_geometry'},indent=2))
