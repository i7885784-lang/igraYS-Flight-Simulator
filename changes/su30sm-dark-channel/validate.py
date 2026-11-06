from pathlib import Path
import sys,json,hashlib,collections,numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
r=Path(__file__).parent;sys.path.insert(0,str(r));from model import Model
from common import dnm
old,on=dnm.read(r/'baseline/su30sm.dnm');p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm');assert ns==on and set(p)==set(old);changed=[k for k in old if old[k]!=p[k]];assert set(changed)=={'IntakeDuct_-1.srf','IntakeDuct_1.srf'};m=Model();stats={}
for side in [-1,1]:
 name='IntakeDuct_'+str(side);raw=dnm.mesh(p[name+'.srf']);v,f=m.meshes[name];rawv=np.array(raw.v);tri=[];zarea=0
 for ids,c,b in raw.f:
  assert c==(25,30,33) and not b
  for j in range(1,len(ids)-1):
   q=rawv[[ids[0],ids[j],ids[j+1]]];n=np.cross(q[1]-q[0],q[2]-q[0]);assert np.linalg.norm(n)>1e-12 and n[2]>1e-12;tri.append(Polygon(q[:,:2]));zarea+=np.linalg.norm(n)/2
 overlap=sum(a.area for a in tri)-unary_union(tri).area;assert overlap<1e-9
 edges=collections.Counter(tuple(sorted((int(a),int(b)))) for q in f for a,b in zip(q,np.roll(q,-1)));assert all(n in [1,2] for n in edges.values());assert sum(n==1 for n in edges.values())==48
 m.sample(1);static={s:m.collide(name,s) is not None for s in ['Fuselage_0_4','GearWell_Left','GearWell_Right']};stats[name]={'vertices':len(v),'unique_triangles':len(f),'zero_area_triangles':0,'same_xy_projection_overlap_m2':overlap,'open_inlet_boundary_edges':48,'other_edges_two_faces':True,'no_duplicate_or_reverse_surface_faces':True,'all_face_normals_towards_inlet':True,'emissive_faces':0,'original_body_or_bay_intersections':static,'area_m2':zarea,'depth_m':float(v[:,2].max()-v[:,2].min())}
 assert not any(static.values()),static
motion=json.loads((r/'motion.json').read_text());sha=hashlib.sha256((r/'runtime/aircraft/su30sm.dnm').read_bytes()).hexdigest();assert motion['model_sha256']==sha and not motion['contacts']
out={'model_sha256':sha,'changed_packs':changed,'all_nodes_states_pivots_parents_exact':True,'all_other_meshes_including_original_aircraft_skin_byte_exact':True,'no_new_nodes':True,'exterior_paint_exact':True,'internal_material_only':[25,30,33],'motion_201_pose_contacts':0,'geometry':stats,'continuous_collision_proof':False};(r/'validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
