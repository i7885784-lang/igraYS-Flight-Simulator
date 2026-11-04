from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'model-source'))
from common import *
import json
r=Path(__file__).parent;(r/'baseline').mkdir(exist_ok=True);p,ns=dnm.read(sys.argv[1]);audit={}
def clip(poly,axis,t,positive):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  da=(a[axis]-t)*(1 if positive else -1);db=(b[axis]-t)*(1 if positive else -1)
  if da>=-1e-12:out.append(a)
  if (da>=0)!=(db>=0):out.append(a+(b-a)*da/(da-db))
 return out
for side,sg,name in [('Left',-1,'GearDoor_Left_Inner'),('Right',1,'GearDoor_Right_Outer')]:
 n=next(n for n in ns if dnm.name(n)==name);m=dnm.mesh(p[dnm.fil(n)]);R,t=transform(n,0);v=np.array(m.v)@R.T+t;mout=Mesh();source=[]
 for i,(ids,c,b) in enumerate(m.f):
  if c!=(57,50,115):continue
  poly=[v[j] for j in ids]
  for axis,value,positive in [(0,-1.87 if sg<0 else 1.03,True),(0,-1.03 if sg<0 else 1.87,False),(2,-1.858,True),(2,-.662,False)]:
   poly=clip(poly,axis,value,positive) if len(poly)>=3 else []
  if len(poly)<3:continue
  for k in range(1,len(poly)-1):
   tri=np.array([poly[0],poly[k],poly[k+1]]);normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);area=np.linalg.norm(normal)
   if area<1e-10:continue
   if normal[1]>0:tri=tri[::-1]
   mout.face(tri,(142,169,181));source.append(i)
 (r/'baseline'/('support-'+side+'.srf')).write_text('\n'.join(mout.srf())+'\n');audit[side]={'source_node':name,'source_face_ids':source,'triangles':len(mout.f),'bounds':[np.array(mout.v).min(0).tolist(),np.array(mout.v).max(0).tolist()]}
(r/'support-provenance.json').write_text(json.dumps(audit,indent=2));print({k:v['triangles'] for k,v in audit.items()})
