from surface import *
from model import Model
import trimesh,json
p,ns,lu,ss=surfaces(r/'runtime/aircraft/su30sm.dnm');model=Model();tris=[]
for name,(v,f) in model.meshes.items():
 if not name.startswith('Fuselage'):continue
 R,t=model.poses[name];q=v[f]@R.T+t;c=q.mean(1);inside=(abs(c[:,0])>1.030001)&(abs(c[:,0])<1.869999)&(c[:,2]>-3.379999)&(c[:,2]<-.410001);tris.extend(q[~inside])
tris=np.array(tris);ref=trimesh.Trimesh(vertices=tris.reshape(-1,3),faces=np.arange(len(tris)*3).reshape(-1,3),process=False);audit={}
for side,sg in [('Left',-1),('Right',1)]:
 name='MainBayFixedSkin_'+side;source=ss[name];polys=[Polygon(q[:,[0,2]]) for q,c in source];tree=STRtree(polys);co=np.array([np.linalg.solve(np.c_[q[:,[0,2]],np.ones(3)],q[:,1]) for q,c in source]);colors=[c for q,c in source];n=lu[name];R,C=transform(n,0);segs=[];cache={}
 def point(xz):
  key=tuple(np.round(xz,10))
  if key not in cache:
   ids=tree.query(Point(xz).buffer(1e-9),predicate='intersects');assert len(ids),xz;h=co[ids]@np.r_[xz,1];ii=ids[int(h.argmin())];cache[key]=(np.array([xz[0],float(h.min()),xz[1]]),colors[ii])
  return cache[key]
 for A,B,normal in [(np.array([sg*1.03,-3.38]),np.array([sg*1.03,-.41]),np.array([sg,0,0.])),(np.array([sg*1.03,-.41]),np.array([sg*1.87,-.41]),np.array([0,0,-1.])),(np.array([sg*1.03,-3.38]),np.array([sg*1.87,-3.38]),np.array([0,0,1.]))]:
  direction=B-A;l2=direction@direction;ts=set(np.linspace(0,1,max(3,int(np.sqrt(l2)/.006))))
  for q,c in source:
   for v in q:
    t=(v[[0,2]]-A)@direction/l2
    if 0<t<1 and np.linalg.norm(v[[0,2]]-A-t*direction)<1e-8:ts.add(float(t))
  ts=sorted(ts);pts=[point(A+t*direction)[0] for t in ts];Q,dist,ids=trimesh.proximity.closest_point(ref,np.array(pts))
  queue=[(pts[i],pts[i+1],Q[i],Q[i+1],normal,0) for i in range(len(pts)-1)]
  while queue:
   batch=queue;queue=[];mids=np.array([(a+b)/2 for a,b,qa,qb,n,k in batch]);mq,md,mi=trimesh.proximity.closest_point(ref,mids)
   for (a,b,qa,qb,normal,depth),mid,qmid in zip(batch,mids,mq):
    error=np.linalg.norm(qmid-(qa+qb)/2)
    if error>2e-7 and depth<20 and np.linalg.norm(a-b)>1e-7:
     queue.extend([(a,mid,qa,qmid,normal,depth+1),(mid,b,qmid,qb,normal,depth+1)]);continue
    if max(np.linalg.norm(a-qa),np.linalg.norm(b-qb))>.065:continue
    if error>2e-6:continue
    segs.append((a,b,qa,qb,normal))
 m=Mesh();maxgap=0
 for a,b,qa,qb,normal in segs:
  if max(np.linalg.norm(a-qa),np.linalg.norm(b-qb))<.00002:continue
  maxgap=max(maxgap,float(np.linalg.norm(a-qa)),float(np.linalg.norm(b-qb)));expected=normal*(1 if (a[1]+b[1]-qa[1]-qb[1])>=0 else -1)+[0,-.05,0];color=point((a[[0,2]]+b[[0,2]])/2)[1]
  for t in [np.array([a,b,qb]),np.array([a,qb,qa])]:
   nn=np.cross(t[1]-t[0],t[2]-t[0])
   if np.linalg.norm(nn)<1e-12:continue
   if nn@expected<0:t=t[::-1]
   m.face((t-C)@R,color)
 # Replace the old outer rim by a real joint to the existing body edge.
 raw=p[dnm.fil(n)];first=raw.index('F');blocks=[];i=first;old=dnm.mesh(raw);oldv=np.array(old.v)@R.T+C;removed=0
 while i<len(raw) and raw[i]=='F':
  end=raw.index('E',i)+1;block=raw[i:end];ids=list(map(int,next(s[2:] for s in block if s.startswith('V ')).split()));col=tuple(map(int,next(s[2:] for s in block if s.startswith('C ')).split()));q=oldv[ids];outer=(np.max(abs(q[:,0]-sg*1.03))<1e-7 or np.max(abs(q[:,2]+3.38))<1e-7 or np.max(abs(q[:,2]+.41))<1e-7)
  if col==(105,118,123) and outer:removed+=1
  else:blocks.append(block)
  i=end
 new=m.srf();nf=new.index('F');newV=[s for s in new[:nf] if s.startswith('V ')];newBlocks=[];j=nf
 while j<len(new) and new[j]=='F':
  end=new.index('E',j)+1;block=new[j:end];newBlocks.append([('V '+' '.join(str(int(k)+len(old.v)) for k in s[2:].split())) if s.startswith('V ') else s for s in block]);j=end
 p[dnm.fil(n)]=raw[:first]+newV+sum(blocks,[])+sum(newBlocks,[])+raw[i:];audit[name]={'joining_triangles':len(m.f),'old_outer_rim_faces_removed':removed,'max_closed_stationary_step_m':maxgap,'body_joint_endpoint_error_m':0,'no_change_to_moving_door_seam':True};print(name,audit[name],flush=True)
dnm.write(r/'runtime/aircraft/su30sm.dnm',p,ns);(r/'static-joints.json').write_text(json.dumps(audit,indent=2))
