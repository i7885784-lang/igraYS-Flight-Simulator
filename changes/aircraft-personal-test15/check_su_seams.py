from pathlib import Path
import sys,numpy as np,json,fcl
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
from collision import arrays,obj,interpolate
report={}
for kind in ['su27','su34']:
 p,ns=dnm.read(Path(__import__('os').environ.get('SEAM_RUNTIME',str(r/'runtime')))/'aircraft'/f'{kind}.dnm')
 if kind=='su27':moving=[n for n in ns if dnm.cla(n)==210];fixed=[n for n in ns if dnm.name(n).startswith('ConformalMainBayLiner')]
 else:moving=[n for n in ns if dnm.name(n).startswith('OriginalSideDoor') and dnm.name(n).endswith('Wheel')];fixed=[n for n in ns if dnm.name(n) in ['SourceAirframe','ConformalWingRootBaySides','InternalSeamSeatMain','MainBaySeals'] or dnm.name(n).startswith('Su34RearBayInnerWall')]
 mo=[(obj(*arrays(dnm.mesh(p[dnm.fil(n)]))),n) for n in moving];st=[(obj(*arrays(dnm.mesh(p[dnm.fil(n)]))),n) for n in fixed];hits=[];hinge=0
 for g in np.linspace(0,1,401):
  for a,n in mo:a.setTransform(interpolate(n,float(g)))
  for a,n in mo:
   for b,o in st:
    res=fcl.CollisionResult()
    if fcl.collide(a,b,fcl.CollisionRequest(num_max_contacts=1,enable_contact=True),res):
     q=np.array(res.contacts[0].pos)
     if kind=='su34' and np.linalg.norm(q[:2]-[2.662*(1 if 'DoorL' in dnm.name(n) else -1),-.245])<.025:hinge+=1;continue
     h={'g':float(g),'moving':dnm.name(n),'fixed':dnm.name(o),'point':q.round(5).tolist()};hits.append(h)
     if len(hits)<6:print(kind,h,flush=True)
 report[kind]={'passed':not hits,'poses':401,'hits':hits,'mount_contacts_within_25mm':hinge};print(kind,'hits',len(hits),'hinge contacts',hinge,flush=True)
(r/__import__('os').environ.get('SEAM_OUTPUT','su-seam-collision-checks.json')).write_text(json.dumps(report,indent=2))
