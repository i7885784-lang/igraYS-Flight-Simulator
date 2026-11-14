"""Scope, animation, material and closed-shell checks against the exact saved baseline."""
import sys
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parent.parent/'su30sm-local-skin'))
from repair import *
NAMES=['MainBayFixedSkin_Left','MainBayFixedSkin_Right']
import trimesh

def verify(baseline,candidate,output):
 p,ns=dnm.read(baseline);q,nt=dnm.read(candidate);assert ns==nt,'Animation/node records changed';assert list(p)==list(q),'Packs added/removed'
 lu={dnm.name(n):n for n in ns};changed=[k for k in p if p[k]!=q[k]];assert set(changed)=={dnm.fil(lu[n]) for n in NAMES}|{'Fuselage_0_4.srf'}
 result={'baseline_sha256':sha(baseline.read_bytes()),'model_sha256':sha(candidate.read_bytes()),'all_node_records_exact':True,'node_count':len(ns),'changed_packs':changed,'protected_pack_sha256':{k:sha(('\n'.join(v)+'\n').encode()) for k,v in p.items() if k not in changed},'geometry':{}}
 for name in NAMES:
  lines=q[dnm.fil(lu[name])];m=dnm.mesh(lines);v=np.array(m.v);assert np.isfinite(v).all();tri=[];deg=0;zero_normals=0;dots=[];i=lines.index('F');seen=set();duplicate=0
  oldcolors={c for ids,c,b in dnm.mesh(p[dnm.fil(lu[name])]).f};assert {c for ids,c,b in m.f}<=oldcolors
  for ids,c,b in m.f:
   assert min(ids)>=0 and max(ids)<len(v)
   qq=v[ids];normal=sum((np.cross(a,b) for a,b in zip(qq,np.roll(qq,-1,axis=0))),np.zeros(3));length=np.linalg.norm(normal)
   end=lines.index('E',i);record=np.array(next(s[2:] for s in lines[i:end] if s.startswith('N ')).split(),float);zero_normals+=int(np.linalg.norm(record)<.5)
   if length>1e-12:dots.append(float(record@normal/length))
   for j in range(1,len(ids)-1):
    t=ids[0],ids[j],ids[j+1];a,b1,c1=v[list(t)];area=np.linalg.norm(np.cross(b1-a,c1-a))/2
    if area<1e-14:deg+=1;continue
    tri.append(t)
   key=tuple(sorted(tuple(a) for a in np.round(qq,8)));duplicate+=int(key in seen);seen.add(key);i=end+1
  mesh=trimesh.Trimesh(vertices=v,faces=np.array(tri),process=False);raw_watertight=bool(mesh.is_watertight);raw_consistent=bool(mesh.is_winding_consistent);raw_components=mesh.split(only_watertight=False);component_areas=sorted([float(c.area) for c in raw_components],reverse=True);mesh.merge_vertices(digits_vertex=8);mesh.remove_unreferenced_vertices()
  stats={'vertices':len(v),'faces':len(m.f),'triangles':len(tri),'degenerate_triangles_below_1e-14_m2':deg,'zero_face_normals':zero_normals,'min_normal_winding_dot':min(dots),'duplicate_polygons_at_1e-8m':duplicate,'indexed_shell_watertight':raw_watertight,'indexed_winding_consistent':raw_consistent,'indexed_component_areas_m2':component_areas,'watertight_after_1e-8m_merge':bool(mesh.is_watertight),'winding_consistent':bool(mesh.is_winding_consistent),'connected_components':len(mesh.split(only_watertight=False)),'euler_number':int(mesh.euler_number)}
  result['geometry'][name]=stats;print(name,stats,flush=True)
 assert all(x['indexed_shell_watertight'] and x['indexed_winding_consistent'] and len(x['indexed_component_areas_m2'])==1 for x in result['geometry'].values())
 assert not any(x['zero_face_normals'] or x['min_normal_winding_dot']<.99 or x['degenerate_triangles_below_1e-14_m2'] or x['duplicate_polygons_at_1e-8m'] for x in result['geometry'].values())
 output.write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--baseline',required=True,type=Path);parser.add_argument('--candidate',required=True,type=Path);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args();verify(args.baseline,args.candidate,args.output)
