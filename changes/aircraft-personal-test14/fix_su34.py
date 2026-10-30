from pathlib import Path
import sys,numpy as np
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'))
from common import *
from envelope import Envelope
p,ns=dnm.read(r/'baseline/su34.dnm');orig=dnm.mesh((r/'baseline/uncut-su34.srf').read_text().splitlines());env=Envelope([{'v':orig.v,'f':[ids for ids,c,b in orig.f]}],step=.008)
for side,sg in [('L',1),('R',-1)]:
 wall=Mesh();z=np.linspace(-4.05,-1.47,130);q=np.c_[np.full(len(z),sg*1.52),np.zeros(len(z)),z];lo,hi,dist=env.bounds(q);lo=np.full_like(lo,-.42);hi-=.006
 for i in range(len(z)-1):
  if min(hi[i]-lo[i],hi[i+1]-lo[i+1])<.01:continue
  v=[(q[i,0],lo[i],z[i]),(q[i+1,0],lo[i+1],z[i+1]),(q[i+1,0],hi[i+1],z[i+1]),(q[i,0],hi[i],z[i])];wall.face(v,(103,140,159));wall.face(v[::-1],(103,140,159))
 add(p,ns,'Su34RearBayInnerWall'+side,wall)
(r/'runtime/aircraft').mkdir(parents=True,exist_ok=True)
for n in ['su34.dnm','su34_coarse.dnm']:dnm.write(r/'runtime/aircraft'/n,p,ns)
print('Rear well partitions inside original nacelle bounds')
