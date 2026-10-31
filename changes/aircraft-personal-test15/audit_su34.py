from pathlib import Path
import sys,numpy as np,json,fcl
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'model-source'))
import dnm
from common import transform as state_rt
from collision import arrays

def make_mesh(m):
 v,f=arrays(m);b=fcl.BVHModel();b.beginModel(len(v),len(f));b.addSubModel(v,f);b.endModel();return b

def transform(n,idx=0):
 R,t=state_rt(n,idx);return fcl.Transform(R,t)
r=Path(__file__).resolve().parent;p,ns=dnm.read(r/'runtime/aircraft/su34.dnm');lu={dnm.name(n):n for n in ns};entries={};moving=[];obstacles=[]
for name,n in lu.items():
 if name.startswith(('MainCylinder','MainInnerStem','TandemTruck')) or name in ['GearN','WheelsN','LandingLamp39','LandingLamp40']:moving.append(name)
 elif name in ['SourceAirframe','ConformalWingRootBaySides','InternalWellN','OwnCockpitLiner','Source_chassis','RecessedGearBaySeals','RecessedNoseBaySeal','BayRoofRepair','BayWallRepair','MainBaySeals','IntakeChannelL','IntakeChannelR','InsideIntakeL','InsideIntakeR'] or name.startswith(('OriginalSideDoor','FlushDoorN')):obstacles.append(name)
 else:continue
 entries[name]=(fcl.CollisionObject(make_mesh(dnm.mesh(p[dnm.fil(n)]))),n)
def interp(n,u):
 if dnm.cla(n)!=210:return transform(n,0)
 i=min(99,int(u));f=u-i;a,b=transform(n,i),transform(n,i+1);A,B=a.getRotation(),b.getRotation();forward=A[:,2]*(1-f)+B[:,2]*f;forward/=np.linalg.norm(forward);up=A[:,1]*(1-f)+B[:,1]*f;side=np.cross(up,forward);side/=np.linalg.norm(side);up=np.cross(forward,side);return fcl.Transform(np.column_stack([side,up,forward]),a.getTranslation()*(1-f)+b.getTranslation()*f)
hits=[];req=fcl.CollisionRequest(num_max_contacts=1,enable_contact=True)
for u in np.linspace(0,100,401):
 for obj,n in entries.values():obj.setTransform(interp(n,float(u)))
 for a in moving:
  for b in obstacles:
   res=fcl.CollisionResult()
   if fcl.collide(entries[a][0],entries[b][0],req,res):
    hits.append({'gear':float(u),'part':a,'obstacle':b,'point':np.asarray(res.contacts[0].pos).round(5).tolist()})
    if len(hits)<10:print(hits[-1],flush=True)
result={'passed':not hits,'checked':'main gear vs source airframe and both moving cover types; native between-state interpolation','poses':401,'hits':hits,'nose_included':True};(r/'motion-audit.json').write_text(json.dumps(result,indent=2));print('PASS',not hits,'hits',len(hits),flush=True)
