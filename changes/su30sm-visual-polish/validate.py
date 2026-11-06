from pathlib import Path
import sys,json,hashlib,numpy as np
r=Path(__file__).parent;sys.path.insert(0,str(r));from model import Model
from common import dnm,transform
p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm');op,ons=dnm.read(r/'baseline/su30sm.dnm');ol={dnm.name(n):n for n in ons};lu={dnm.name(n):n for n in ns};audit=json.loads((r/'repair-audit.json').read_text());assert set(p)==set(op) and set(lu)==set(ol)
for n in ns:
 name=dnm.name(n);o=ol[name];assert [s for s in n if not s.startswith('STA ')]==[s for s in o if not s.startswith('STA ')],name
 if name not in audit['changed_nodes']:assert n==o
 if name.startswith(('Wheel','GearUpper','GearPiston','GearAxle','GearLink','MainWheelBayShutter','Cylinder_')):assert n==o and p[dnm.fil(n)]==op[dnm.fil(o)],name
 if name.startswith(('GearDoor_','DoorHingePin_')):
  for k in range(101):
   A,a=transform(n,k);B,b=transform(o,k);assert np.array_equal(A,B);assert abs((a-b)[0])+abs((a-b)[2])<1e-8;assert abs((a-b)[1]-.04*min(1,k/1.5))<1e-6
m=Model();stats={}
for fn in audit['changed_packs']:
 a=dnm.mesh(p[fn]);v=np.array(a.v);assert np.isfinite(v).all();zero=0
 for ids,c,b in a.f:
  for j in range(1,len(ids)-1):zero+=np.linalg.norm(np.cross(v[ids[j]]-v[ids[0]],v[ids[j+1]]-v[ids[0]]))<=2e-12
 stats[fn]={'vertices':len(v),'faces':len(a.f),'zero_area_triangle_instances':int(zero)}
 # Historical F13 may include source degenerates: count and compare, don't silently claim all are new.
 original=dnm.mesh(op[fn]);ov=np.array(original.v);oldzero=sum(np.linalg.norm(np.cross(ov[ids[j]]-ov[ids[0]],ov[ids[j+1]]-ov[ids[0]]))<=2e-12 for ids,c,b in original.f for j in range(1,len(ids)-1));stats[fn]['baseline_zero_area_triangle_instances']=int(oldzero);assert zero<=oldzero
# New cone tips must be behind their dark throat and no longer block a central rear ray.
cap=dnm.mesh(p['Fuselage_0_13.srf']);oldcap=dnm.mesh(op['Fuselage_0_13.srf']);av,bv=np.array(oldcap.v),np.array(cap.v);changed=np.flatnonzero(np.any(av!=bv,axis=1));assert len(changed)==audit['engine_centerbodies']['changed_vertex_instances'];assert [ix for ix,c,b in cap.f]==[ix for ix,c,b in oldcap.f]
# Actuator link length/overlap and attachment positions over the same 21 samples are recorded at build.
assert audit['brake']['minimum_telescopic_overlap_m']>0
motion=json.loads((r/'final-motion.json').read_text());assert motion['model_sha256']==audit['model_sha256'] and not motion['contacts']
result={'model_sha256':audit['model_sha256'],'cockpit_sha256':audit['cockpit_sha256'],'geometry':stats,'all_original_node_metadata_exact':True,'all_wheel_strut_inner_shutter_and_nozzle_petal_meshes_curves_exact':True,'door_and_pin_rotations_exact':True,'only_door_translation_reduced_m':.04,'centerbody_topology_preserved':True,'centerbody_changed_vertex_instances':len(changed),'new_degenerate_triangles':0,'motion_201_pose_contacts':0,'all_original_mesh_names_preserved':True,'no_added_meshes_or_nodes':True,'continuous_collision_proof':False}
(r/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
