from pathlib import Path
import json,numpy as np,hashlib
from model import Model
from common import dnm
r=Path(__file__).parent;m=Model();moving=[name for name in m.objects if (dnm.cla(m.lu[name]) in [210,146] or name.startswith(('WheelFairing','GearLink')))];doors=[s for s in m.objects if s.startswith('GearDoor_')];cover=[s for s in m.objects if s.startswith('MainWheelBayShutter_')];nose=[s for s in m.objects if s.endswith('_Nose') and s.startswith(('Wheel_','WheelHub_','GearUpper','GearPiston','GearAxle','GearLink'))];static=[s for s in m.objects if s.startswith(('GearBayStructure','BayCornerSkin','GearBayUpperClosure','DoorSeat','GearWell_'))];bodies=[s for s in m.objects if s.startswith(('Fuselage_','IntakeDuct_'))];pairs=set()
for a in cover:
 for b in m.objects:
  if a!=b:pairs.add((a,b))
for a in doors:
 for b in bodies+moving:
  if a!=b and not b.startswith(('GearDoor_','DoorHingePin_')):pairs.add((a,b))
for a in static:
 for b in moving:pairs.add((a,b))
for a in nose:
 for b in ['Fuselage_0_4','GearWell_Nose']:pairs.add((a,b))
for b in moving:
 if not b.startswith(('DoorHingePin','GearDoor_')):pairs.add(('DoorHingeForks',b))
hits=[];cache={};tested=0
for i,g in enumerate(np.linspace(0,1,201)):
 m.sample(g)
 for a,b in sorted(pairs):
  R,t=m.poses[a];S,v=m.poses[b];key=(a,b,R.tobytes(),t.tobytes(),S.tobytes(),v.tobytes())
  if key not in cache:cache[key]=m.collide(a,b) is not None;tested+=1
  if cache[key]:hits.append({'g':round(float(g),4),'a':a,'b':b})
 if i%50==0:print('pose',round(float(g),3),'hits',len(hits),flush=True)
out={'model_sha256':hashlib.sha256((r/'runtime/aircraft/su30sm.dnm').read_bytes()).hexdigest(),'samples':201,'all_101_keys_and_100_midpoints':True,'pair_definitions':len(pairs),'distinct_pose_pairs_tested':tested,'contacts':hits,'intentional_hinge_pin_own_fork_and_door_contacts_not_classified_as_obstruction':True,'full_continuous_collision_proof':False};(r/'final-motion.json').write_text(json.dumps(out,indent=2));print('FINALcontacts',len(hits),sorted(set((h['a'],h['b']) for h in hits)),flush=True)
