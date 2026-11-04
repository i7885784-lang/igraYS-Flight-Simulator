from pathlib import Path
from common import *
r=Path('/workspace/ysflight-dev/su30sm-test-7');p,ns=dnm.read('/workspace/ysflight-dev/su30sm-test-4/source-stage.dnm');n=next(n for n in ns if dnm.name(n)=='Fuselage_0_4');m=dnm.mesh(p[dnm.fil(n)]);pos=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);v=np.array(m.v)+pos;out=Mesh()
def clip(poly,axis,value,positive):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  da=(a[axis]-value)*(1 if positive else -1);db=(b[axis]-value)*(1 if positive else -1)
  if da>=0:out.append(a)
  if (da>=0)!=(db>=0):out.append(a+(b-a)*da/(da-db))
 return out
for ids,c,b in m.f:
 q=v[ids]
 if q[:,1].mean()<.025:continue
 for sg in [-1,1]:
  poly=list(q)
  for axis,t,positive in [(0,1.03 if sg>0 else -2.4,True),(0,2.4 if sg>0 else -1.03,False),(2,-3.38,True),(2,-.41,False)]:
   if len(poly)<3:break
   poly=clip(poly,axis,t,positive)
  if len(poly)<3:continue
  x,y,z=np.array(poly).mean(0);signal=math.sin(z*.86+x*.56)+.58*math.sin(x*1.7-z*.30)+.27*math.cos(z*1.9);c=(77,139,163) if signal<-.48 else (118,166,185) if signal<.72 else (147,163,172);out.face(poly,c)
(r/'baseline/upper-wing-repair.srf').write_text('\n'.join(out.srf())+'\n');print(len(out.f))
