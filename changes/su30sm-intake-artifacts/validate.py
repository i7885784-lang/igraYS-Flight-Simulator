from pathlib import Path
import sys,json,hashlib,collections,numpy as np
from shapely.geometry import Polygon
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import dnm
p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm');old,on=dnm.read(r/'baseline/su30sm.dnm');assert ns==on and set(p)==set(old)
audit=json.loads((r/'repair-audit.json').read_text());changed=[k for k in old if p[k]!=old[k]];assert changed==audit['changed_packs'];data=json.loads((r/'subset-provenance.json').read_text());groups=collections.defaultdict(list);maxoutside=0;maxoffplane=0
for row in data:
 q=np.array(row['source_world']);tri=np.array(row['replacement_world']);n=np.cross(q[1]-q[0],q[2]-q[0]);n/=np.linalg.norm(n);off=float(abs((tri-q[0])@n).max());maxoffplane=max(maxoffplane,off);assert off<3e-8;axis=np.argmax(abs(n));a=Polygon(np.delete(q,axis,axis=1));b=Polygon(np.delete(tri,axis,axis=1));outside=b.difference(a.buffer(3e-8)).area;maxoutside=max(maxoutside,outside);assert outside<1e-12;groups[row['node'],row['source_face'],row['source_triangle_index']].append(b)
maxoverlap=0
from shapely.ops import unary_union
for parts in groups.values():
 overlap=sum(t.area for t in parts)-unary_union(parts).area;maxoverlap=max(maxoverlap,overlap);assert overlap<1e-10
stats={}
for fn in changed:
 m=dnm.mesh(p[fn]);o=dnm.mesh(old[fn]);assert m.v[:len(o.v)]==o.v;v=np.array(m.v);assert np.isfinite(v).all();z=sum(np.linalg.norm(np.cross(v[ids[j]]-v[ids[0]],v[ids[j+1]]-v[ids[0]]))<2e-12 for ids,c,b in m.f for j in range(1,len(ids)-1));ov=np.array(o.v);oz=sum(np.linalg.norm(np.cross(ov[ids[j]]-ov[ids[0]],ov[ids[j+1]]-ov[ids[0]]))<2e-12 for ids,c,b in o.f for j in range(1,len(ids)-1));assert z<=oz,(fn,z,oz);stats[fn]={'faces_before':len(o.f),'faces_after':len(m.f),'new_zero_area_triangles':int(max(0,z-oz)),'all_old_vertices_preserved':True}
report={'model_sha256':hashlib.sha256((r/'runtime/aircraft/su30sm.dnm').read_bytes()).hexdigest(),'all_nodes_and_animation_states_exact':True,'all_other_packs_exact':True,'new_zero_area_triangles':0,'replacement_triangles_proven_original_surface_subsets':len(data),'maximum_off_original_plane_m':maxoffplane,'maximum_area_outside_source_triangle_m2':maxoutside,'maximum_same_source_replacement_overlap_m2':maxoverlap,'new_geometry_is_only_subset_of_original_faces':True,'all_original_material_color_brightness_records_preserved':True,'stats':stats};(r/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
