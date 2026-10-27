"""Private geometry rig; fit source legs and adapted tandem wheels inside original skin."""
import numpy as np,math,json
from pathlib import Path
from scipy.spatial.transform import Rotation
from scipy.optimize import differential_evolution
from mesh import Mesh
from envelope import Envelope
from gear_v3 import clip,normal
from source_parts import components
from recessed_well import make_well
from curved_panel import make_panel

def align(a,b):
 a=np.array(a,float,copy=True);a/=np.linalg.norm(a);b=np.array(b,float,copy=True);b/=np.linalg.norm(b);c=np.cross(a,b);d=float(np.clip(a@b,-1,1))
 return np.eye(3) if np.linalg.norm(c)<1e-9 else Rotation.from_rotvec(c/np.linalg.norm(c)*math.acos(d)).as_matrix()

def add_rig(meshes,source,C,offset,hull,add,double,sta,cv,rotate):
 rawfaces=[(np.array([hull.v[i] for i in ids]),col,br) for ids,col,br in hull.f]
 main=max(components(rawfaces),key=len);verts=np.concatenate([f[0] for f in main]);lengths=[len(f[0]) for f in main];offsets=np.cumsum([0]+lengths)
 objects=[{'name':'original_main_airframe','v':verts.tolist(),'f':[list(range(a,b)) for a,b in zip(offsets,offsets[1:])]}]
 # Close only the original gear apertures, following adjoining wing-root lower skin.
 for sg in [-1,1]:
  objects.append({'name':'main_aperture_flush_reference','v':[(sg*1.50,-.65,-1.50),(sg*2.20,-.02,-1.50),(sg*2.20,-.02,.65),(sg*1.50,-.65,.65)],'f':[[0,1,2,3]]})
 from nose_skin import close_nose
 objects.append(close_nose(objects))
 # Include armored cockpit roof only as upper envelope; don't invent extra volume.
 
 m=meshes[16];objects.append({'name':'glazing','v':m.v,'f':[f[0] for f in m.f]})
 env=Envelope(objects)
 (Path(__file__).resolve().parent/'envelope-reference.json').write_text(json.dumps(objects))
 report={};bays=[]
 for title,b,wb in [('N',33,34),('L',41,42),('R',43,44)]:
  nose=title=='N';leg=meshes[b];wheel=meshes[wb];sign=1 if title=='L' else -1
  if not nose:
   # Source braces are rigidly baked to the leg; replace only those links with IK.
   keep=Mesh();raw=[]
   for ids,col,bright in leg.f:raw.append((np.array([leg.v[i] for i in ids]),col,bright))
   for comp in components(raw):
    q=np.array([f[0] for f in comp]).reshape(-1,3);original=(q-offset)@np.linalg.inv(C).T
    if len(comp) not in [32,20] and not (len(comp)==10 and original[:,2].min()<-1.0):continue
    for poly,col,bright in comp:keep.face(poly,col,bright)
   leg=keep
  pivot=cv(source.skeleton[b]['position']);axle=cv(source.skeleton[wb]['position'])
  pivot[1]=.30 if nose else .15
  if not nose:
   # Actual Su-34 uses tandem main wheels. Adapt the source tyre mesh twice.
   tandem=Mesh();front=Mesh();front.merge(wheel);front.shift(0,.17*C[1,2],0);tandem.merge(front)
   rear=Mesh();rear.merge(front);rear.shift(0,0,-1.05*C[2,1]);tandem.merge(rear);wheel=tandem
   axle=front_center=cv(source.skeleton[wb]['position'])+np.array([0,.17*C[1,2],-.525*C[2,1]])
   center=np.asarray(leg.v).mean(0);axlex=(sign*2.46)*abs(C[0,0]);bogie=Mesh()
   a=np.array([axlex,axle[1],axle[2]-.525*C[2,1]]);end=a+np.array([0,0,1.05*C[2,1]])
   bogie.tube(a,end,.065,(128,146,158),12)
   for z in [a[2],end[2]]:bogie.tube((axlex,axle[1],z),(axle[0],axle[1],z),.065,(149,166,178),12)
   wheel.v=[(axle[0]+(x-axle[0])*.72,y,z) for x,y,z in wheel.v]
   wheel.merge(bogie)
  upper=Mesh();lower=Mesh()
  if not nose:
   pieces=[(np.array([leg.v[i] for i in ids]),col,br) for ids,col,br in leg.f]
   for comp in components(pieces):
    dest=upper if len(comp)==20 else lower
    for poly,col,br in comp:dest.face(poly,col,br)
  else:upper=leg
  if not nose:
   from main_gear import build_main
   info=build_main(title,upper,lower,wheel,source,b,env,add,double,sta,cv,align)
   storage=(.20,2.75,-3.95,1.05) if sign>0 else (-2.75,-.20,-3.95,1.05);rect=(.85,2.38,-3.25,.65) if sign>0 else (-2.38,-.85,-3.25,.65)
   info['rect']=rect;info['storage_rect']=storage;bays.append((title,rect,storage));report[title]=info;continue
  leg=upper;V=np.unique(np.round(leg.v,5),axis=0);L=np.unique(np.round(lower.v,5),axis=0) if lower.v else np.empty((0,3));W=np.unique(np.round(wheel.v,5),axis=0)
  if not nose:
   def samples(mesh):
    rows=list(mesh.v)
    for ids,col,br in mesh.f:
     q=np.array([mesh.v[i] for i in ids]);center=q.mean(0);rows.append(center)
     for a,b in zip(q,np.roll(q,-1,axis=0)):rows.extend(a+(b-a)*f for f in np.linspace(0,1,max(2,int(np.linalg.norm(b-a)/.03)+1)))
     for a in q:
      for f in [.25,.5,.75]:rows.append(a*(1-f)+center*f)
    return np.unique(np.round(rows,5),axis=0)
   V=samples(leg);L=samples(lower)
  d=axle-pivot;length=np.linalg.norm(d)
  def eval(params,ret=False):
   x,y,roll,swivel,compression=(0.,params[0],0.,0.,0.) if nose else (sign*params[0],params[1],params[2],params[3],params[4])
   short=d*(1-compression/length);ln=np.linalg.norm(short);dz=ln*ln-(x-pivot[0])**2-(y-pivot[1])**2
   if dz<=0:return 1e7
   target=np.array([x,y,pivot[2]+(-1 if nose else 1)*math.sqrt(dz)]);axis=(target-pivot)/ln
   R=Rotation.from_rotvec(axis*roll).as_matrix()@align(short,target-pivot);t=pivot-R@pivot
   A=Rotation.from_rotvec(np.array([0.,swivel,0.])).as_matrix()@Rotation.from_rotvec(np.array([0.,0.,sign*math.pi/2])).as_matrix() if not nose else R;Q=A@R.T;u=target-A@axle
   q=np.concatenate([V@R.T+t,(L-d*compression/length)@R.T+t,W@A.T+u]);lo,hi,dist=env.bounds(q);hi=np.minimum(hi,.98 if nose else .40)
   res=np.concatenate([np.maximum(lo+.025-q[:,1],0),np.maximum(q[:,1]+.025-hi,0),np.maximum(dist-.012,0)*3])
   center_penalty=np.maximum(1.30-sign*q[:,0],0) if not nose else np.array([0.])
   cost=np.sum(res*res)+np.sum(center_penalty**2)*3+1e-7*(roll*roll+compression*compression)+1e-6*swivel*swivel+1e-5*((abs(x)-1.85)**2)
   
   if ret:
    bad=np.maximum.reduce([np.maximum(lo+.025-q[:,1],0),np.maximum(q[:,1]+.025-hi,0),np.maximum(dist-.012,0)*3]);ids=np.argsort(bad)[-3:];print(title,'worst',q[ids],bad[ids],flush=True)
   return (R,Q,target,compression,float(res.max())) if ret else float(cost)
  bounds=[(-.15,.65)] if nose else [(1.65,2.15),(-.55,.25),(-math.pi,math.pi),(-1.20,1.20),(.40,.75)]
  result=differential_evolution(eval,bounds,seed=47,popsize=12,maxiter=160,tol=1e-7,polish=True);R,Q,target,compression,error=eval(result.x,True)
  # Adapt only small fork/corner clearances; never hide or globally shrink the leg.
  corner_adjustments={}
  for label,mesh,M,translation in [('upper',leg,R,pivot-R@pivot),('lower',lower,R,pivot-R@pivot-R@d*compression/length),('tyres',wheel,Q@R,target-(Q@R)@axle)]:
   if not mesh.v:continue
   points=np.asarray(mesh.v);world=points@M.T+translation;lo,hi,dist=env.bounds(world);hi=np.minimum(hi,.98 if nose else .40)
   correction=np.maximum(lo+.025-world[:,1],0)-np.maximum(world[:,1]-(hi-.025),0);maximum=float(abs(correction).max())
   if maximum>.060 or dist.max()>.03:raise RuntimeError(('Fit needs redesign, not corner cleanup',title,label,maximum,float(dist.max())))
   mesh.v=[tuple(p) for p in points+correction[:,None]*M[1,:]];corner_adjustments[label]=maximum
  rv=Rotation.from_matrix(R).as_rotvec();qv=Rotation.from_matrix(Q@R).as_rotvec();states=[];wheelstates=[];lowerstates=[]
  ar=Rotation.from_matrix(align(d,target-pivot)).as_rotvec();roll=0. if nose else float(result.x[2])
  def leg_pose(fold):
   A=Rotation.from_rotvec(ar*fold).as_matrix();axis=A@d;axis/=np.linalg.norm(axis);A=Rotation.from_rotvec(axis*roll*fold).as_matrix()@A;return A,pivot-A@pivot
  for g in np.linspace(0,1,101):
   fold=1-np.clip((g-.24)/.76,0,1);A,t=leg_pose(fold);B=Rotation.from_rotvec(qv*fold).as_matrix();u=A@axle+t-A@d*compression*fold/length
   states.append(sta(A,t));lowerstates.append(sta(A,t-A@d*compression*fold/length));wheelstates.append(sta(B,u-B@axle))
  double(leg);add('Gear'+title,leg,210,states)
  if nose:
   root_link=Mesh();root_link.tube(tuple(pivot),tuple(cv(source.skeleton[b]['position'])),.055,(146,166,180),12);add('NoseUpperTrunnion',root_link,210,states)
  if lower.f:double(lower);add('GearLower'+title,lower,210,lowerstates)
  double(wheel);add('Wheels'+title,wheel,210,wheelstates)
  if not nose:
   trunnion=Mesh();trunnion.tube(tuple(pivot),tuple(cv(source.skeleton[b]['position'])),.065,(146,166,180),12);add('MainUpperTrunnion'+title,trunnion,210,states)
   # Articulated drag strut replaces the baked, disconnected source brace.
   base=cv([(-1 if title=='L' else 1)*2.46,-3.75,.50]);base[1]=.08;attach=cv([(-1 if title=='L' else 1)*2.46,-2.85,-.65]);transforms=[];distances=[]
   for g in np.linspace(0,1,101):
    fold=1-np.clip((g-.24)/.76,0,1);A,t=leg_pose(fold);tip=A@(attach-d*compression*fold/length)+t;transforms.append((base,tip));distances.append(np.linalg.norm(tip-base))
   length=max(distances)*.515;links=[[],[]]
   def knee_at(base,tip,angle):
    delta=tip-base;distance=np.linalg.norm(delta);side=np.cross(delta,[0.,1,0]);side/=np.linalg.norm(side)
    if side[0]*sign>0:side=-side
    up=np.cross(delta/distance,side)
    if up[1]<0:up=-up
    return (base+tip)/2+(side*math.cos(angle)+up*math.sin(angle))*math.sqrt(max(0,length*length-distance*distance/4))
   base0,tip0=transforms[0]
   def knee_cost(angle):
    k=knee_at(base0,tip0,angle);q=np.concatenate([base0+(k-base0)*f for f in np.linspace(0,1,61)]+[k+(tip0-k)*f for f in np.linspace(0,1,61)]).reshape(-1,3);lo,hi,_=env.bounds(q);return float(np.maximum(lo+.045-q[:,1],0).dot(np.maximum(lo+.045-q[:,1],0))+np.maximum(q[:,1]+.045-np.minimum(hi,.40),0).dot(np.maximum(q[:,1]+.045-np.minimum(hi,.40),0))+1e-7*angle*angle)
   angles=np.linspace(0,math.pi/2,91);closed_angle=min(angles,key=knee_cost)
   for index,(base,tip) in enumerate(transforms):
    g=index/100;fold=1-np.clip((g-.24)/.76,0,1);knee=knee_at(base,tip,closed_angle*fold)
    for j,(a,z) in enumerate([(base,knee),(knee,tip)]):links[j].append(sta(align([0,0,1],z-a),a))
   for j in [0,1]:
    link=Mesh();link.tube((0,0,0),(0,0,length),.024,(153,171,184),10);add('MainDragBrace'+title+str(j),link,210,links[j])
  else:
   # A short moving trunnion joins the raised internal hinge to the source cylinder.
   trunnion=Mesh();trunnion.tube(tuple(pivot),tuple(cv(source.skeleton[b]['position'])),.070,(146,166,180),12);add('NoseUpperTrunnion',trunnion,210,states)
  # Nose landing lamps follow the source leg.
  if nose:
   for b in [39,40]:double(meshes[b]);add('LandingLamp'+str(b),meshes[b],210,states)
  rect=(-.47,.47,1.20,4.38) if nose else (1.10,2.75,-3.95,1.05) if sign>0 else (-2.75,-1.10,-3.95,1.05)
  storage=rect;rect={'N':(-.41,.41,1.28,4.30),'L':(.85,2.38,-3.25,.65),'R':(-2.38,-.85,-3.25,.65)}[title]
  bays.append((title,rect,storage));report[title]={'fit_error_m':error,'root':pivot.tolist(),'axle_down':axle.tolist(),'stowed_target':target.tolist(),'compression':compression,'optimizer':result.fun,'corner_adjustments_m':corner_adjustments,'rect':rect}
  print('SU34 gear',title,report[title],flush=True)
 # Genuine lower skin cutouts with only recessed walls; doors use source skin profile.
 from shapely.geometry import Polygon,box
 from shapely import constrained_delaunay_triangles
 for title,rect,storage in bays:
  x0,x1,z0,z1=rect;cap=.98 if title=='N' else .40;new=Mesh()
  for ids,col,bright in hull.f:
   poly=[hull.v[i] for i in ids];n=normal(poly);center=np.mean(poly,0);bottom_at,top_at,_=env.bounds(center.reshape(1,3));top=top_at[0]
   if title!='N' and abs(n[1])>.30 and center[1]>bottom_at[0]+.05 and center[1]<top-.05:
    inside=poly; sx0,sx1,sz0,sz1=storage
    for ax,k,pos in [(0,sx0,True),(0,sx1,False),(2,sz0,True),(2,sz1,False),(1,cap,False)]:
     outside=clip(inside,ax,k,not pos) if len(inside)>=3 else []
     if len(outside)>=3:new.face(outside,col,bright)
     inside=clip(inside,ax,k,pos) if len(inside)>=3 else []
    continue
   if n[1]>.2 and abs(center[1]-top)<.05:new.face(poly,col,bright);continue
   inside=poly
   for ax,k,pos in [(0,x0,True),(0,x1,False),(2,z0,True),(2,z1,False),(1,cap,False)]:
    outside=clip(inside,ax,k,not pos) if len(inside)>=3 else []
    if len(outside)>=3:new.face(outside,col,bright)
    inside=clip(inside,ax,k,pos) if len(inside)>=3 else []
  hull.v,hull.f=new.v,new.f
  def bottom(x,z):return float(env.bounds(np.array([[x,0,z]]))[0][0])
  def ceiling(x,z):return min(float(env.bounds(np.array([[x,0,z]]))[1][0])-.018,cap)
  shape=env.footprint.intersection(box(x0,z0,x1,z1)).buffer(-.010);well=Mesh();mid=(x0+x1)/2
  def polys(g):return list(g.geoms) if hasattr(g,'geoms') else [g]
  leaves=([(x0,x1,x1,1)] if title=='L' else [(x0,x1,x0,-1)]) if title!='N' else [(x0,mid,x0,-1),(mid,x1,x1,1)]
  for idx,(lo,hi,hx,sg) in enumerate(leaves):
   leafarea=shape.intersection(box(lo,z0,hi,z1)).buffer(-.002)
   door=make_panel(env,leafarea,(135,167,180),(64,80,91))
   p=np.array([hx,bottom(hx,z0),z0]);end=np.array([hx,bottom(hx,z1),z1]);axis=end-p;axis/=np.linalg.norm(axis)
   states=[sta(*rotate(axis,p,sg*96*min(g/.20,1))) for g in np.linspace(0,1,101)]
   add('FlushDoor'+title+str(idx),door,210,states)
  well=make_well(env,rect,storage,cap);double(well);add('InternalWell'+title,well)
 # Su-34 cockpit glazing is fixed. No fictional hinged canopy or entry animation.
 report['validation']='NOT YET VALIDATED; fit diagnostics must pass before handoff'
 return report
