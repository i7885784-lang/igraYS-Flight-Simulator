from pathlib import Path
import json,sys,hashlib,numpy as np,collections
from shapely.geometry import Polygon
from shapely.ops import unary_union
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import *
a,an=dnm.read(r/'baseline/su30sm.dnm');b,bn=dnm.read(r/'runtime/aircraft/su30sm.dnm');assert an==bn and set(a)==set(b);changed=[k for k in a if a[k]!=b[k]];stats={};paint={(142,169,181),(77,139,163),(118,166,185),(147,163,172)}
for name in changed:
 m=dnm.mesh(b[name]);v=np.array(m.v);zeros=0;seen=set();dups=0;polys=[];wrong_emissive=0;normals=[]
 for ids,c,bright in m.f:
  assert all(0<=i<len(v) for i in ids)
  wrong_emissive+=int(bright)
  for k in range(1,len(ids)-1):
   q=v[[ids[0],ids[k],ids[k+1]]];n=np.cross(q[1]-q[0],q[2]-q[0]);length=np.linalg.norm(n)
   if length<1e-12:zeros+=1
   key=tuple(sorted(tuple(a) for a in np.round(q,7)));dups+=int(key in seen);seen.add(key)
   if c in paint and n[1]<-1e-10:polys.append(Polygon(q[:,[0,2]]))
 overlap=sum(p.area for p in polys)-unary_union(polys).area if polys else 0
 stats[name]={'vertices':len(v),'faces':len(m.f),'degenerate_triangles':zeros,'duplicate_or_reverse_triangles':dups,'exterior_projected_overlap_m2':overlap,'emissive_faces':wrong_emissive}
 assert zeros==0,(name,zeros)
 if name.startswith(('MainBayFixedSkin','MainWheelBayShutter','GearDoor')):assert dups==0 and overlap<3e-6,(name,dups,overlap)
assert a['IntakeDuct_-1.srf']==b['IntakeDuct_-1.srf'] and a['IntakeDuct_1.srf']==b['IntakeDuct_1.srf']
assert a['GearWell_Nose.srf']==b['GearWell_Nose.srf']
sha=hashlib.sha256((r/'runtime/aircraft/su30sm.dnm').read_bytes()).hexdigest();motion=json.loads((r/'motion-comparison.json').read_text());assert motion['model_sha256']==sha and len(motion['new_pair_poses'])==0
out={'model_sha256':sha,'all_nodes_STAs_parents_pivots_exact':True,'intake_dark_channels_exact':True,'original_airframe_engine_meshes_exact':all(a[k]==b[k] for k in a if k.startswith(('Fuselage','Intake','Su30Nozzle'))),'no_new_nodes':True,'changed_packs':changed,'geometry':stats,'motion_samples':201,'new_pair_poses':0,'removed_pair_poses':len(motion['removed_pair_poses']),'inherited_pair_poses':len(motion['after_contacts']),'continuous_collision_proof':False,'self_intersection_scope':'Single-valued projected outer sheets and matching inward 8mm sheets, rim walls only on actual union boundary. No all-aircraft self-intersection assertion.'};(r/'validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
