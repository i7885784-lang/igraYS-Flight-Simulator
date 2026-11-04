from pathlib import Path
import numpy as np,json,hashlib
from model import Model
r=Path(__file__).parent;m=Model();contacts=[];rigidity=[]
for g in [0,.1,.2,.3,.5,.7,.8,.9,1]:
 m.sample(g)
 for side in ['Left','Right']:
  R,C=m.poses['WheelCarrier_'+side]
  for part in ['WheelFairing_'+side,'WheelFairingBrace_'+side]:
   S,T=m.poses[part];rigidity.append(float(np.max(abs(S-R)))+float(np.max(abs(T-C))))
  for a,b in [('MainWheelBayShutter_'+side,'Wheel_'+side),('MainWheelBayShutter_'+side,'WheelFairing_'+side),('WheelFairing_'+side,'Wheel_'+side),('WheelFairingBrace_'+side,'Wheel_'+side),('MainWheelBayShutter_'+side,'GearUpper_'+side),('MainWheelBayShutter_'+side,'GearPiston_'+side)]:
   q=m.collide(a,b)
   if q is not None:contacts.append({'g':g,'a':a,'b':b,'point':q.tolist()})
for g in [0,.1,.2,.3,.5,.7,.8,.9,1]:
 m.sample(g)
 for name in m.lu:
  if not name.startswith('GearDoor_'):continue
  side='Nose' if '_Nose_' in name else 'Left' if '_Left_' in name else 'Right'
  for b in ['Wheel_'+side,'GearUpper_'+side,'GearPiston_'+side]:
   q=m.collide(name,b)
   if q is not None:contacts.append({'g':g,'a':name,'b':b,'point':q.tolist()})
assert max(rigidity)<1e-10
(r/'assembly-check.json').write_text(json.dumps({'model_sha256':hashlib.sha256((r/'runtime/aircraft/su30sm.dnm').read_bytes()).hexdigest(),'poses':[0,.1,.2,.3,.5,.7,.8,.9,1],'rigid_attachment_error':max(rigidity),'contacts':contacts},indent=2));print(json.dumps(contacts,indent=2),flush=True)
