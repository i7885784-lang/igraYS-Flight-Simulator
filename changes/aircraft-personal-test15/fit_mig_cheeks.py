from pathlib import Path
import sys,numpy as np
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
from envelope import Envelope
p,ns=dnm.read(r/'runtime/aircraft/mig29.dnm');lu={dnm.name(n):n for n in ns};h=dnm.mesh(p[dnm.fil(lu['Hull'])]);env=Envelope([{'v':h.v,'f':[i for i,c,b in h.f]}],step=.008)
m=dnm.mesh(p[dnm.fil(lu['MainBayOuterWalls'])]);v=np.array(m.v)
# The old upper rim stopped at .19-.23m, below the wing underside. Lift
# only its recessed upper row, following the existing airframe roof.
for i,q in enumerate(v):
 if abs(q[0])>1.73 and q[2]<-.24 or q[1]>.185:
  v[i,1]=env.bounds([q])[1][0]-.012
m.v=[tuple(q) for q in v];p[dnm.fil(lu['MainBayOuterWalls'])]=m.srf()
# Visible end bulkheads were extended past the actual aperture. Keep their
# lower row inside the existing nacelle, retaining the internal well itself.
n=lu['MainBayInnerLiner'];m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v);v[:,2]=np.clip(v[:,2],-2.37,.04)
# Fore and aft ends rise to meet the original lower edge instead of a flat
# -.24m board projecting below the sloped outside skin.
lo,hi,d=env.bounds(v);v[:,1]=np.minimum(np.maximum(v[:,1],lo+.025),hi-.025);m.v=[tuple(q) for q in v];m.f=[(ids,c,b) for ids,c,b in m.f if not np.all(abs(np.array([m.v[i][2] for i in ids])-.04)<1e-5)];p[dnm.fil(n)]=m.srf()
for name in ['mig29.dnm','mig29_coarse.dnm']:dnm.write(r/'runtime/aircraft'/name,p,ns)
