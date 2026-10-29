from pathlib import Path
import sys,numpy as np,json,shutil
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'model-source'))
from common import *
report={}
for kind in ['su27','mig29','su34','su47','su57']:
 path=root/'runtime/aircraft'/f'{kind}.dnm';p,ns=dnm.read(path);changed=0
 for n in ns:
  name=dnm.name(n);door=name.startswith(('RootDoor','FlushGearDoor','OriginalSideDoor','Source_fwdgeardoor','Source_reargeardoor','FlushDoor','DoorN','DoorL','DoorR','Door_'))
  body=name in ['Hull','SourceAirframe','Airframe','Fuselage','Su57Hull'] or name.startswith(('MainFuselage','WingSkin'))
  if not door and not body:continue
  m=dnm.mesh(p[dnm.fil(n)]);out=[]
  for ids,c,b in m.f:
   if len(c)>3 or sum(c[:3])<190 or b:out.append((ids,c,b));continue
   q=np.array([m.v[i] for i in ids]);center=q.mean(0);delta=0
   if door and sum(c[:3])>315:delta=6
   elif body and center[1]<.15:
    delta=3 if abs(center[0])>2.4 else -3 if .6<abs(center[0])<2.1 and center[2]<-1.5 else 0
   if delta:c=tuple(min(255,max(0,v+delta)) for v in c);changed+=1
   out.append((ids,c,b))
  m.f=out;p[dnm.fil(n)]=m.srf()
 dnm.write(path,p,ns);shutil.copy2(path,path.with_name(kind+'_coarse.dnm'));report[kind]={'toned_faces':changed,'normal_mode_delta_rgb_max':6}
(root/'palette.json').write_text(json.dumps(report,indent=2))
