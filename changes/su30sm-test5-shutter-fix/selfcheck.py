from intersection_helpers import *
from shapely.geometry import Polygon
out=[]
for side in ['Left','Right']:
 name='MainWheelBayShutter_'+side;v,f=m.meshes[name];obj=m.objects[name];res=fcl.CollisionResult();fcl.collide(obj,obj,fcl.CollisionRequest(num_max_contacts=200000,enable_contact=True),res);bad=[];coplanar=[];seen=set()
 for c in res.contacts:
  i,j=sorted((c.b1,c.b2))
  if i==j or (i,j) in seen:continue
  seen.add((i,j));A=v[f[i]];B=v[f[j]];n=np.cross(A[1]-A[0],A[2]-A[0]);n/=np.linalg.norm(n);dist=(B-A[0])@n
  if abs(dist).max()<1e-7:
   axis=np.argmax(abs(n));P=Polygon(np.delete(A,axis,axis=1));Q=Polygon(np.delete(B,axis,axis=1));area=P.intersection(Q).area
   if area>1e-10:coplanar.append([int(i),int(j),float(area)])
  else:
   seg=segment(A,B)
   if seg:
    a,b=np.array(seg);mid=(a+b)/2;d=min(edge_distance(mid,A),edge_distance(mid,B))
    if np.linalg.norm(a-b)>1e-5 and d>1e-6:bad.append([int(i),int(j),float(np.linalg.norm(a-b)),float(d)])
 out.append({'name':name,'triangles':len(f),'fcl_contacts':len(res.contacts),'candidate_pairs':len(seen),'self_crossing':bad,'coplanar_overlap':coplanar});print(name,len(f),'cross',len(bad),'overlap',len(coplanar),flush=True)
(r/'selfcheck.json').write_text(json.dumps(out,indent=2))
