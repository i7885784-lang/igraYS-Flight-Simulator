from pathlib import Path
import sys,numpy as np,json
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *

def pos(n):
 a=next(s for s in n if s.startswith('POS ')).split()[1:];t=np.array(a[:3],float);h,p,b=np.array(a[3:6],float)*np.pi/32768;return Rotation.from_euler('YXZ',[-h,-p,b]).as_matrix(),t
def interpolate(n,idx):
 count=sum(s.startswith('STA ') for s in n);i=min(count-2,int(idx));f=idx-i;R,t=transform(n,i);S,v=transform(n,i+1);z=R[:,2]*(1-f)+S[:,2]*f;z/=np.linalg.norm(z);y=R[:,1]*(1-f)+S[:,1]*f;x=np.cross(y,z);x/=np.linalg.norm(x);return np.c_[x,np.cross(z,x),z],t*(1-f)+v*f
rows=[]
for kind in ['su27','mig29','su34','su47','su57']:
 bp,bns=dnm.read(r/'baseline'/f'{kind}.dnm');p,ns=dnm.read(r/'runtime/aircraft'/f'{kind}.dnm');lu={dnm.name(n):n for n in ns}
 for n in bns:
  cl=dnm.cla(n)
  if cl not in list(range(180,192))+list(range(220,230))+list(range(240,252))+([211,212] if kind in ['su27','mig29'] else []):continue
  m=dnm.mesh(bp[dnm.fil(n)]);new=lu[dnm.name(n)];newm=dnm.mesh(p[dnm.fil(new)]);N=sum(s.startswith('STA ') for s in n);idx=20 if N==41 and kind=='su34' else 0
  R,t=transform(n,idx);P,v=pos(n);a=(np.array(m.v)@R.T+t)@P.T+v;R,t=transform(new,idx);P,v=pos(new);b=(np.array(newm.v)@R.T+t)@P.T+v
  assert a.shape==b.shape
  err=float(np.max(np.linalg.norm(a-b,axis=1)));assert err<.00001,(kind,dnm.name(n),err)
  info={'aircraft':kind,'part':dnm.name(n),'neutral_shape_error_m':err,'states':N}
  # For rebased FG/Su34 surfaces, the new local origin is the fixed hinge.
  if kind in ['su27','mig29','su34']:
   pivot=pos(new)[1];drift=[]
   pairs=[(0,1),(0,2)] if N==3 else [(i,i+1) for i in range(N-1)]
   for ia,ib in pairs:
    R0,t0=transform(n,ia);R1,t1=transform(n,ib)
    for f in np.linspace(0,1,101 if N<=3 else 5):
     z=(1-f)*R0[:,2]+f*R1[:,2];z/=np.linalg.norm(z);y=(1-f)*R0[:,1]+f*R1[:,1];x=np.cross(y,z);x/=np.linalg.norm(x);R=np.c_[x,np.cross(z,x),z];t=(1-f)*t0+f*t1;drift.append(float(np.linalg.norm(R@pivot+t-pivot)))
   info['old_reference_pivot_drift_max_m']=max(drift)
   info['new_pivot_drift_m']=0
   assert all(np.linalg.norm(transform(new,i)[1])<1e-8 for i in range(N))
  rows.append(info)
(r/'control-checks.json').write_text(json.dumps({'passed':True,'neutral_preserved':True,'surfaces':rows},indent=2));print('PASS',len(rows),'surfaces; neutral shape preserved <10um; fixed local pivots')
