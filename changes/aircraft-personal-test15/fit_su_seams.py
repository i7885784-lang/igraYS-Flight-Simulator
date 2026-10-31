from pathlib import Path
import sys,numpy as np,json
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
for kind in ['su27','su34']:
 p,ns=dnm.read(r/'runtime/aircraft'/f'{kind}.dnm');ns=[n for n in ns if dnm.name(n)!='RecoveredBayShoulderSkin'];p.pop('RecoveredBayShoulderSkin.srf',None)
 if kind=='su27':
  for n in ns:
   if not dnm.name(n).startswith('ConformalMainBayLiner'):continue
   old=dnm.mesh(p[dnm.fil(n)]);m=Mesh()
   for ids,c,b in old.f[::2]:
    q=np.array([old.v[i] for i in ids]);q[:2,1]-=.010;q[2:,1]+=.010;m.face(q,c);m.face(q[::-1],c)
   p[dnm.fil(n)]=m.srf()
 else:
  for n in ns:
   if not dnm.name(n).startswith('OriginalSideDoor') or not dnm.name(n).endswith('Wheel'):continue
   # Neutral cover was widened 82mm in test9; the hinge was not updated.
   # Anchor the same leaf to its actual outer edge. Closed skin stays exact.
   delta=np.array([.082*(1 if 'DoorL' in dnm.name(n) else -1),0,0]);ss=[s for s in n if s.startswith('STA ')]
   new=[state(R,t+(np.eye(3)-R)@delta) for R,t in [transform(n,i) for i in range(len(ss))]]
   i=n.index('NST '+str(len(ss)));j=next(i for i,s in enumerate(n) if s.startswith('POS '));n[i:j]=['NST '+str(len(new))]+new
 for name in [kind+'.dnm',kind+'_coarse.dnm']:dnm.write(r/'runtime/aircraft'/name,p,ns)
