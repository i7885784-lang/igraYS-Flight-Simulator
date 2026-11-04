from model import Model
import json
from pathlib import Path
m=Model();rows=[]
for g in [0,.1,.25,.5,.75,1]:
 m.sample(g)
 for side in ['Left','Right']:
  a='GearDoor_'+side+'_WheelShield'
  for b in ['Wheel_'+side,'GearUpper_'+side,'GearPiston_'+side,'MainBayFixedSkin_'+side]:
   q=m.collide(a,b)
   if q is not None:rows.append({'g':g,'a':a,'b':b,'point':q.tolist()})
 for a in ['GearDoor_Nose_Inner','GearDoor_Nose_Outer','GearDoor_Nose_Aft']:
  for b in ['Wheel_Nose','GearUpper_Nose','GearPiston_Nose']:
   q=m.collide(a,b)
   if q is not None:rows.append({'g':g,'a':a,'b':b,'point':q.tolist()})
 for a,b in [('Wheel_Nose','GearWell_Nose'),('Wheel_Nose','Su30Interior')]:
  q=m.collide(a,b)
  if q is not None:rows.append({'g':g,'a':a,'b':b,'point':q.tolist()})
Path(__file__).with_name('fix-contacts.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2),flush=True)
