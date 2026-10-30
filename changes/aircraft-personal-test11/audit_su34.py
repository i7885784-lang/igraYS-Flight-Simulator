from pathlib import Path
"""Exact triangle intersections: gear tyres against doors, wells and airframe."""
from pathlib import Path
import sys,json,math
import numpy as np
from scipy.spatial.transform import Rotation
import fcl
sys.path.insert(0,str(Path(__file__).resolve().parent/'model-source'));import dnm

def make_mesh(m):
 vertices,index=np.unique(np.round(m.v,6),axis=0,return_inverse=True);faces=[]
 for ids,col,b in m.f:
  for k in range(1,len(ids)-1):
   tri=index[[ids[0],ids[k],ids[k+1]]]
   q=vertices[tri]
   if np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))>1e-10:faces.append(tri)
 faces=np.unique(np.sort(faces,axis=1),axis=0).astype(np.int32);model=fcl.BVHModel();model.beginModel(len(vertices),len(faces));model.addSubModel(vertices,faces);model.endModel();return model

def transform(n,state=0):
 states=[s.split()[1:] for s in n if s.startswith('STA ')];s=states[min(state,len(states)-1)];t=np.array(s[:3],float);h,p,b=np.array(s[3:6],float)*math.pi/32768;R=Rotation.from_euler('YXZ',[-h,-p,b]).as_matrix();return fcl.Transform(R,t)


r=Path(__file__).resolve().parent;p,ns=dnm.read(r/'runtime/aircraft/su34.dnm');lu={dnm.name(n):n for n in ns};entries={};moving=[];obstacles=[]
for name,n in lu.items():
 if name.startswith(('MainCylinder','MainInnerStem','TandemTruck')) or name in ['GearN','WheelsN','LandingLamp39','LandingLamp40']:moving.append(name)
 elif name in ['SourceAirframe','ConformalWingRootBaySides','InternalWellN','OwnCockpitLiner','Source_chassis','RecessedGearBaySeals','InternalSeamSeatMain','InternalSeamSeatNose'] or name.startswith(('OriginalSideDoor','FlushDoorN')):obstacles.append(name)
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
    hits.append({'gear':float(u),'part':a,'obstacle':b})
    if len(hits)<10:print(hits[-1],flush=True)
result={'passed':not hits,'checked':'main gear vs source airframe and both moving cover types; native between-state interpolation','poses':401,'hits':hits,'nose_included':True};(r/'motion-audit.json').write_text(json.dumps(result,indent=2));print('PASS',not hits,'hits',len(hits),flush=True)
