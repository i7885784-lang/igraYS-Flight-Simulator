from pathlib import Path
import json,numpy as np
from model import Model
r=Path(__file__).parent;m=Model();hits=[];cache={}
for g in np.linspace(0,1,201):
 m.sample(g)
 for side in ['Left','Right']:
  a='MainWheelBayShutter_'+side
  for b in m.objects:
   if b==a:continue
   R,t=m.poses[a];S,v=m.poses[b];k=(a,b,R.tobytes(),t.tobytes(),S.tobytes(),v.tobytes())
   if k not in cache:cache[k]=m.collide(a,b) is not None
   if cache[k]:hits.append({'g':round(float(g),4),'a':a,'b':b})
(r/'cover-clearance-final.json').write_text(json.dumps(hits,indent=2));print('covercontacts',len(hits),sorted(set((h['a'],h['b']) for h in hits)),flush=True)
