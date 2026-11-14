"""Return the aft bay skin to its original large outer-door assembly.
Only two fixed skins, the paired outer doors and matching F4 remnants may change.
Every original DNM node/state, the small inner shutters and all mechanisms stay exact.
"""
from pathlib import Path
import sys,json,argparse,hashlib
import numpy as np,trimesh,manifold3d as mf
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin'))
sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin/model-source'))
from fit_field import dnm,world,exterior,Projected
from mesh import Mesh
from cut import cut
BASE='ee1f9324e1c4a46179efd2af2323e5cd0b599e19221e1d8e04910e3332071f27'
SHA=lambda b:hashlib.sha256(b).hexdigest()
FACE_COLORS=[]

def to_tm(m,R=np.eye(3),T=np.zeros(3)):
 faces=[];colors=[]
 for ids,c,b in m.f:
  assert len(c)==3 and not b
  for j in range(1,len(ids)-1):faces.append([ids[0],ids[j],ids[j+1]]);colors.append(c)
 tm=trimesh.Trimesh(np.array(m.v)@R.T+T,np.array(faces),face_colors=np.c_[colors,np.full(len(colors),255)],process=True)
 assert tm.is_watertight and tm.is_winding_consistent
 tm.fix_normals();return tm

def manifold(tm):
 # Discontinuous per-face RGB properties retain the original camouflage borders.
 ix=tm.faces.ravel();props=np.c_[tm.vertices[ix],np.repeat(tm.visual.face_colors[:,:3],3,axis=0)].astype(np.float64)
 unique,first=np.unique(ix,return_index=True);lookup=dict(zip(unique,first));first_for=np.array([lookup[i] for i in ix]);src=np.flatnonzero(first_for!=np.arange(len(ix)))
 face_ids=[]
 for c in tm.visual.face_colors:
  col=tuple(map(int,c[:3]))
  if col not in FACE_COLORS:FACE_COLORS.append(col)
  face_ids.append(FACE_COLORS.index(col))
 mesh=mf.Mesh64(face_id=np.array(face_ids,dtype=np.uint64),vert_properties=np.ascontiguousarray(props),tri_verts=np.arange(len(ix),dtype=np.uint64).reshape(-1,3),merge_from_vert=src.astype(np.uint64),merge_to_vert=first_for[src].astype(np.uint64))
 result=mf.Manifold(mesh);assert result.status()==mf.Error.NoError,result.status();assert not result.is_empty();return result

def from_manifold(solid,R=np.eye(3),T=np.zeros(3)):
 assert solid.status()==mf.Error.NoError and not solid.is_empty(),solid.status()
 solid=solid.simplify(2e-6)
 data=solid.to_mesh64();props=np.array(data.vert_properties);ix=np.array(data.tri_verts,dtype=int);rgb=props[ix,3:6];error=float(np.max(abs(rgb-rgb[:,0,None,:])))
 # The boolean preserves ancestor face IDs. Use their exact source RGB rather
 # than interpolated corner properties after the micrometre simplification.
 colors=np.array([FACE_COLORS[i] for i in data.face_id],dtype=int)
 parent=np.arange(len(props))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for a,b in zip(data.merge_from_vert,data.merge_to_vert):parent[root(int(a))]=root(int(b))
 ids=np.array([root(i) for i in range(len(props))]);used,inv=np.unique(ids,return_inverse=True)
 tm=trimesh.Trimesh(props[used,:3],inv[ix],face_colors=np.c_[colors,np.full(len(colors),255)],process=False);tm.remove_unreferenced_vertices()
 assert tm.is_watertight and tm.is_winding_consistent and tm.body_count==1,(tm.is_watertight,tm.body_count)
 # Collapse boolean slivers at 2 micrometres before decimal serialization.
 # Check the resulting closed topology; deleting triangles alone would make holes.
 local=np.round((tm.vertices-T)@R,10);faces=tm.faces.copy();parents=np.arange(len(local));alive=np.ones(len(faces),bool)
 incident=[set() for _ in local]
 for i,ids in enumerate(faces):
  for v in ids:incident[v].add(i)
 def leader(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 # Collapse only existing edges satisfying the closed-manifold link condition.
 # A spatial weld can merge unrelated close layers at the original corner cap.
 edges=np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1),axis=0)
 lengths=np.linalg.norm(local[edges[:,0]]-local[edges[:,1]],axis=1);candidates=edges[np.flatnonzero(lengths<=2e-6)[np.argsort(lengths[lengths<=2e-6])]]
 for aa,bb in candidates:
  a,b=leader(aa),leader(bb)
  if a==b or np.linalg.norm(local[a]-local[b])>2e-6:continue
  shared=incident[a]&incident[b]
  if len(shared)!=2:continue
  na=set(faces[list(incident[a])].ravel())-{a};nb=set(faces[list(incident[b])].ravel())-{b};opposite=set(faces[list(shared)].ravel())-{a,b}
  if na&nb!=opposite:continue
  keep,drop=a,b;affected=incident[a]|incident[b];remaining=sorted(affected-shared)
  old=faces[remaining];cross=np.cross(local[old[:,1]]-local[old[:,0]],local[old[:,2]]-local[old[:,0]])
  valid=False
  for keep,drop in [(a,b),(b,a)]:
   new=old.copy();new[new==drop]=keep;nn=np.cross(local[new[:,1]]-local[new[:,0]],local[new[:,2]]-local[new[:,0]])
   nontrivial=np.linalg.norm(cross,axis=1)>2e-14
   if np.all(np.einsum('ij,ij->i',cross,nn)[nontrivial]>0):valid=True;break
  if not valid:continue
  parents[drop]=keep
  for fi in list(affected):
   for v in faces[fi]:incident[v].discard(fi)
   if fi in shared:alive[fi]=False;continue
   faces[fi][faces[fi]==drop]=keep
   for v in faces[fi]:incident[v].add(fi)
 labels=np.array([leader(i) for i in range(len(local))]);used,inv=np.unique(labels,return_inverse=True);ff=inv[faces[alive]]
 displacement=float(np.linalg.norm(local-local[labels],axis=1).max());assert displacement<4e-6
 clean=trimesh.Trimesh(local[used],ff,face_colors=tm.visual.face_colors[alive],process=False);clean.remove_unreferenced_vertices()
 assert clean.is_watertight and clean.is_winding_consistent and clean.body_count==1
 assert clean.area_faces.min()>1e-14
 m=Mesh();m.v=list(map(tuple,clean.vertices));m.f=[(list(map(int,t)),tuple(map(int,c[:3])),False) for t,c in zip(clean.faces,clean.visual.face_colors)]
 return m,dict(vertices=len(m.v),triangles=len(m.f),watertight=True,components=1,source_face_colors_exact=True,simplification_tolerance_m=2e-6,sliver_vertex_displacement_m=displacement,collapsed_triangles=int(np.sum(~alive)))

def serialize(m):
 lines=m.srf();normals=[];vertices=np.array(m.v)
 for ids,col,bright in m.f:
  q=vertices[ids];n=np.cross(q[1]-q[0],q[2]-q[0]);n/=np.linalg.norm(n);normals.append('N %.9f %.9f %.9f'%tuple(n))
 it=iter(normals);return [next(it) if line.startswith('N ') else line for line in lines]

def box(sg,x0,x1,z0,z1):
 a,b=sorted([sg*x0,sg*x1]);m=Mesh();m.box((a+b)/2,-.7,(z0+z1)/2,b-a,3.6,z1-z0,(105,118,123));return manifold(to_tm(m))

def bridge(p,lu,side,sg,skin_ref,door_ref):
 name='GearDoor_Left_Inner' if side=='Left' else 'GearDoor_Right_Outer'
 # The original stationary aft corner cap reaches Z=-3.325 at absX=1.87.
 # End the connecting bridge 2 mm ahead of it; the inherited leaf remains curved.
 us=np.linspace(0,1,13);zs=np.linspace(-3.323,-1.892,74)
 import shapely
 from shapely.geometry import LineString
 domain=shapely.union_all(door_ref.polys)
 pts=[]
 for z in zs:
  edge=domain.intersection(LineString([(1.7,z),(2.5,z)])).bounds[0]+.00005;end=edge+.025
  for t in us:
   u=1.84+(end-1.84)*t
   a=skin_ref.lower([min(u,1.87),z],nearest=True);b=door_ref.lower([max(u,edge),z],nearest=True);w=np.clip((u-1.845)/(edge+.020-1.845),0,1);w=w*w*(3-2*w);pts.append((sg*u,(1-w)*a+w*b,z))
 pts=np.array(pts);f=[];c=[];nu=len(us)
 painted=[*exterior(p['MainBayFixedSkin_'+side+'.srf'],lu['MainBayFixedSkin_'+side]),*exterior(p[dnm.fil(lu[name])],lu[name])]
 from shapely.geometry import Polygon,Point
 from shapely.strtree import STRtree
 polys=[Polygon(np.c_[sg*q[:,0],q[:,2]]) for q,col in painted];tree=STRtree(polys)
 for j in range(len(zs)-1):
  for i in range(nu-1):
   a=j*nu+i;b=a+1;d=a+nu;cc=d+1
   for ids in [[a,b,cc],[a,cc,d]]:
    q=pts[ids]
    if np.cross(q[1]-q[0],q[2]-q[0])[1]>0:ids=ids[::-1]
    uv=np.c_[sg*q[:,0],q[:,2]].mean(0);hit=tree.query(Point(*uv),predicate='intersects');col=painted[int(hit[0] if len(hit) else tree.nearest(Point(*uv)))][1];f.append(ids);c.append(col)
 m=Mesh();m.v=list(map(tuple,pts))+list(map(tuple,pts+[0,.008,0]));n=len(pts);edges={}
 from collections import Counter
 counts=Counter(tuple(sorted((a,b))) for ids in f for a,b in zip(ids,ids[1:]+ids[:1]))
 for ids,col in zip(f,c):
  m.f.append((ids,col,False));m.f.append(([i+n for i in ids[::-1]],(148,153,148),False))
  for a,b in zip(ids,ids[1:]+ids[:1]):
   if counts[tuple(sorted((a,b)))]==1:m.f.append(([b,a,a+n,b+n],(105,118,123),False))
 return manifold(to_tm(m))

def roofs(p,lu,side):
 n=lu['GearWell_'+side];m=dnm.mesh(p[dnm.fil(n)]);R,T=world(n);v=np.array(m.v)@R.T+T;result=[]
 for ids,c,b in m.f:
  for j in range(1,len(ids)-1):
   q=v[[ids[0],ids[j],ids[j+1]]];normal=np.cross(q[1]-q[0],q[2]-q[0]);ln=np.linalg.norm(normal)
   if ln>1e-12 and abs(normal[1])>.6*ln and q[:,1].min()>0:result.append(q)
 assert result;return np.array(result)

def run(base,out):
 assert SHA(base.read_bytes())==BASE;p,ns=dnm.read(base);old={k:list(v) for k,v in p.items()};lu={dnm.name(n):n for n in ns};audit={'baseline_sha256':BASE,'panels':{}}
 for side,sg in [('Left',-1),('Right',1)]:
  fixed='MainBayFixedSkin_'+side;door='GearDoor_Left_Inner' if side=='Left' else 'GearDoor_Right_Outer';fn=dnm.fil(lu[fixed]);dn=dnm.fil(lu[door]);R,T=world(lu[fixed]);A,B=world(lu[door]);oldskin=manifold(to_tm(dnm.mesh(p[fn]),R,T));oldDoor=manifold(to_tm(dnm.mesh(p[dn]),A,B))
  ref=Projected(np.array([q for q,c in exterior(p[fn],lu[fixed])]),sg);dref=Projected(np.array([q for q,c in exterior(p[dn],lu[door])]),sg)
  aperture=box(sg,1.055,1.872,-3.35,-1.89);leaf=oldskin^box(sg,1.057,1.870,-3.348,-1.892);join=bridge(p,lu,side,sg,ref,dref)
  retained=oldskin-aperture;combined=oldDoor+leaf+join
  fm,fa=from_manifold(retained,R,T);dm,da=from_manifold(combined,A,B);p[fn]=serialize(fm);p[dn]=serialize(dm);audit['panels'][side]={'fixed':fa,'outer_door':da,'original_door_volume_m3':oldDoor.volume(),'extension_volume_m3':leaf.volume(),'combined_volume_m3':combined.volume()}
  print(side,'retained',len(fm.f),'connected door',len(dm.f),flush=True)
 audit['internal_body_cut']=cut(p,lu,{s:roofs(p,lu,s) for s in ['Left','Right']},dnm,world)
 expected={'MainBayFixedSkin_Left.srf','MainBayFixedSkin_Right.srf','GearDoor_Left_Inner.srf','GearDoor_Right_Outer.srf','Fuselage_0_4.srf'};assert set(k for k in p if p[k]!=old[k])==expected
 out.parent.mkdir(exist_ok=True,parents=True);dnm.write(out,p,ns);out.write_bytes(out.read_bytes().replace(b'\r\n',b'\n'));audit.update(model_sha256=SHA(out.read_bytes()),changed_packs=sorted(expected),all_original_node_records_exact=True,all_existing_axes_and_animation_states_exact=True);out.with_suffix('.audit.json').write_text(json.dumps(audit,indent=2));print(audit['model_sha256'])
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--baseline',type=Path,required=True);a.add_argument('--output',type=Path,required=True);v=a.parse_args();run(v.baseline,v.output)
