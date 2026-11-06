from pathlib import Path
import json,numpy as np,fcl
from model import Model
r=Path(__file__).parent;m=Model();results=[]
for dz in [.025,.05,.075,.1,.125,.15,.2,.3,.4,.5,.65]:
 hits=[];m.sample(1)
 for name in ['IntakeDuct_-1','IntakeDuct_1']:
  R,t=m.poses[name];t=t+[0,0,-dz];m.objects[name].setTransform(fcl.Transform(R,t));lo,hi=m.worldboxes[name];m.worldboxes[name]=(lo+[0,0,-dz],hi+[0,0,-dz])
  for b in m.objects:
   if name==b or b.startswith(('IntakeDuct','Su30Plume','Su30Dry')):continue
   pt=m.collide(name,b)
   if pt is not None:hits.append({'a':name,'b':b,'point':pt.tolist()})
 results.append({'shift_m':dz,'contacts':hits});print(dz,len(hits),[(h['a'],h['b']) for h in hits],flush=True)
(r/'translation-scan.json').write_text(json.dumps(results,indent=2))
