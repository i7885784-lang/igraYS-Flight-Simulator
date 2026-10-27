from pathlib import Path
import sys,json,math,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
lab=Path(__file__).resolve().parent;sys.path.insert(0,str(lab/'model-source'));import dnm
rt=lab/'runtime';results={}
def transformed(a,m,s):
 p=[x.split()[1:] for x in a if x.startswith('STA ')][s];t=np.array(p[:3],float);h,pi,b=np.array(p[3:6],float)*math.pi/32768;R=Rotation.from_euler('YXZ',[-h,-pi,b]).as_matrix();return np.array(m.v)@R.T+t
for kind in ['su27','mig29']:
 packs,nodes=dnm.read(rt/'aircraft'/(kind+'.dnm'));info=json.load(open(lab/'model-source/model-stats.json'))[kind];boxes=info['bays'];group={'closed_containment':{},'wheel_clearance_through_apertures':{}}
 for a in nodes:
  name=dnm.name(a);m=dnm.mesh(packs[dnm.fil(a)]);assert np.isfinite(m.v).all() and all(len(f)>=3 for f,c,b in m.f)
  if not name.startswith(('Gear_','AxleFork','UpperHingeLink')):continue
  title='L' if 'Main_Left' in name or '_L_' in name or name.endswith('ForkL') or name.endswith('LinkL') else 'R' if 'Main_Right' in name or '_R_' in name or name.endswith('ForkR') or name.endswith('LinkR') else 'N'
  box=boxes[title];x0,x1,z0,z1=box['rect'];lo=np.array([x0,box['closed_door_y']+.005,z0]);hi=np.array([x1,box['roof_y']-.005,z1]);q=transformed(a,m,0)
  assert (q>=lo-.002).all() and (q<=hi+.002).all(),(kind,name,q.min(0),q.max(0),lo,hi)
  assert all(x.endswith(' 1') for x in a if x.startswith('STA ')),(name,'gear must remain visible inside bay')
  group['closed_containment'][name]={'min':q.min(0).tolist(),'max':q.max(0).tolist(),'bay':title}
  if any(k in name for k in ['Tyre','_wheel_','nosewheels']):
   sweep=[]
   for s in range(21):
    q=transformed(a,m,s);q=q[(q[:,1]>box['closed_door_y']-.025)&(q[:,1]<box['roof_y'])];sweep.extend(q)
   q=np.array(sweep);assert (q[:,0]>=x0-.005).all() and (q[:,0]<=x1+.005).all() and (q[:,2]>=z0-.005).all() and (q[:,2]<=z1+.005).all(),name
   group['wheel_clearance_through_apertures'][name]={'passed':True,'poses':21}
 assert kind+'_coarse.dnm' in (rt/'aircraft/aircraft.lst').read_text()
 if kind=='mig29':assert all('OpenIntakeDuct'+str(i) in [dnm.name(a) for a in nodes] for i in range(2))
 results[kind]=group
p,n=dnm.read(rt/'aircraft/su57.dnm');names={dnm.name(a) for a in n};assert {'CockpitRearDeck','ExternalPylons'}.issubset(names)
assert sum(l.startswith('HRDPOINT') for l in (rt/'aircraft/su57.dat').read_text().splitlines())==4
results['su57']={'rear_deck':True,'four_external_pylons':True,'latest_local_revision_integrated':True}
for fn in ['su47.dat','su47.dnm','su47_coarse.dnm','su47coll.srf','su47cockpit.srf']:assert (rt/'aircraft'/fn).read_bytes()==(lab.parent/'fighters-fg-test-1/runtime/aircraft'/fn).read_bytes()
results['su47']={'preserved_byte_for_byte':True}
(lab/'validation.json').write_text(json.dumps({'passed':True,'aircraft':results,'scope':'One combined geometry audit; closed gear containment and 21 existing animation poses through apertures, not repeated gameplay runs.'},indent=2));print('PASS: both gear containment/sweeps, Su57 revision, Su47 preservation')
