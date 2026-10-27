"""Split rigidly weighted YFT geometry; refuse mixed bone triangles."""
import numpy as np
from read_yft import YFT
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

def read_parts(path):
 r=YFT(path).parse();parts={}
 for mesh in r.meshes:
  if mesh['skin']:
   weights=mesh['weights'];assert np.all(np.sort(weights,axis=1)==[0,0,0,255])
   channels=mesh['indices'][np.arange(len(weights)),weights.argmax(1)]
   bone=np.asarray(mesh['palette'])[channels];fb=bone[mesh['faces']];assert not np.ptp(fb,axis=1).any()
   facebones=fb[:,0]
  else:facebones=np.full(len(mesh['faces']),mesh['bone'])
  for b in np.unique(facebones):
   for ids in mesh['faces'][facebones==b]:
    q=mesh['positions'][ids];n=mesh['normals'][ids].mean(0) if mesh['normals'] is not None else None
    if n is not None and np.dot(np.cross(q[1]-q[0],q[2]-q[0]),n)<0:q=q[::-1]
    if np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))<1e-9:continue
    parts.setdefault(int(b),[]).append((q,mesh['geometry'],mesh['shader']))
 return r,parts

def components(faces):
 lengths=[len(f[0]) for f in faces];q=np.concatenate([f[0] for f in faces]);_,ids=np.unique(np.round(q,4),axis=0,return_inverse=True);nv=int(ids.max()+1)
 offsets=np.cumsum([0]+lengths);rows=[];cols=[];first=[]
 for a,b in zip(offsets,offsets[1:]):
  v=ids[a:b];rows.extend(v);cols.extend(np.roll(v,-1));first.append(v[0])
 count,labels=connected_components(coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(nv,nv)),directed=False)
 flabel=labels[first]
 return [[faces[i] for i in np.where(flabel==k)[0]] for k in range(count)]
