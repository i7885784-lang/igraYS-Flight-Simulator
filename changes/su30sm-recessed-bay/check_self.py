from pathlib import Path
import sys,json,numpy as np,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin'));sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin/validation'))
from fit_field import dnm,world
sha=lambda b:hashlib.sha256(b).hexdigest()
NAMES=['MainBayFixedSkin_Left','MainBayFixedSkin_Right','GearDoor_Left_Inner','GearDoor_Right_Outer']
from triangles import classify
import trimesh
model_path=Path(sys.argv[1] if len(sys.argv)>1 else 'work/candidate/runtime/aircraft/su30sm.dnm');p,ns=dnm.read(model_path);lu={dnm.name(n):n for n in ns};result={'model_sha256':sha(model_path.read_bytes()),'tolerance_m':2e-6,'shared_vertex_pairs_excluded':True,'vertex_positions':'actual serialized positions, no coordinate welding or rounding','separating_plane_tolerance_m':1e-8,'panels':{}}
for name in NAMES:
 n=lu[name];m=dnm.mesh(p[dnm.fil(n)]);R,t=world(n);v=np.array(m.v)@R.T+t;uv=v;ix=np.arange(len(v));tri=[];source_faces=[]
 for fi,(ids,c,b) in enumerate(m.f):
  for j in range(1,len(ids)-1):
   ids2=ix[[ids[0],ids[j],ids[j+1]]]
   if len(set(ids2))<3:continue
   q=uv[ids2]
   if np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))<1e-12:continue
   tri.append(ids2);source_faces.append(fi)
 tri=np.array(tri);q=uv[tri];cross=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);normals=cross/np.linalg.norm(cross,axis=1)[:,None];tree=trimesh.Trimesh(vertices=uv,faces=tri,process=False).triangles_tree;boxes=np.c_[q.min(1),q.max(1)];hits=[];tested=0
 for i in range(len(tri)):
  js=np.array([j for j in tree.intersection(boxes[i]) if j>i],int)
  if not len(js):continue
  shared=(tri[js,:,None]==tri[i][None,None,:]).any(axis=(1,2));js=js[~shared]
  if not len(js):continue
  dd=np.einsum('jki,i->jk',q[js]-q[i,0],normals[i]);sep=(dd.min(1)>1e-8)|(dd.max(1)<-1e-8);js=js[~sep]
  if not len(js):continue
  ee=np.einsum('jki,ji->jk',q[i][None,:,:]-q[js,0,None,:],normals[js]);sep=(ee.min(1)>1e-8)|(ee.max(1)<-1e-8);js=js[~sep]
  for j in js:
   tested+=1;kind=classify(q[i],q[j],tol=2e-6)
   if kind in ['cross','coplanar_overlap']:hits.append({'a_face':source_faces[i],'b_face':source_faces[j],'kind':kind,'a':q[i].tolist(),'b':q[j].tolist()})
  if i%5000==0:print(name,i,'hits',len(hits),flush=True)
 result['panels'][name]={'triangles':len(tri),'narrow_phase_pairs':tested,'hits':hits};print(name,'FINAL',len(hits),flush=True)
Path(sys.argv[2] if len(sys.argv)>2 else 'work/self-intersections.json').write_text(json.dumps(result,indent=2))
