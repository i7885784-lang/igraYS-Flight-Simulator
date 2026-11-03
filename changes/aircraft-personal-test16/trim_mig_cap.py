from pathlib import Path
import sys,numpy as np
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'runtime/aircraft/mig29.dnm')
for n in ns:
 if dnm.name(n).startswith('MainBayAftCap'):
  old=dnm.mesh(p[dnm.fil(n)]);m=Mesh()
  for ids,c,b in old.f:
   poly=[np.array(old.v[i]) for i in ids];out=[]
   for a,z in zip(poly,poly[1:]+poly[:1]):
    ia=a[1]>=.035;ib=z[1]>=.035
    if ia:out.append(a)
    if ia!=ib:out.append(a+(z-a)*((.035-a[1])/(z[1]-a[1])))
   if len(out)>=3:m.face(out,c,b)
  p[dnm.fil(n)]=m.srf()
for name in ['mig29.dnm','mig29_coarse.dnm']:dnm.write(r/'runtime/aircraft'/name,p,ns)
