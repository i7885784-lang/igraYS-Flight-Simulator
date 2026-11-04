from pathlib import Path
import numpy as np,json,hashlib,collections,sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'model-source'))
from common import *
from surface import build_surface
r=Path(__file__).parent;p,ns=dnm.read(r/'baseline/su30sm.dnm');original={k:list(v) for k,v in p.items()};audit={}
for side in ['Left','Right']:
 n=next(n for n in ns if dnm.name(n)=='MainWheelBayShutter_'+side);R,t=transform(n,0);old_mesh=dnm.mesh(p[dnm.fil(n)]);oldv=np.array(old_mesh.v)@R.T+t;paints={}
 for ids,c,b in old_mesh.f:
  for k in range(1,len(ids)-1):
   q=oldv[[ids[0],ids[k],ids[k+1]]];area=np.cross(q[1]-q[0],q[2]-q[0])[1]
   if abs(area)<1e-10:continue
   key=tuple(sorted(tuple(np.round(v[[0,2]],6)) for v in q));old=paints.get(key)
   if old is None or q[:,1].mean()<old[0][:,1].mean()-1e-8:paints[key]=(q,c)
 support=dnm.mesh((r/'baseline'/('support-'+side+'.srf')).read_text().splitlines());v=np.array(support.v);v,idx=np.unique(np.round(v,6),axis=0,return_inverse=True);tri=np.array([idx[ids] for ids,c,b in support.f]);unique={}
 for ids in tri:unique[tuple(sorted(ids))]=ids
 tri=np.array(list(unique.values()));
 if '--retriangulate' in sys.argv:
  v,tri,colors,meta=build_surface(v,tri,side,list(paints.values()))
 else:
  expected={'su30sm.dnm':'17ddccbe820b4220463d2b4303f36460cb5effc7aa10973c7693dc1d1a68a504',**json.loads((r/'source-data/layout-input-hashes.json').read_text())}
  for filename,digest in expected.items():assert hashlib.sha256((r/'baseline'/filename).read_bytes()).hexdigest()==digest, 'Changed input: use --retriangulate and repeat geometry/game verification'
  layout=json.loads((r/'source-data'/('validated-layout-'+side+'.json')).read_text());v=np.array(layout['vertices']);tri=np.array(layout['triangles']);colors=[tuple(c) for c in layout['colors']];meta=layout['metadata']
 edge=collections.Counter(tuple(sorted((int(a),int(b)))) for ids in tri for a,b in zip(ids,np.roll(ids,-1)));directed={tuple(sorted((int(a),int(b)))):(int(a),int(b)) for ids in tri for a,b in zip(ids,np.roll(ids,-1))};boundary=[directed[e] for e,c in edge.items() if c==1];m=Mesh();offset=np.array([0,-.008,0]);color=(142,169,181)
 for ids,color in zip(tri,colors):
  q=v[ids];m.face((q+offset-t)@R,color);m.face((q[::-1]-t)@R,(98,113,121))
 for a,b in boundary:
  q=np.array([v[b]+offset,v[a]+offset,v[a],v[b]]);m.face((q[[0,1,2]]-t)@R,(104,120,130));m.face((q[[0,2,3]]-t)@R,(104,120,130))
 m.f += [(ids[::-1],c,b) for ids,c,b in list(m.f)];p[dnm.fil(n)]=m.srf();audit[side]={'surface':meta,'support_triangles':len(tri),'boundary_edges':len(boundary),'nonmanifold_support_edges':sum(c>2 for c in edge.values()),'nearest_vertex_fallbacks':0}
# Preserve every state, pivot, parent and unrelated mesh byte-for-byte.
changed=[k for k in p if p[k]!=original[k]];assert len(changed)==2
output=r/'runtime/aircraft/su30sm.dnm';temp=output.with_suffix('.dnm.building');dnm.write(temp,p,ns);p2,n2=dnm.read(temp);assert n2==ns
for k in p:
 if k not in changed:assert p2[k]==original[k]
assert set(changed)=={'MainWheelBayShutter_Left.srf','MainWheelBayShutter_Right.srf'}
temp.replace(output)
(r/'refinement.json').write_text(json.dumps({'changed_packs':changed,'nodes_unchanged':True,'audit':audit,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()},indent=2));print({s:{'surface_triangles':v['surface']['surface_triangles'],'unsupported_cells':v['surface']['unsupported_cells'],'area_retained_fraction':v['surface']['projected_area_retained_fraction']} for s,v in audit.items()})
