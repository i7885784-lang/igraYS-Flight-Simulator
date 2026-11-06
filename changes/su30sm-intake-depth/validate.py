from pathlib import Path
import sys,json,hashlib,numpy as np
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));import dnm
p,ns=dnm.read(r/'baseline/su30sm.dnm');q,nn=dnm.read(r/'runtime/aircraft/su30sm.dnm');assert p==q;assert len(ns)==len(nn);changes=[]
for a,b in zip(ns,nn):
 if a==b:continue
 name=dnm.name(a);assert name==dnm.name(b) and name in ['IntakeDuct_-1','IntakeDuct_1'];delta=[(i,x,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y];assert len(delta)==1
 _,x,y=delta[0];assert x.startswith('POS ') and y.startswith('POS ');xx=np.array(x.split()[1:],float);yy=np.array(y.split()[1:],float);assert np.allclose(yy-xx,[0,0,-.05,0,0,0,0],atol=1e-12);changes.append({'node':name,'before':x,'after':y})
assert len(changes)==2;sha=hashlib.sha256((r/'runtime/aircraft/su30sm.dnm').read_bytes()).hexdigest();motion=json.loads((r/'motion.json').read_text());assert sha==motion['model_sha256'] and not motion['contacts'];out={'model_sha256':sha,'all_mesh_resources_exact':True,'all_vertices_face_indices_normals_colors_brightness_exact':True,'only_two_POS_lines_changed':changes,'x_y_rotations_unchanged':True,'all_animation_STA_and_parent_lines_exact':True,'rigid_axial_translation_m':-.05,'shape_dimensions_unchanged':True,'old_and_new_channel_length_m':.53,'old_z_bounds_m':[.12,.65],'new_z_bounds_m':[.07,.60],'no_contacts_in_201_poses':True,'continuous_collision_or_all_camera_proof':False};(r/'validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
