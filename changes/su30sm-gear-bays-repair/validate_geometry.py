from pathlib import Path
import sys,json,hashlib,collections,numpy as np
from model import Model
from common import dnm
r=Path(__file__).parent;p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm');old,on=dnm.read(r/'baseline/su30sm.dnm');oldn={dnm.name(n):n for n in on};assert set(old)<=set(p);changed=[k for k in old if p[k]!=old[k]];retimed=[]
for n in ns:
 name=dnm.name(n)
 if name not in oldn:continue
 a=oldn[name]
 assert [s for s in n if not s.startswith('STA ')]==[s for s in a if not s.startswith('STA ')],name
 if n!=a:
  assert name.startswith('MainWheelBayShutter_');retimed.append(name)
 assert len([s for s in n if s.startswith('STA ')])==len([s for s in a if s.startswith('STA ')])
for name in ['Fuselage_0_4','Fuselage_0_5']:
 n=oldn[name];fn=dnm.fil(n)
 if fn not in changed:continue
 a,b=dnm.mesh(old[fn]),dnm.mesh(p[fn]);av,bv=np.array(a.v),np.array(b.v);assert np.array_equal(av,bv[:len(av)]),'Existing body vertices changed';bf={(tuple(ids),c,k) for ids,c,k in b.f};R,t=Model().poses[name];missing=[]
 for ids,c,k in a.f:
  if (tuple(ids),c,k) in bf:continue
  q=av[ids]@R.T+t;assert q[:,2].min()<4.45001 and q[:,2].max()>4.15999 and q[:,0].min()<.38001 and q[:,0].max()>-.38001 and q[:,1].mean()<-.15;missing.append(ids)
 print(name,'only',len(missing),'original face instances clipped inside nose-fore scope',flush=True)
m=Model();geometry={}
for name,n in m.lu.items():
 fn=dnm.fil(n)
 if fn not in changed and fn in old:continue
 raw=dnm.mesh(p[fn]);v=np.array(raw.v);areas=[]
 for ids,c,b in raw.f:
  for j in range(1,len(ids)-1):areas.append(np.linalg.norm(np.cross(v[ids[j]]-v[ids[0]],v[ids[j+1]]-v[ids[0]]))/2)
 zero=int(sum(a<=1e-12 for a in areas));assert np.isfinite(v).all();vv,ff=m.meshes[name];edge=collections.Counter(tuple(sorted((int(a),int(b)))) for f in ff for a,b in zip(f,np.roll(f,-1)))
 geometry[name]={'unique_vertices':len(vv),'unique_triangles':len(ff),'zero_area_triangles':zero,'non_two_sided_edges':sum(n!=2 for n in edge.values())}
 if name.startswith(('GearDoor_','MainWheelBayShutter_')):print(name,geometry[name],flush=True)
 assert zero==0,name+' zero-area triangles'
report={'model_sha256':hashlib.sha256((r/'runtime/aircraft/su30sm.dnm').read_bytes()).hexdigest(),'changed_packs':changed,'retimed_original_nodes':retimed,'all_other_original_nodes_exact':True,'all_original_node_metadata_exact':True,'all_other_meshes_byte_exact':True,'geometry':geometry};(r/'geometry-validation.json').write_text(json.dumps(report,indent=2))
