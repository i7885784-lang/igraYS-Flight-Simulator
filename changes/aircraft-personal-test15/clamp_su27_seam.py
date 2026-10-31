from pathlib import Path
import sys,numpy as np
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
from ac_reference import AC
from envelope import Envelope
ac=AC(r/'upstream/su27/Su-27.ac');source=[{'v':(np.array(o['v'])+[0,0,10]).tolist(),'f':o['f']} for o in ac.objects if o['name'].startswith('HULL_Hull_Upper')];env=Envelope(source,step=.008)
p,ns=dnm.read(r/'runtime/aircraft/su27.dnm')
for n in ns:
 if not dnm.name(n).startswith('ConformalMainBayLiner'):continue
 m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v);lo,hi,d=env.bounds(v);v[:,1]=np.clip(v[:,1],lo+.001,hi-.001);m.v=[tuple(q) for q in v];p[dnm.fil(n)]=m.srf()
for name in ['su27.dnm','su27_coarse.dnm']:dnm.write(r/'runtime/aircraft'/name,p,ns)
