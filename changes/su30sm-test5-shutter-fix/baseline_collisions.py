from pathlib import Path
import numpy as np,json,time
from model import Model
r=Path(__file__).parent;m=Model(r/"baseline/su30sm.dnm");report={}
# Exhaust all 101 keys and 100 midpoints. Cache identical pairs of poses.
hits=[];cache={};tested=0;cached=0;start=time.monotonic();states=np.linspace(0,1,201)
for gi,g in enumerate(states):
 m.sample(float(g))
 for side in ['Left','Right']:
  a='MainWheelBayShutter_'+side
  for b in m.objects:
   if b==a:continue
   # Includes every other visible mesh available to the diagnostic evaluator.
   Ra,ta=m.poses[a];Rb,tb=m.poses[b];key=(a,b,Ra.tobytes(),ta.tobytes(),Rb.tobytes(),tb.tobytes())
   if key in cache:q=cache[key];cached+=1
   else:q=m.collide(a,b);cache[key]=None if q is None else q.tolist();tested+=1
   if q is not None:hits.append({'g':float(g),'a':a,'b':b,'point':np.array(q).tolist()})
 if gi%40==0:print('pose',round(float(g),3),'contacts',len(hits),flush=True)
report['animation']={'samples':[float(g) for g in states],'all_101_keys_and_100_midpoints':True,'pairs_evaluated':tested,'identical_pairs_reused':cached,'other_meshes':len(m.objects)-1,'contacts':hits,'elapsed_seconds':round(time.monotonic()-start,2)}
(r/'baseline-collisions.json').write_text(json.dumps(report,indent=2));print('validation done; contacts',len(hits),flush=True)

