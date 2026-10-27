"""Check stowed DNM against original editable airframe, including added links."""
from pathlib import Path
import sys,json,math
import numpy as np
from scipy.spatial.transform import Rotation
from shapely import contains_xy
lab=Path(__file__).resolve().parent
sys.path.insert(0,str(lab/'model-source'))
from ac_reference import AC
from fit_internal import reference
import dnm
report={}
for kind in ['su27','mig29']:
 su=kind=='su27';root=lab/'model-source/upstream'/kind
 ac=AC(root/('Su-27.ac' if su else 'mesh_airframe.ac'))
 for o in ac.objects:o['v']=(np.array(o['v'])+np.array([0,0,10 if su else 8.05])).tolist()
 env=reference(ac,su);packs,nodes=dnm.read(lab/'runtime/aircraft'/(kind+'.dnm'));rows=[]
 for n in nodes:
  name=dnm.name(n)
  if not name.startswith(('Gear_','FixedGearTrunnions','UpperHingeLink','AxleFork','NoseDragBrace','NoseTorqueLink','FlushGearDoor','InternalGearBay')):continue
  v=np.array(dnm.mesh(packs[dnm.fil(n)]).v);s=next(s.split()[1:] for s in n if s.startswith('STA '));t=np.array(s[:3],float);h,p,b=np.array(s[3:6],float)*math.pi/32768
  R=Rotation.from_euler('YXZ',[-h,-p,b]).as_matrix();q=v@R.T+t;lo,hi,dist=env.bounds(q)
  res=np.maximum(lo-q[:,1],q[:,1]-hi);foot=contains_xy(env.footprint.buffer(.002),q[:,0],q[:,2]);bad=(res>.015)|~foot
  rows.append({'node':name,'vertices':len(v),'outside_over_15mm':int(bad.sum()),'max_y_error_m':round(float(np.maximum(res,0).max()),5),'outside_footprint':int((~foot).sum()),'all_states_visible':all(s.split()[-1]=='1' for s in n if s.startswith('STA '))})
 assert all(r['outside_over_15mm']==0 and r['all_states_visible'] for r in rows),(kind,rows)
 report[kind]=rows
 print(kind,json.dumps([r for r in rows if r['outside_over_15mm']]),flush=True)
(lab/'checks/source-skin-audit.json').write_text(json.dumps(report,indent=2))
