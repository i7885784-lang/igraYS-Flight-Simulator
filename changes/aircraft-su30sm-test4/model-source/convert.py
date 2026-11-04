from pathlib import Path
import sys,json,numpy as np,math,hashlib,io
from PIL import Image
from scipy.spatial import ConvexHull
from gltf_source import GLB
from nozzle import Nozzles
from nozzle_geometry import flame
from common import Mesh,add,state,dnm,Rotation
r=Path(__file__).resolve().parent.parent;out=r/'runtime/aircraft';out.mkdir(parents=True,exist_ok=True);g=GLB(r/'source/su-30sm.glb');d=g.d
vv=np.concatenate([v for i,n in enumerate(d['nodes']) if 'mesh' in n for v,ids,mat,prim in g.mesh(i)]);lo,hi=vv.min(0),vv.max(0);scale=21.935/(hi[2]-lo[2]);center=(lo+hi)/2;center[1]=0
cv=lambda v:(np.array(v)-center)*scale
nozzle=Nozzles(g,scale,center);nozzle.save(r)
packs={};nodes=[];metadata={'source_triangles':0,'scale':scale,'bounds_m':[cv(lo).tolist(),cv(hi).tolist()],'components':[]};static={};petals=[]
def srgb(v):v=np.array(v);return np.where(v<=.0031308,v*12.92,1.055*np.maximum(v,0)**(1/2.4)-.055)
def material(k):
 mat=d['materials'][k];f=mat.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1]);col=np.clip(np.rint(srgb(f[:3])*255),0,255).astype(int).tolist()
 if mat.get('alphaMode')=='BLEND':col=[88,138,162,130]
 return tuple(col)
def reverse(m):m.f += [(ids[::-1],c,b) for ids,c,b in list(m.f)]
for i,n in enumerate(d['nodes']):
 if 'mesh' not in n:continue
 parent=g.parents[i];name=d['nodes'][parent].get('name','part')+'_'+str(i);name=name.replace(' ','_').replace('.','_');m=Mesh();m.normals=[];count=0
 for v,ids,mat,prim in g.mesh(i):
  offset=len(m.v);m.v.extend(map(tuple,cv(v)));N=g.acc(prim['attributes']['NORMAL'])@np.linalg.inv(g.world(i)[:3,:3]);N/=np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-15);m.normals.extend(map(tuple,N));m.f.extend((list(q+offset),material(mat),False) for q in ids);count+=len(ids)
 metadata['source_triangles']+=count;W=g.world(parent);pivot=cv(W[:3,3]);m.v=[tuple(np.array(v)-pivot) for v in m.v];cla=99;states=None;kind=d['nodes'][parent].get('name','')
 if kind.startswith('Cylinder'):
  cla=270;petals.append((i,parent,m,pivot))
  # Full original petal geometry; bounded source articulation between closed(t10) and rest.
  M0=g.world(parent);Mc=g.world(parent,10.);Rc=Mc[:3,:3]@np.linalg.inv(M0[:3,:3]);states=[state(nozzle.rotation(parent,float(u))) for u in np.linspace(0,1,21)];m.f=[(ids,(111,115,123),b) for ids,c,b in m.f]
 elif kind.startswith(('Front Stabilizers','Elevator','Aileron','Rudder','Flaps','Air Brake','Cockpit.cover')):
  cla=6 if kind.startswith(('Front Stabilizers','Elevator')) else 7 if kind.startswith('Aileron') else 8 if kind.startswith('Rudder') else 5 if kind.startswith('Flaps') else 212 if kind.startswith('Air Brake') else 211
  # Use source pivots and rotation axes, bound extreme demo movements for gameplay.
  ts,vs,_=g.tracks[parent,'rotation'];R0=g.world(parent)[:3,:3];rots=[Rotation.from_matrix(g.world(parent,float(t))[:3,:3]@np.linalg.inv(R0)).as_rotvec() for t in ts];axis=max(rots,key=np.linalg.norm);axis=axis/np.linalg.norm(axis) if np.linalg.norm(axis)>1e-8 else np.array([1.,0,0]);axis*=1 if axis[np.argmax(abs(axis))]>=0 else -1
  extent=math.radians(15 if kind.startswith('Front') else 25 if cla in [6,7] else 15 if cla==8 else 60 if cla==212 else 55 if cla==211 else 15)
  states=[state(),state(Rotation.from_rotvec(axis*extent).as_matrix())]
  if cla in [6,7,8]:states.append(state(Rotation.from_rotvec(-axis*extent).as_matrix()))
 if cla==99 and parent==3:static[name]=(m,pivot,i)
 # Keep original vertex/index buffers; two-sided rendering adds reverse faces, no decimation.
 reverse(m) if d['materials'][d['meshes'][n['mesh']]['primitives'][0].get('material',0)].get('doubleSided',False) else None
 node=add(packs,nodes,name,m,cla,states);nodes[-1]=dnm.edit(node,'POS ',' '.join(map(str,pivot))+' 0 0 0 1');metadata['components'].append({'name':name,'node':i,'parent':parent,'triangles':count,'class':cla,'pivot':pivot.tolist()})
# Own nozzle-matched plume, controlled separately from the original source geometry.
for side in ['0','1']:
 q=nozzle.profiles[side][-1];m=flame(q['cx'],q['cy'],q['z']+.008,q['radius']/.67*.94,q['radius']/.67*.94,2.1);add(packs,nodes,'Su30Plume_'+side,m,112+int(side),[state(show=0),state()])
# Subtle transparent dry exhaust, separate from afterburner flame.
for side in ['0','1']:
 q=nozzle.profiles[side][-1];m=Mesh();N=20
 for j in range(4):
  za=q['z']-.6*j;zb=q['z']-.6*(j+1);ra=q['radius']*(1+.14*j);rb=q['radius']*(1+.14*(j+1))
  for k in range(N):
   a=2*math.pi*k/N;b=2*math.pi*(k+1)/N
   m.face([(q['cx']+ra*math.cos(a),q['cy']+ra*math.sin(a),za),(q['cx']+ra*math.cos(b),q['cy']+ra*math.sin(b),za),(q['cx']+rb*math.cos(b),q['cy']+rb*math.sin(b),zb),(q['cx']+rb*math.cos(a),q['cy']+rb*math.sin(a),zb)],(130,139,148,18-4*j),True)
 add(packs,nodes,'Su30DryExhaust_'+side,m,114+int(side),[state(show=0),state()])
# Full source stage; gear construction mutates only the necessary underside skins later.
assert metadata['source_triangles']==418250
for name in ['su30sm.dnm','su30sm_coarse.dnm']:dnm.write(out/name,packs,nodes)
# Separate collision envelope does not replace or simplify visible source meshes.
hull=ConvexHull(cv(vv));used=np.unique(hull.simplices);remap={int(old):new for new,old in enumerate(used)};coll=Mesh();coll.v=[tuple(v) for v in cv(vv)[used]];coll.f=[([remap[int(i)] for i in q],(90,100,120),False) for q in hull.simplices];(out/'su30smcoll.srf').write_text('\n'.join(coll.srf())+'\n');(out/'su30smcockpit.srf').write_text('SURF\nE\n')
dnm.write(r/'source-stage.dnm',packs,nodes)
(r/'conversion.json').write_text(json.dumps(metadata,indent=2));np.savez_compressed(r/'source_geometry.npz',vertices=cv(vv));print('CONVERTED',metadata['source_triangles'],'triangles','bounds',metadata['bounds_m'],flush=True)
