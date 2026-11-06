from pathlib import Path
import json,numpy as np,hashlib
from model import Model
from common import dnm
r=Path(__file__).parent;m=Model();moving=[s for s in m.objects if dnm.cla(m.lu[s]) in [210,146] or s.startswith(('WheelFairing','GearLink'))];hits=[]
for g in np.linspace(0,1,201):
 m.sample(float(g))
 for a in ['IntakeDuct_-1','IntakeDuct_1']:
  for b in moving:
   p=m.collide(a,b)
   if p is not None:hits.append({'g':round(float(g),3),'a':a,'b':b,'point':p.tolist()})
print('contacts',len(hits),sorted({(v['a'],v['b']) for v in hits}));(r/'motion.json').write_text(json.dumps({'model_sha256':hashlib.sha256(m.path.read_bytes()).hexdigest(),'samples':201,'contacts':hits,'tested_moving_nodes':moving},indent=2))
