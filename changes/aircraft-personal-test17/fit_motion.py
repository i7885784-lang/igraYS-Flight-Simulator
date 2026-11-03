from pathlib import Path
import sys,numpy as np,fcl,json,itertools
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
from collision import arrays,obj,interpolate
p,ns=dnm.read(r/'runtime/aircraft/mig29.dnm');lu={dnm.name(n):n for n in ns};side='L';node=lu['MainBayRearClosureL'];source=lu['Source_reargeardoor_L'];full=dnm.mesh(p[dnm.fil(node)]);proxy=Mesh()
for ids,c,b in full.f:
 q=np.array([full.v[i] for i in ids]);q=.99*q+.01*q.mean(0);proxy.face(q,c,b)
a=obj(*arrays(full));edge_proxy=obj(*arrays(proxy))
obs=[(obj(*arrays(dnm.mesh(p[dnm.fil(n)]))),n) for n in ns if dnm.name(n) in ['Hull','EngineL','MainBayOuterWalls','MainBayInnerLiner','MainBayCeiling','Source_fwdgeardoor_L','Source_reargeardoor_L'] or dnm.name(n).startswith(('Gear_','WheelHub','AxleFork','MainBayReturnStrip'))];req=fcl.CollisionRequest(num_max_contacts=1,enable_contact=True)
def pulse(g,lo,hi):return max(0.,min(1.,(g-lo)/.01,(hi-g)/.01))
groups=[(.01,.065),(.075,.13)];deltas=[np.zeros(3),np.zeros(3)];allgs=np.linspace(0,.15,61);cache={}
for g in allgs:
 cache[round(float(g),5)]=[(o,n,interpolate(n,float(g)) if dnm.cla(n)==210 else fcl.Transform()) for o,n in obs]
def first_hit(gs,ds):
 for g in gs:
  delta=sum((pulse(g,*b)*d for b,d in zip(groups,ds)),np.zeros(3));tf=interpolate(source,float(g));a.setTransform(fcl.Transform(tf.getRotation(),tf.getTranslation()+delta));edge_proxy.setTransform(fcl.Transform(tf.getRotation(),tf.getTranslation()+delta))
  for o,n,t in cache[round(float(g),5)]:
   o.setTransform(t)
   if fcl.collide(edge_proxy if dnm.name(n)=='Source_reargeardoor_L' else a,o,req,fcl.CollisionResult()):return float(g),dnm.name(n)
 return None
raw=[]
for x,y,z in itertools.product(range(-6,7),repeat=3):
 if x==y==z==0:continue
 raw.append((x*x+y*y+z*z,np.array([x,y,z],float)*.01))
raw.sort(key=lambda t:t[0])
for gi,interval in enumerate(groups):
 gs=[float(g) for g in allgs if interval[0]<g<interval[1]];hit=first_hit(gs,deltas)
 print('group',gi,'initial',hit,flush=True)
 if hit:
  found=False
  for j,(cost,d) in enumerate(raw):
   ds=deltas.copy();ds[gi]=d
   if first_hit(gs,ds) is None:deltas=ds;found=True;print('fit',gi,d.tolist(),'candidate',j,flush=True);break
  if not found:raise RuntimeError('No feasible clearance within grid')
assert first_hit(allgs,deltas) is None
for sg,side in [(1,'L'),(-1,'R')]:
 n=lu['MainBayRearClosure'+side];src=lu['Source_reargeardoor_'+side];idx=[i for i,s in enumerate(n) if s.startswith('STA ')];ss=[s for s in src if s.startswith('STA ')]
 for k,i in enumerate(idx):
  g=k/100;delta=sum((pulse(g,*b)*d for b,d in zip(groups,deltas)),np.zeros(3));delta[0]*=sg;a=ss[k].split();a[1:4]=[str(float(v)+q) for v,q in zip(a[1:4],delta)];n[i]=' '.join(a)
for name in ['mig29.dnm','mig29_coarse.dnm']:dnm.write(r/'runtime/aircraft'/name,p,ns)
(r/'clearance-fit.json').write_text(json.dumps({'groups':groups,'deltas':[d.tolist() for d in deltas]},indent=2));print('DONE',flush=True)
