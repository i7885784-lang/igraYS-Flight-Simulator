from pathlib import Path
import sys,math,numpy as np,json,hashlib,pickle
import fcl
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'model-source'));from common import dnm,Rotation,transform
from collision import arrays,obj,interpolate
class Model:
 def __init__(self,path=None):
  self.path=Path(path or r/'runtime/aircraft/su30sm.dnm');p,self.ns=dnm.read(self.path);self.lu={dnm.name(n):n for n in self.ns};self.parents={s[4:].strip('"'):dnm.name(n) for n in self.ns for s in n if s.startswith('CLD ')};self.meshes={};self.boxes={};self.objects={};self.poses={};self.cache=r/'geometry-cache';self.cache.mkdir(exist_ok=True)
  for name,n in self.lu.items():
   if dnm.cla(n) in [112,113]:continue
   lines=p[dnm.fil(n)];h=hashlib.sha256('\n'.join(lines).encode()).hexdigest();fn=self.cache/(h+'.pickle')
   if fn.exists():
    with fn.open('rb') as f:v,faces=pickle.load(f)
   else:
    m=dnm.mesh(lines)
    if not m.f or not m.v:continue
    v,faces=arrays(m)
    with fn.open('wb') as f:pickle.dump((v,faces),f,protocol=5)
   if len(faces)==0:continue
   self.meshes[name]=(v,faces);self.boxes[name]=(v.min(0),v.max(0));self.objects[name]=obj(v,faces)
  self.sample(0)
 def local(self,n,g):
  pos=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float)
  if dnm.cla(n)==210:
   t=interpolate(n,float(g));R=t.getRotation();v=t.getTranslation()
  else:R,v=transform(n,0)
  return R,pos+v
 def sample(self,g):
  self.g=float(g);self.poses={};self.worldboxes={}
  def world(name):
   if name in self.poses:return self.poses[name]
   R,t=self.local(self.lu[name],g)
   if name in self.parents:
    A,b=world(self.parents[name]);R,t=A@R,A@t+b
   self.poses[name]=(R,t);return R,t
  for name in self.lu:world(name)
  for name,o in self.objects.items():
   R,t=self.poses[name];o.setTransform(fcl.Transform(R,t));lo,hi=self.boxes[name];mid=(lo+hi)/2;half=(hi-lo)/2;c=R@mid+t;h=abs(R)@half;self.worldboxes[name]=(c-h,c+h)
 def collide(self,a,b):
  aa,ab=self.worldboxes[a];ba,bb=self.worldboxes[b]
  if np.any(aa>bb+.00001) or np.any(ba>ab+.00001):return None
  res=fcl.CollisionResult()
  if fcl.collide(self.objects[a],self.objects[b],fcl.CollisionRequest(num_max_contacts=1,enable_contact=True),res):return np.array(res.contacts[0].pos)
  return None
