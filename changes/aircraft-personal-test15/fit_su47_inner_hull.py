from pathlib import Path
import sys,numpy as np
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
from gear_v3 import clip
p,ns=dnm.read(r/'runtime/aircraft/su47.dnm');n=next(n for n in ns if dnm.name(n)=='OpaqueInternalHull');old=dnm.mesh(p[dnm.fil(n)]);m=Mesh()
# The coarse hidden collision-LOD shell crossed the intake cutout. Keep it
# elsewhere; the recessed source-bounded liner handles this span instead.
for ids,c,b in old.f:
 q=[old.v[i] for i in ids]
 for axis,z,sg in [(2,.05,False),(2,4.05,True)]:
  part=clip(q,axis,z,sg)
  if len(part)>2:m.face(part,c,b)
p[dnm.fil(n)]=m.srf()
for name in ['su47.dnm','su47_coarse.dnm']:dnm.write(r/'runtime/aircraft'/name,p,ns)
