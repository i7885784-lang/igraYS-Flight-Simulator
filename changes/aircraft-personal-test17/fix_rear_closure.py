"""Close the missing aft gear-well skin with paired guided door extensions.
Own game-model adaptation. Original airframe and source door meshes retained.
"""
from pathlib import Path
import sys,json,numpy as np
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'baseline/mig29.dnm');fit=json.loads((r/'clearance-fit.json').read_text())
def pulse(g,lo,hi):return max(0.,min(1.,(g-lo)/.01,(hi-g)/.01))
for sg,side in [(1,'L'),(-1,'R')]:
 n=next(n for n in ns if dnm.name(n)=='Source_reargeardoor_'+side);d=dnm.mesh(p[dnm.fil(n)]);edges=[]
 for ids,c,b in d.f:
  q=np.array([d.v[i] for i in ids]);edges.extend(zip(q,np.roll(q,-1,axis=0)))
 en=next(n for n in ns if dnm.name(n)==('EngineL' if sg>0 else 'EngineR'));engine=dnm.mesh(p[dnm.fil(en)]);ee=[]
 for ids,c,b in engine.f:
  qq=np.array([engine.v[i] for i in ids]);ee.extend(zip(qq,np.roll(qq,-1,axis=0)))
 rows=[]
 for z in np.linspace(-2.30,-1.56,60):
  hits=[]
  for a,b in edges:
   if abs(a[2]-b[2])<1e-9:continue
   t=(z-a[2])/(b[2]-a[2])
   if 0<=t<=1:hits.append(a+(b-a)*t)
  if hits:
   q=min(hits,key=lambda x:x[1]);eh=[]
   for a,b in ee:
    if abs(a[2]-b[2])<1e-9:continue
    t=(z-a[2])/(b[2]-a[2])
    if 0<=t<=1:eh.append(a+(b-a)*t)
   if eh:
    inner=max(eh,key=lambda x:sg*x[0]);inner[0]+=sg*.0005;rows.append((inner,q))
 m=Mesh()
 for a,b in zip(rows[:-1],rows[1:]):m.face([a[0],a[1],b[1],b[0]],(111,133,132));m.face([b[0],b[1],a[1],a[0]],(111,133,132))
 new=n.copy();name='MainBayRearClosure'+side;fn=name+'.srf';p[fn]=m.srf();new[0]='SRF '+chr(34)+name+chr(34);new=dnm.edit(new,'FIL ',fn);indices=[i for i,s in enumerate(new) if s.startswith('STA ')]
 for k,i in enumerate(indices):
  a=new[i].split();delta=sum((pulse(k/100,*b)*np.array(d) for b,d in zip(fit['groups'],fit['deltas'])),np.zeros(3));delta[0]*=sg;a[1:4]=[str(float(v)+q) for v,q in zip(a[1:4],delta)];new[i]=' '.join(a)
 ns.append(new)
for name in ['mig29.dnm','mig29_coarse.dnm']:dnm.write(r/'runtime/aircraft'/name,p,ns)
