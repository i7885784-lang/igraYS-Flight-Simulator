from intersection_helpers import *
from shapely.geometry import Polygon
from common import dnm
import collections,hashlib
out=[]
names=[n for n in m.objects if n.startswith(('GearDoor_','MainWheelBayShutter_'))]+['GearWell_Nose','GearWell_Left','GearWell_Right']
for name in names:
 v,f=m.meshes[name];res=fcl.CollisionResult();limit=400000;fcl.collide(m.objects[name],m.objects[name],fcl.CollisionRequest(num_max_contacts=limit,enable_contact=True),res);assert len(res.contacts)<limit;seen=set();cross=[];coplanar=[]
 for c in res.contacts:
  i,j=sorted((c.b1,c.b2))
  if i==j or (i,j) in seen:continue
  seen.add((i,j));A=v[f[i]];B=v[f[j]];n=np.cross(A[1]-A[0],A[2]-A[0]);n/=np.linalg.norm(n);dist=(B-A[0])@n
  if abs(dist).max()<1e-7:
   axis=int(np.argmax(abs(n)));P=Polygon(np.delete(A,axis,axis=1));Q=Polygon(np.delete(B,axis,axis=1));area=P.intersection(Q).area
   if area>1e-10:coplanar.append([int(i),int(j),float(area)])
  else:
   seg=segment(A,B)
   if not seg:continue
   a,b=np.array(seg);mid=(a+b)/2
   if np.linalg.norm(a-b)>1e-5 and min(edge_distance(mid,A),edge_distance(mid,B))>1e-5:cross.append([int(i),int(j)])
 row={'name':name,'triangles':len(f),'candidate_pairs':len(seen),'self_crossing':cross,'coplanar_overlap':coplanar};out.append(row);print(name,'self',len(cross),'coplanar',len(coplanar),flush=True)
(r/'selfcheck-final.json').write_text(json.dumps({'model_sha256':hashlib.sha256((r/'runtime/aircraft/su30sm.dnm').read_bytes()).hexdigest(),'checks':out},indent=2))
