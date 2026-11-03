from pathlib import Path
import struct,json,numpy as np
from scipy.spatial.transform import Rotation,Slerp
class GLB:
 def __init__(self,path):
  self.raw=Path(path).read_bytes();assert self.raw[:4]==b'glTF';n=struct.unpack_from('<I',self.raw,12)[0];self.d=json.loads(self.raw[20:20+n]);self.bin=self.raw[28+n:];self.parents={c:i for i,v in enumerate(self.d['nodes']) for c in v.get('children',[])};self.tracks={};self.cache={}
  for a in self.d.get('animations',[]):
   for c in a['channels']:
    s=a['samplers'][c['sampler']];self.tracks[c['target']['node'],c['target']['path']]=(self.acc(s['input']).ravel(),self.acc(s['output']),s.get('interpolation','LINEAR'))
 def acc(self,i):
  if i in self.cache:return self.cache[i]
  a=self.d['accessors'][i];v=self.d['bufferViews'][a['bufferView']];dt=np.dtype({5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1',5122:'<i2'}[a['componentType']]);n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];q=np.ndarray((a['count'],n),dtype=dt,buffer=self.bin,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*n),dt.itemsize)).copy();self.cache[i]=q;return q
 def value(self,i,key,t):
  default={'translation':[0,0,0],'rotation':[0,0,0,1],'scale':[1,1,1]}[key];v=self.d['nodes'][i].get(key,default)
  if t is None or (i,key) not in self.tracks:return np.array(v,float)
  ts,vs,mode=self.tracks[i,key];t=np.clip(t,ts[0],ts[-1]);idx=min(np.searchsorted(ts,t,side='right')-1,len(ts)-2);idx=max(idx,0);f=(t-ts[idx])/(ts[idx+1]-ts[idx]) if ts[idx+1]>ts[idx] else 0
  if mode=='STEP':return vs[idx].astype(float)
  assert mode=='LINEAR',mode
  if key=='rotation':return Slerp([0,1],Rotation.from_quat(vs[idx:idx+2]))([f]).as_quat()[0]
  return (1-f)*vs[idx]+f*vs[idx+1]
 def world(self,i,t=None):
  n=self.d['nodes'][i];M=np.eye(4)
  if 'matrix' in n:M=np.array(n['matrix']).reshape(4,4).T
  else:M[:3,:3]=Rotation.from_quat(self.value(i,'rotation',t)).as_matrix()@np.diag(self.value(i,'scale',t));M[:3,3]=self.value(i,'translation',t)
  return self.world(self.parents[i],t)@M if i in self.parents else M
 def mesh(self,i,t=None):
  n=self.d['nodes'][i];M=self.world(i,t);out=[]
  for p in self.d['meshes'][n['mesh']]['primitives']:
   assert p.get('mode',4)==4;v=self.acc(p['attributes']['POSITION']);v=v@M[:3,:3].T+M[:3,3];ids=self.acc(p['indices']).reshape(-1,3).astype(int);out.append((v,ids,p.get('material',0),p))
  return out
