"""Rebase remote control pivots locally; keep the rest of each model unchanged."""
from pathlib import Path
import sys,numpy as np,json
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'))
from common import *
rows=[]
for kind in ['su27','mig29','su34']:
 p,ns=dnm.read(r/'baseline'/f'{kind}.dnm')
 for n in ns:
  cl=dnm.cla(n)
  if cl not in (list(range(240,252)) if kind=='su34' else list(range(220,230))+[211,212]):continue
  m=dnm.mesh(p[dnm.fil(n)]);vv=np.array(m.v);ss=[s for s in n if s.startswith('STA ')];ki=40 if len(ss)==41 else 1
  Rs=[transform(n,i) for i in ([0,40] if len(ss)==41 else [1,2])];A=np.vstack([np.eye(3)-R for R,t in Rs]);b=np.concatenate([t for R,t in Rs]);pivot=np.linalg.lstsq(A,b,rcond=None)[0]
  axis=Rotation.from_matrix(Rs[-1][0]).as_rotvec();axis/=np.linalg.norm(axis);pivot+=axis*(vv.mean(0)-pivot).dot(axis)
  custom=kind=='su34' and cl in [242,243,244,245]
  if custom:
   side=1 if cl in [242,244] else -1;sg=vv[:,0]*side;lo,hi=sg.min(),sg.max();ends=[]
   for is_outer in [False,True]:
    q=vv[sg>hi-.06] if is_outer else vv[sg<lo+.06]
    # Flap hinge is its front edge. Slat hinge is its rear edge.
    z=(q[:,2].max()-.04) if cl in [242,243] else (q[:,2].min()+.035)
    edge=q[np.abs(q[:,2]-z)<.09]
    ends.append(np.array([q[:,0].mean(),edge[:,1].mean(),z]))
   a,b=ends;pivot=(a+b)/2;axis=b-a
   if axis[0]<0:axis=-axis
   axis/=np.linalg.norm(axis);degrees=-25 if cl in [242,243] else 22
   newstates=[state(Rotation.from_rotvec(axis*np.deg2rad(degrees*q)).as_matrix()) for q in np.linspace(-1,1,41)]
  else:newstates=[state(transform(n,i)[0]) for i in range(len(ss))]
  m.v=[tuple(q-pivot) for q in vv];p[dnm.fil(n)]=m.srf();i=n.index('NST '+str(len(ss)));j=next(i for i,s in enumerate(n) if s.startswith('POS '));n[i:j]=['NST '+str(len(newstates))]+newstates
  n[:]=dnm.edit(n,'POS ',' '.join(map(str,np.round(pivot,7)))+' 0 0 0 1')
  rows.append({'aircraft':kind,'part':dnm.name(n),'hinge_m':pivot.tolist(),'refitted_axis':custom,'axis':axis.tolist()})
 for file in [kind+'.dnm',kind+'_coarse.dnm']:dnm.write(r/'runtime/aircraft'/file,p,ns)
(r/'control-changes.json').write_text(json.dumps(rows,indent=2))
