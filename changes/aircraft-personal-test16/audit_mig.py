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
p,ns=dnm.read(root/'runtime/aircraft/mig29.dnm');entries={};moving=[];obstacles=[]
for n in ns:
 name=dnm.name(n)
 if name.startswith(('Gear_','AxleFork','WheelHub','NoseTire','NoseWheelHub')):moving.append(name)
 elif name in ['Hull','EngineL','EngineR','BayRoofRepair','BayWallRepair','ContinuousIntakeL','ContinuousIntakeR'] or name.startswith(('MainBay','Source_fwdgeardoor','Source_reargeardoor','Source_GearWell','InternalGearBayN','FlushGearDoorN','OpenIntakeDuct')):obstacles.append(name)
 else:continue
 entries[name]=(fcl.CollisionObject(make_mesh(dnm.mesh(p[dnm.fil(n)]))),n)
hits=[];req=fcl.CollisionRequest(num_max_contacts=1,enable_contact=True)
def interp(n,u):
 if dnm.cla(n)!=210:return transform(n,0)
 i=min(99,int(u));f=u-i;a,b=transform(n,i),transform(n,i+1);A,B=a.getRotation(),b.getRotation();forward=A[:,2]*(1-f)+B[:,2]*f;forward/=np.linalg.norm(forward);up=A[:,1]*(1-f)+B[:,1]*f;side=np.cross(up,forward);side/=np.linalg.norm(side);up=np.cross(forward,side);return fcl.Transform(np.column_stack([side,up,forward]),a.getTranslation()*(1-f)+b.getTranslation()*f)
for u in np.linspace(0,100,401):
 for obj,n in entries.values():obj.setTransform(interp(n,float(u)))
 for a in moving:
  for b in obstacles:
   res=fcl.CollisionResult()
   if fcl.collide(entries[a][0],entries[b][0],req,res):
    point=np.asarray(res.contacts[0].pos);side=1 if '_L_' in a or a.endswith('ForkL') else -1
    # The upper cylinder mounts deliberately enter the fuselage at the trunnion.
    if a.startswith('Gear_gear1_') and b=='Hull' and np.linalg.norm(point-[side*1.348,.070,-2.09])<.18:continue
    hit={'pose':float(u),'part':a,'obstacle':b,'point':point.round(5).tolist()};hits.append(hit)
    if len(hits)<8:print(hit,flush=True)
(root/'mig-motion-audit.json').write_text(json.dumps({'passed':not hits,'poses':401,'hits':hits},indent=2));print('HITS',len(hits),__import__('collections').Counter((h['part'],h['obstacle']) for h in hits),flush=True)
