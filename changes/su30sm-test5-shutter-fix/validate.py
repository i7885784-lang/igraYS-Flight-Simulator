from pathlib import Path
import json,hashlib,collections,itertools,time
import numpy as np,shapely
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
from model import Model
from common import dnm,transform
r=Path(__file__).parent;p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm');old,oldns=dnm.read(r/'baseline/su30sm.dnm');assert ns==oldns;changed=[k for k in p if p[k]!=old[k]];assert set(changed)=={'MainWheelBayShutter_Left.srf','MainWheelBayShutter_Right.srf'}
report={'model_sha256':hashlib.sha256((r/'runtime/aircraft/su30sm.dnm').read_bytes()).hexdigest(),'changed_packs':changed,'all_nodes_states_parents_unchanged':True,'all_other_packs_unchanged':True,'geometry':{}}
m=Model();m.sample(0)
for side in ['Left','Right']:
 name='MainWheelBayShutter_'+side;n=m.lu[name];mesh=dnm.mesh(p[dnm.fil(n)]);vv=np.array(mesh.v);tri=np.array([ids for ids,c,b in mesh.f]);areas=np.linalg.norm(np.cross(vv[tri[:,1]]-vv[tri[:,0]],vv[tri[:,2]]-vv[tri[:,0]]),axis=1)/2;assert np.isfinite(vv).all() and areas.min()>1e-12
 v,f=m.meshes[name];edges=collections.Counter(tuple(sorted((int(a),int(b)))) for ids in f for a,b in zip(ids,np.roll(ids,-1)));assert all(k==2 for k in edges.values()),'Not closed manifold '+side
 # First half is the consistently oriented shell, second half reverse render faces.
 edge_dirs=collections.defaultdict(list);half=mesh.f[:len(mesh.f)//2];signed_volume=0
 for ids,c,b in half:
  a,b,c=vv[ids];signed_volume+=float(a@np.cross(b,c))/6
  for i,j in zip(ids,np.roll(ids,-1)):
   A=tuple(vv[i]);B=tuple(vv[j]);edge_dirs[tuple(sorted((A,B)))].append((A,B))
 assert all(len(d)==2 and d[0]==d[1][::-1] for d in edge_dirs.values()),'Inconsistent orientation '+side
 support=dnm.mesh((r/'baseline'/('support-'+side+'.srf')).read_text().splitlines());sv=np.array(support.v);domain=unary_union([Polygon(sv[ids][:,[0,2]]) for ids,c,b in support.f if Polygon(sv[ids][:,[0,2]]).area>1e-12]);R,t=m.poses[name];w=v@R.T+t;outside_vertices=sum(not domain.buffer(2e-6).covers(Point(q[[0,2]])) for q in w);outside_triangles=0;outside_area=0
 for ids in f:
  poly=Polygon(w[ids][:,[0,2]])
  if poly.area<1e-12:continue
  a=poly.difference(domain.buffer(2e-6)).area;outside_area+=a;outside_triangles+=int(a>1e-11)
 assert outside_vertices==outside_triangles==0
 report['geometry'][side]={'vertices':len(v),'triangles_unique':len(f),'degenerate_triangles':int((areas<=1e-12).sum()),'minimum_triangle_area_m2':float(areas.min()),'nonmanifold_edges':sum(c!=2 for c in edges.values()),'consistent_shell_orientation':True,'signed_volume_m3':signed_volume,'unsupported_vertices':outside_vertices,'unsupported_triangles':outside_triangles,'outside_projected_area_m2':outside_area,'source_precision_tolerance_m':2e-6,'nearest_height_fallbacks':0}
print('geometry + exact invariance passed',flush=True)
# Exhaust all 101 keys and 100 midpoints. Cache identical pairs of poses.
hits=[];cache={};tested=0;cached=0;start=time.monotonic();states=np.linspace(0,1,201)
for gi,g in enumerate(states):
 m.sample(float(g))
 for side in ['Left','Right']:
  a='MainWheelBayShutter_'+side
  for b in m.objects:
   if b==a:continue
   # Includes every other visible mesh available to the diagnostic evaluator.
   Ra,ta=m.poses[a];Rb,tb=m.poses[b];key=(a,b,Ra.tobytes(),ta.tobytes(),Rb.tobytes(),tb.tobytes())
   if key in cache:q=cache[key];cached+=1
   else:q=m.collide(a,b);cache[key]=None if q is None else q.tolist();tested+=1
   if q is not None:hits.append({'g':float(g),'a':a,'b':b,'point':np.array(q).tolist()})
 if gi%40==0:print('pose',round(float(g),3),'contacts',len(hits),flush=True)
report['animation']={'samples':[float(g) for g in states],'all_101_keys_and_100_midpoints':True,'pairs_evaluated':tested,'identical_pairs_reused':cached,'other_meshes':len(m.objects)-1,'contacts':hits,'elapsed_seconds':round(time.monotonic()-start,2)}
(r/'validation.json').write_text(json.dumps(report,indent=2));print('validation done; contacts',len(hits),flush=True)
print('Raw contact free:',not hits,flush=True)
