from pathlib import Path
import json,hashlib,numpy as np,collections
from model import Model
r=Path(__file__).parent;m=Model();old=Model(r/'baseline/su30sm.dnm');hits=[];new=[]
for i,g in enumerate(np.linspace(0,1,201)):
 m.sample(float(g));old.sample(float(g))
 for a in ['IntakeDuct_-1','IntakeDuct_1']:
  for b in m.objects:
   if a==b or b.startswith(('Su30Plume','Su30Dry')):continue
   q=m.collide(a,b)
   if q is not None:
    h={'g':round(float(g),3),'a':a,'b':b,'point':q.tolist()};hits.append(h)
    if old.collide(a,b) is None:new.append(h)
 if i%100==0:print(i,len(hits),len(new),flush=True)
x={'model_sha256':hashlib.sha256(m.path.read_bytes()).hexdigest(),'samples':201,'contacts':hits,'new_contacts':new};(r/'motion.json').write_text(json.dumps(x,indent=2));print(collections.Counter((x['a'],x['b']) for x in hits));print('new examples',new[:6])
