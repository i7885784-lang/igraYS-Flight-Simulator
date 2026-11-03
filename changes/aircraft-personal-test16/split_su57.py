from pathlib import Path
import sys,numpy as np
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'baseline/su57.dnm')
def clip(poly,mid,right):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ia=(a[0]>=mid) if right else (a[0]<=mid);ib=(b[0]>=mid) if right else (b[0]<=mid)
  if ia:out.append(a)
  if ia!=ib:
   t=(mid-a[0])/(b[0]-a[0]);out.append(tuple(np.array(a)+(np.array(b)-a)*t))
 return out
for title in ['Left','Right']:
 n=next(n for n in ns if dnm.name(n)=='Door_'+title);old=dnm.mesh(p[dnm.fil(n)]);pos=np.array(next(x[4:] for x in n if x.startswith('POS ')).split()[:3],float);v=np.array(old.v)+pos;lo,hi=v.min(0),v.max(0);mid=(lo[0]+hi[0])/2
 for right in [False,True]:
  hx=hi[0] if right else lo[0]; candidates=v[abs(v[:,0]-hx)<.00001]; hy=float(candidates[np.argmin(abs(candidates[:,2]-pos[2])),1]);hinge=np.array([hx,hy,pos[2]]);m=Mesh()
  for ids,c,b in old.f:
   poly=clip([tuple(v[i]) for i in ids],mid,right)
   if len(poly)>=3:m.face([np.array(a)-hinge for a in poly],c,b)
  name='Door_'+title+('_Inner' if (right==(title=='Left')) else '_Outer');nn=add(p,ns,name,m,dnm.cla(n),[state(),state(Rotation.from_euler('Z',70 if right else -70,degrees=True).as_matrix())]);ns[-1]=dnm.edit(nn,'POS ',' '.join(map(str,hinge))+' 0 0 0 1')
 ns.remove(n);del p[dnm.fil(n)]
for name in ['su57.dnm','su57_coarse.dnm']:dnm.write(r/'runtime/aircraft'/name,p,ns)
print('Four main door leaves generated; movement pending collision/native review.')
