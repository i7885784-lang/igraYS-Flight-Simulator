import numpy as np,collections,math,copy
import shapely
from scipy.spatial import cKDTree
from shapely.geometry import Polygon,box
from common import *

def bevel(x0,z0,x1,z1,d):
 d=min(d,(x1-x0)*.25,(z1-z0)*.25)
 return Polygon([(x0+d,z0),(x1-d,z0),(x1,z0+d),(x1,z1-d),(x1-d,z1),(x0+d,z1),(x0,z1-d),(x0,z0+d)])

def leaf_shape(x0,z0,x1,z1,d,main):
 if main:return bevel(x0,z0,x1,z1,d)
 # Only body-side corners are rounded. The centre meeting edge stays straight,
 # so there are no stationary triangular islands in the open compartment.
 if x1<=1e-6:return Polygon([(x0+d,z0),(x1,z0),(x1,z1),(x0+d,z1),(x0,z1-d),(x0,z0+d)])
 return Polygon([(x0,z0),(x1-d,z0),(x1,z0+d),(x1,z1-d),(x1-d,z1),(x0,z1)])

def real_frame(main,right):
 if main:
  return box(2.38,-3.40,2.42,-.39).union(box(1.84,-3.40,2.42,-3.36)).union(box(1.84,-.43,2.42,-.39)) if right else box(-2.42,-3.40,-2.38,-.39).union(box(-2.42,-3.40,-1.84,-3.36)).union(box(-2.42,-.43,-1.84,-.39))
 return box(-.4,1.97,-.362,4.47).union(box(.362,1.97,.4,4.47)).union(box(-.4,1.97,.4,2.01)).union(box(-.4,4.43,.4,4.47))

def hinge_slots(strip,x0,x1,main,aft=False):
 edge=x0 if x1<=0 else x1
 for z in ([-3.03,-1.05] if main else ([2.22,2.86] if aft else [3.32,3.93])):
  strip=strip.difference(box(edge-.021,z-.045,edge+.021,z+.045))
 return strip

def exterior(p,n):
 m=dnm.mesh(p[dnm.fil(n)]);R,C=transform(n,0);v=np.array(m.v)@R.T+C;out=[];seen=set()
 for ids,color,b in m.f:
  if color in [(98,113,121),(104,120,130)]:continue
  for k in range(1,len(ids)-1):
   q=v[[ids[0],ids[k],ids[k+1]]];normal=np.cross(q[1]-q[0],q[2]-q[0]);key=tuple(sorted(tuple(np.round(t,6)) for t in q))
   if normal[1]>=-1e-10 or key in seen:continue
   seen.add(key);out.append((q,color))
 return out

def clipped_surface(triangles,domain):
 out=[]
 for q,color in triangles:
  poly=Polygon(q[:,[0,2]]);cut=poly.intersection(domain)
  if cut.is_empty:continue
  coeff=np.linalg.solve(np.c_[q[:,0],q[:,2],np.ones(3)],q[:,1])
  for shape in ([cut] if cut.geom_type=='Polygon' else getattr(cut,'geoms',[])):
   if shape.geom_type!='Polygon' or shape.area<1e-12:continue
   pts=np.array(shape.exterior.coords)[:-1]
   pieces=[pts[[0,j,j+1]] for j in range(1,len(pts)-1)] if not len(shape.interiors) and abs(shape.convex_hull.area-shape.area)<1e-12 else [np.array(t.exterior.coords)[:3] for t in shapely.get_parts(shapely.constrained_delaunay_triangles(shape))]
   for xy in pieces:
    t=np.round(np.c_[xy[:,0],np.c_[xy,np.ones(3)]@coeff,xy[:,1]],6)
    if np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))<1e-10:continue
    if np.cross(t[1]-t[0],t[2]-t[0])[1]>0:t=t[::-1]
    out.append((t,color))
 return out

def fit_fore_seam(surface,measured):
 # Both halves of the extended front panel use one measured boundary at Z4.16.
 xs=sorted({round(float(v[0]),6) for tri,c in surface for v in tri if abs(v[2]-4.16)<2e-6})
 def point(x):
  candidates=[]
  for q,color in measured:
   a=q[0];u=q[1]-a;v=q[2]-a;det=u[0]*v[2]-u[2]*v[0]
   if abs(det)<1e-12:continue
   b=((x-a[0])*v[2]-(4.16-a[2])*v[0])/det;c=(u[0]*(4.16-a[2])-u[2]*(x-a[0]))/det
   if b>=-2e-5 and c>=-2e-5 and b+c<=1.00002:candidates.append(float(a[1]+b*u[1]+c*v[1]))
  assert candidates, ('Unsupported measured front seam',x)
  return np.round([x,min(candidates),4.16],6)
 cache={x:point(x) for x in xs};out=[]
 for tri,color in surface:
  q=np.array([cache[round(float(v[0]),6)] if abs(v[2]-4.16)<2e-6 else v for v in tri]);edge=next(((i,j,k) for i,j,k in [(0,1,2),(1,2,0),(2,0,1)] if abs(q[i,2]-4.16)<1e-6 and abs(q[j,2]-4.16)<1e-6),None)
  if edge is None:out.append((q,color));continue
  i,j,k=edge;lo,hi=sorted([q[i,0],q[j,0]]);points=[cache[x] for x in xs if lo-1e-7<=x<=hi+1e-7]
  if q[i,0]>q[j,0]:points=points[::-1]
  for a,b in zip(points,points[1:]):
   t=np.array([q[k],a,b]);n=np.cross(t[1]-t[0],t[2]-t[0])
   if abs(n[1])<1e-12:continue
   if n[1]>0:t=t[::-1]
   out.append((t,color))
 return out

def weld_surface(surface):
 points=np.concatenate([q for q,c in surface]);v,inv=np.unique(np.round(points,6),axis=0,return_inverse=True);parent=list(range(len(v)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for a,b in sorted(cKDTree(v).query_pairs(3e-6)):
  a,b=root(a),root(b)
  if a!=b:parent[max(a,b)]=min(a,b)
 groups=collections.defaultdict(list)
 for i in range(len(v)):groups[root(i)].append(i)
 reps={k:min(ids,key=lambda i:(v[i,1],v[i,0],v[i,2])) for k,ids in groups.items()};mapped=np.array([v[reps[root(int(i))]] for i in inv]);out=[];seen=set()
 for j,(q,color) in enumerate(surface):
  t=mapped[j*3:j*3+3];n=np.cross(t[1]-t[0],t[2]-t[0]);key=tuple(sorted(tuple(a) for a in t))
  if abs(n[1])<1e-12 or np.linalg.norm(n)<2e-12 or key in seen:continue
  seen.add(key)
  if n[1]>0:t=t[::-1]
  out.append((t,color))
 return out

def conform_surface(surface):
 # Convex subtraction can leave partial shared edges between its pieces.
 # Split every incident face on the SAME existing vertices before making rims.
 points=np.concatenate([q for q,c in surface]);v,inv=np.unique(np.round(points,6),axis=0,return_inverse=True);faces=inv.reshape(-1,3);tree=cKDTree(v);split={}
 for ids in faces:
  for a,b in zip(ids,np.roll(ids,-1)):
   key=tuple(sorted((int(a),int(b))))
   if key in split:continue
   A,B=v[list(key)];d=B-A;l2=float(d@d)
   if abs(A[2]+1.23)>1e-7 or abs(B[2]+1.23)>1e-7 or abs(d[0])<1e-9:split[key]=list(key);continue
   if l2<1e-18:split[key]=list(key);continue
   nearby=np.array(tree.query_ball_point((A+B)/2,math.sqrt(l2)/2+2e-6),int);t=(v[nearby]-A)@d/l2;dist=np.linalg.norm(v[nearby]-A-t[:,None]*d,axis=1);tx=(v[nearby,0]-A[0])/d[0];inside=nearby[(tx>1e-6)&(tx<1-1e-6)&(dist<2e-6)&(abs(v[nearby,2]+1.23)<1e-7)];byx={}
   for i in inside:
    x=float(v[i,0]);oldi=byx.get(x)
    if oldi is None or np.linalg.norm(np.cross(v[i]-A,d))<np.linalg.norm(np.cross(v[oldi]-A,d)):byx[x]=int(i)
   inside=list(byx.values());seq=[key[0],*sorted(set(map(int,inside)),key=lambda i:float((v[i]-A)@d)),key[1]];split[key]=seq
 out=[]
 for ids,(q,color) in zip(faces,surface):
  boundary=[];changed=False
  for a,b in zip(ids,np.roll(ids,-1)):
   key=tuple(sorted((int(a),int(b))));seq=split[key]
   if int(a)!=key[0]:seq=seq[::-1]
   boundary+=seq[:-1];changed|=len(seq)>2
  if not changed:out.append((q,color));continue
  poly=Polygon(v[boundary][:,[0,2]]);assert poly.is_valid and poly.area>1e-14
  lookup={tuple(v[i][[0,2]]):v[i] for i in boundary}
  for tri in shapely.get_parts(shapely.constrained_delaunay_triangles(poly)):
   xy=np.array(tri.exterior.coords)[:3];t=np.array([lookup[tuple(a)] for a in xy]);n=np.cross(t[1]-t[0],t[2]-t[0])
   if abs(n[1])<1e-12:continue
   if n[1]>0:t=t[::-1]
   out.append((t,color))
 return out

def panel(surface,R,C,thick=.008,conform=False):
 surface=weld_surface(surface)
 if conform:surface=conform_surface(surface)
 m=Mesh();edges=collections.Counter();oriented={}
 for q,color in surface:
  m.face((q-C)@R,color);m.face((q[::-1]+[0,thick,0]-C)@R,(148,153,148))
  for a,b in zip(q,np.roll(q,-1,axis=0)):
   a,b=tuple(a),tuple(b);key=tuple(sorted((a,b)));edges[key]+=1;oriented[key]=(a,b)
 for key,count in edges.items():
  if count!=1:continue
  a,b=map(np.array,oriented[key]);quad=np.array([b,a,a+[0,thick,0],b+[0,thick,0]]);m.face((quad-C)@R,(105,118,123))
 return m

def repair_doors(p,ns,lu,audit,remove_drop=False,fore_source=()):
 names=['GearDoor_Left_Inner','GearDoor_Right_Outer','GearDoor_Nose_Inner','GearDoor_Nose_Outer','GearDoor_Nose_Aft'];source={name:exterior(p,lu[name]) for name in names}
 for title,domain in [('Inner',box(-.38,4.16,0,4.45)),('Outer',box(0,4.16,.38,4.45))]:source['GearDoor_Nose_'+title]+=clipped_surface(fore_source,domain)
 for name in ['GearDoor_Nose_Inner','GearDoor_Nose_Outer']:source[name]=fit_fore_seam(source[name],fore_source)
 for name in names:
  n=lu[name];tri=source[name];allv=np.concatenate([q for q,c in tri]);lo,hi=allv.min(0),allv.max(0);x0,z0,x1,z1=lo[0],lo[2],hi[0],hi[2];main='Nose' not in name
  if name.endswith('Nose_Aft'):x1=0
  shape=leaf_shape(x0,z0,x1,z1,.055 if main else .025,main);moving=shape.buffer(-.002,join_style=2);R,C=transform(n,0);surf=clipped_surface(tri,moving);p[dnm.fil(n)]=panel(surf,R,C).srf();filler=Mesh();full=box(x0,z0,x1,z1)
  for q,color in clipped_surface(tri,full.difference(shape)):
   filler.face(q,color);filler.face(q[::-1],color)
  if filler.f:add(p,ns,'BayCornerSkin_'+name,filler)
  # The recess behind the running seam is formed from the same measured surface.
  strip=shape.difference(shape.buffer(-.014,join_style=2))
  strip=hinge_slots(strip.intersection(real_frame(main,x0>0)),x0,x1,main,'Aft' in name)
  seat=Mesh()
  for q,color in clipped_surface(tri,strip):seat.face(q+[0,.018,0],(119,132,134));seat.face((q+[0,.018,0])[::-1],(119,132,134))
  oldseat=lu['DoorSeat_'+name];p[dnm.fil(oldseat)]=seat.srf()
  if remove_drop:
   ki=0
   for i,line in enumerate(n):
    if not line.startswith('STA '):continue
    tokens=line.split();tokens[2]=str(round(float(tokens[2])+.07*min(1,(ki/100)/.015),7));n[i]=' '.join(tokens);ki+=1
  audit[name]={'actual_surface_triangles':len(surf),'running_seam_m':.002,'corner_chamfer_m':.055 if main else .025,'closed_bounds_before':[lo.tolist(),hi.tolist()],'source_surface_preserved':True,'removed_artificial_drop_7cm':remove_drop,'seating_only_on_physical_aperture_perimeter':True}
 # Replace the one full-width rear panel by two symmetric leaves sharing the already working left/right curves.
 old=lu['GearDoor_Nose_Aft'];right=lu['GearDoor_Nose_Outer'];tri=source['GearDoor_Nose_Aft'];allv=np.concatenate([q for q,c in tri]);lo,hi=allv.min(0),allv.max(0);shape=leaf_shape(0,lo[2],hi[0],hi[2],.025,False);R,C=transform(right,0);surf=clipped_surface(tri,shape.buffer(-.002,join_style=2));add(p,ns,'GearDoor_Nose_Aft_Right',panel(surf,R,C),210,[s for s in right if s.startswith('STA ')])
 corner=Mesh()
 for q,color in clipped_surface(tri,box(0,lo[2],hi[0],hi[2]).difference(shape)):corner.face(q,color);corner.face(q[::-1],color)
 if corner.f:add(p,ns,'BayCornerSkin_Nose_Aft_Right',corner)
 seat=lu['DoorSeat_GearDoor_Nose_Aft'];left=dnm.mesh(p[dnm.fil(seat)]);extra=Mesh()
 for q,c in clipped_surface(tri,hinge_slots(shape.difference(shape.buffer(-.014,join_style=2)).intersection(real_frame(False,True)),0,hi[0],False,True)):extra.face(q+[0,.018,0],(119,132,134));extra.face((q+[0,.018,0])[::-1],(119,132,134))
 left.merge(extra);p[dnm.fil(seat)]=left.srf();audit['nose_rear_pair']={'new_right_leaf_uses_unchanged_existing_right_door_curve':True,'existing_left_leaf_uses_existing_left_curve':True,'original_full_width_one_sided_panel_removed':True}
