"""201 actual inherited gear poses: compare exact triangle crossings with baseline.
FCL supplies candidates only. Narrow phase uses actual serialized coordinates.
"""
from pathlib import Path
import sys,json,argparse,numpy as np,fcl,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin/validation'))
from model import Model
from collision import obj
from triangles import classify
DOORS=['GearDoor_Left_Inner','GearDoor_Right_Outer']
BODY=['Fuselage_0_4','MainBayFixedSkin_Left','MainBayFixedSkin_Right','GearWell_Left','GearWell_Right','IntakeDuct_-1','IntakeDuct_1']
def actual(m):
 import dnm
 p,ns=dnm.read(m.path)
 for name in list(m.objects):
  mm=dnm.mesh(p[dnm.fil(m.lu[name])]);v=np.array(mm.v);ix=np.array([[ids[0],ids[j],ids[j+1]] for ids,c,b in mm.f for j in range(1,len(ids)-1)])
  q=v[ix];ix=ix[np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)>1e-14];m.meshes[name]=(v,ix);m.objects[name]=obj(v,ix);m.boxes[name]=(v.min(0),v.max(0))
 m.sample(0)
def scan(m):
 targets=list(m.objects)  # broad phase rejects distant parts; inspect only the two changed doors
 hits=[]
 for g in np.linspace(0,1,201):
  m.sample(float(g))
  for door in DOORS:
   v,ix=m.meshes[door];R,T=m.poses[door];av=v@R.T+T;lo,hi=m.worldboxes[door]
   for other in targets:
    if other==door:continue
    bl,bh=m.worldboxes[other]
    if np.any(lo>bh) or np.any(bl>hi):continue
    res=fcl.CollisionResult();fcl.collide(m.objects[door],m.objects[other],fcl.CollisionRequest(num_max_contacts=100000,enable_contact=True),res)
    if not res.contacts:continue
    bv,bi=m.meshes[other];B,C=m.poses[other];bv=bv@B.T+C
    found=None
    for c in res.contacts:
     a,b=c.b1,c.b2
     kind=classify(av[ix[a]],bv[bi[b]],tol=2e-6)
     if kind in ['cross','coplanar_overlap']:
      found=dict(g=round(float(g),3),door=door,other=other,kind=kind,a=av[ix[a]].tolist(),b=bv[bi[b]].tolist());break
    if found:hits.append(found)
  if round(g*200)%25==0:print(m.path.name,'pose',round(float(g),3),'hit poses',len(hits),flush=True)
 return hits
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--baseline',required=True);a.add_argument('--candidate',required=True);a.add_argument('--output',required=True);v=a.parse_args();results=[]
 for p in [v.baseline,v.candidate]:
  m=Model(p);actual(m);results.append(scan(m));del m
 key=lambda h:(h['g'],h['door'],h['other'],h['kind']);old={key(h) for h in results[0]};new=[h for h in results[1] if key(h) not in old]
 report=dict(samples=201,tolerance_m=2e-6,actual_serialized_vertices=True,model_sha256=hashlib.sha256(Path(v.candidate).read_bytes()).hexdigest(),baseline_hits=results[0],candidate_hits=results[1],new_crossings=new)
 Path(v.output).write_text(json.dumps(report,indent=2));print('NEW CROSSINGS',len(new),flush=True);assert not new
