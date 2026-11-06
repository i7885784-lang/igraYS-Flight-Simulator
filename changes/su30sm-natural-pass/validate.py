from pathlib import Path
import sys,json,hashlib,collections,numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import *
a,an=dnm.read(r/'baseline/su30sm.dnm');b,bn=dnm.read(r/'runtime/aircraft/su30sm.dnm');assert an==bn and set(a)==set(b);changed=[s for s in a if a[s]!=b[s]];assert set(changed)=={'IntakeDuct_-1.srf','IntakeDuct_1.srf'};stats={}
for name in changed:
 m=dnm.mesh(b[name]);v,inv=np.unique(np.round(m.v,6),axis=0,return_inverse=True);faces=[];seen=set();deg=dups=0;emissive=0;caps=[];walls=[]
 for ids,c,bright in m.f:
  assert all(18<=v<=65 for v in c);emissive+=int(bright)
  for k in range(1,len(ids)-1):
   ix=inv[[ids[0],ids[k],ids[k+1]]];q=v[ix];n=np.cross(q[1]-q[0],q[2]-q[0]);deg+=int(np.linalg.norm(n)<1e-12);key=tuple(sorted(map(int,ix)));dups+=int(key in seen);seen.add(key);faces.append(ix)
   if abs(q[:,2].max()-q[:,2].min())<1e-7:assert n[2]>0;caps.append(Polygon(q[:,:2]))
   else:
    centre=np.array([-1.1 if '-1' in name else 1.1,-.55,0]);target=centre-q.mean(0);target[2]=0;assert n@target>0;walls.append(q)
 edges=collections.Counter(tuple(sorted((int(x),int(y)))) for ix in faces for x,y in zip(ix,np.roll(ix,-1)));boundary=[(v[x],v[y]) for (x,y),count in edges.items() if count==1];bad=[count for count in edges.values() if count>2];unexpected=[(a.tolist(),b.tolist()) for a,b in boundary if max(abs(a[2]-.65),abs(b[2]-.65))>1e-6];overlap=sum(t.area for t in caps)-unary_union(caps).area
 assert deg==0 and dups==0 and emissive==0 and not bad and not unexpected and overlap<1e-8,(name,deg,dups,bad[:2],len(unexpected),overlap)
 stats[name]={'unique_vertices':len(v),'triangles':len(faces),'degenerate_triangles':deg,'duplicate_reverse_triangles':dups,'nonmanifold_edges':len(bad),'unexpected_open_edges':len(unexpected),'open_front_boundary_edges':len(boundary),'rear_cap_projection_overlap_m2':overlap,'normals_inward_walls_and_forward_rear_cap':True,'emissive_faces':emissive}
sha=hashlib.sha256((r/'runtime/aircraft/su30sm.dnm').read_bytes()).hexdigest();motion=json.loads((r/'motion.json').read_text());assert sha==motion['model_sha256'] and not motion['contacts'];sections=json.loads((r/'sections.json').read_text());assert max(s['area_error_m2'] for s in sections)<1e-8
out={'model_sha256':sha,'changed_packs':changed,'all_other_packs_original_geometry_and_paint_exact':True,'all_nodes_parents_states_animations_exact':True,'all_gear_and_doors_exact':True,'gear_sweep_samples':201,'insert_vs_other_object_contacts':0,'max_measured_section_area_error_m2':max(s['area_error_m2'] for s in sections),'geometry':stats,'universal_camera_or_continuous_collision_proof':False};(r/'validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
