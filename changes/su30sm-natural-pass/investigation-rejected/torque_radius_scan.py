from pathlib import Path
import json,numpy as np
from model import Model
from collision import obj
r=Path(__file__).parent;out=[]
for rad in [.024,.022,.020,.018,.016,.010,.001]:
 m=Model(r/'baseline/su30sm.dnm');hits=[]
 for side in ['Left','Right']:
  name='GearLink_TorqueUpper_'+side;v,f=m.meshes[name];v=v.copy();v[:,[0,2]]*=rad/.024;m.objects[name]=obj(v,f);m.meshes[name]=(v,f);m.boxes[name]=(v.min(0),v.max(0))
 for g in np.linspace(.25,.4,151):
  m.sample(float(g))
  for side in ['Left','Right']:
   p=m.collide('GearLink_TorqueUpper_'+side,'MainBayFixedSkin_'+side)
   if p is not None:hits.append({'g':round(float(g),4),'side':side})
 out.append({'radius_m':rad,'contacts':hits});print(rad,len(hits),flush=True)
(r/'torque-radius-scan.json').write_text(json.dumps(out,indent=2))
