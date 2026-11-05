from pathlib import Path
import sys,json,numpy as np
from model import Model
r=Path(__file__).parent;m=Model();dynamic=[name for name in m.objects if any(s in name for s in ['Gear','Wheel']) and not name.startswith(('GearBayStructure','GearWell','GearBearing','GearDoor','MainWheelBay','DoorSeat'))];dynamic+=[n for n in m.objects if n.startswith(('GearDoor','MainWheelBay'))];details=[n for n in m.objects if n.startswith('GearBayStructure')];hits=[]
for g in np.linspace(0,1,101):
 m.sample(g)
 for a in details:
  for b in dynamic:
   if m.collide(a,b) is not None:hits.append({'g':round(float(g),4),'a':a,'b':b})
(r/'stage1-moving-contacts.json').write_text(json.dumps(hits,indent=2));print('New structure/moving contacts',len(hits));print(sorted(set((h['a'],h['b']) for h in hits)))
