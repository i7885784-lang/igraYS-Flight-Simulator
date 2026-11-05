from pathlib import Path
import json,numpy as np
from model import Model
from common import dnm
r=Path(__file__).parent;old=Model(r/'baseline/su30sm.dnm');new=Model();report={}
for tag,m in [('before',old),('after',new)]:
 doors=[s for s in m.objects if s.startswith('GearDoor_')];others=[s for s in m.objects if s.startswith(('Fuselage_','IntakeDuct_','Wheel_','WheelHub_','GearUpper_','GearPiston_','GearAxle_','MainWheelBayShutter_','GearLink_'))];hits=[];cache={}
 for g in np.linspace(0,1,201):
  m.sample(g)
  for a in doors:
   for b in others:
    R,t=m.poses[a];S,v=m.poses[b];k=(a,b,R.tobytes(),t.tobytes(),S.tobytes(),v.tobytes())
    if k not in cache:cache[k]=m.collide(a,b) is not None
    if cache[k]:hits.append({'g':round(float(g),4),'a':a,'b':b})
 report[tag]=hits;print(tag,len(hits),sorted(set((h['a'],h['b']) for h in hits)),flush=True)
(r/'door-clearance-trial.json').write_text(json.dumps(report,indent=2))
