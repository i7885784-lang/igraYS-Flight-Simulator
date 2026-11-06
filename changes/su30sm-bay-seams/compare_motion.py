from pathlib import Path
import json,hashlib,numpy as np,time
from model import Model
r=Path(__file__).parent;a=json.loads((r/'repair-audit.json').read_text());names=[s.removesuffix('.srf') for s in a['changed_packs']];before=Model(r/'baseline/su30sm.dnm');after=Model();pairs=set()
for x in names:
 for y in after.objects:
  if x==y or y.startswith(('Su30Plume','Su30Dry','Su30Nozzle','Airbrake','Air_Brake','Canopy','Su30Interior','AirbrakeActuator')):continue
  pairs.add(tuple(sorted((x,y))))
out={'model_sha256':hashlib.sha256(after.path.read_bytes()).hexdigest(),'samples':201,'tested_pairs':len(pairs),'before_contacts':[],'after_contacts':[],'new_pair_poses':[],'removed_pair_poses':[]};start=time.time()
for i,g in enumerate(np.linspace(0,1,201)):
 before.sample(float(g));after.sample(float(g))
 for x,y in sorted(pairs):
  hitb=before.collide(x,y);hita=after.collide(x,y)
  item={'g':round(float(g),3),'a':x,'b':y}
  if hitb is not None:out['before_contacts'].append(dict(item,point=hitb.tolist()))
  if hita is not None:out['after_contacts'].append(dict(item,point=hita.tolist()))
  if hita is not None and hitb is None:out['new_pair_poses'].append(dict(item,point=hita.tolist()))
  if hita is None and hitb is not None:out['removed_pair_poses'].append(item)
 if i%40==0:print(i,len(out['new_pair_poses']),round(time.time()-start,1),flush=True)
(r/'motion-comparison.json').write_text(json.dumps(out,indent=2));print('new',len(out['new_pair_poses']),'removed',len(out['removed_pair_poses']),'after',len(out['after_contacts']),flush=True)
