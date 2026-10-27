"""Test 2: connected landing-gear rig, genuine bays, dorsal brake and tip launchers."""
import math,copy
import numpy as np
from scipy.spatial.transform import Rotation
from mesh import Mesh
from gear_v3 import clip
from fit_internal import reference,fit

def axis_rotation(a,b):
 a=np.array(a,float);b=np.array(b,float);a/=np.linalg.norm(a);b/=np.linalg.norm(b)
 cross=np.cross(a,b);c=np.clip(a@b,-1,1)
 if np.linalg.norm(cross)<1e-9:return np.eye(3) if c>0 else Rotation.from_rotvec(np.array([0.,0,math.pi])).as_matrix()
 return Rotation.from_rotvec(cross/np.linalg.norm(cross)*math.acos(c)).as_matrix()

def construct(kind,ac,sta):
 su=kind=='su27';objects={o['name']:o for o in ac.objects};rig={};info={};bays=[];main_up_positive=None;env=reference(ac,su)
 for title,sign in [('N',0),('L',1),('R',-1)]:
  if su:
   pivot=np.array([sign*1.63,-.06,-3.37]) if sign else np.array([0.,.26,2.34])
   axle=np.array([sign*2.185,-1.995,-3.62]) if sign else np.array([0.,-1.98,2.20])
   target=np.array([sign*1.50,-.10,0.]) if sign else np.array([0.,0.,0.]);direction=1
   rect=(.35,2.42,-4.05,-.55) if sign>0 else (-2.42,-.35,-4.05,-.55) if sign<0 else (-.36,.36,1.88,5.10)
   door=-.58 if sign else -.43;roof=.40 if sign else .52
   names=[n for n in objects if n.startswith('UC_Main_'+('Left' if sign>0 else 'Right'))] if sign else [n for n in objects if n.startswith('UC_Nose_') and n not in ['UC_Nose_Rear_Post','UC_Nose_Upright_Brace','UC_Nose_BSArm']]
  else:
   pivot=np.array([sign*1.348,.070,-2.09]) if sign else np.array([0.,.029,2.135])
   axle=np.array([sign*1.61,-1.30,-1.80]) if sign else np.array([0.,-1.425,1.74])
   target=np.array([sign*1.32,-.12,0.]) if sign else np.array([0.,.05,0.]);direction=1 if sign else -1
   rect=(.52,1.98,-2.52,.16) if sign>0 else (-1.98,-.52,-2.52,.16) if sign<0 else (-.35,.35,.04,3.36)
   door=-.40 if sign else -.34;roof=.40 if sign else .42
   names=['gear1.'+('L' if sign>0 else 'R'),'gear2.'+('L' if sign>0 else 'R'),'wheel.'+('L' if sign>0 else 'R')] if sign else ['nosegear1','nosegear2','nosewheels','WheelGuard']
  up,W,target,fitinfo=fit(kind,title,pivot,axle,names,objects,env)
  rv=Rotation.from_matrix(up).as_rotvec();wheelrv=Rotation.from_matrix(W).as_rotvec()
  legstates=[];wheelstates=[];lowerstates=[];matrices=[]
  for g in np.linspace(0,1,21):
   down=np.clip((g-.24)/.76,0,1);fold=1-down;R=Rotation.from_rotvec(rv*fold).as_matrix();t=pivot-R@pivot;center=R@axle+t
   comp=fitinfo['compression']*fold if su and not sign else 0.;C=(pivot-axle)/np.linalg.norm(pivot-axle)*comp
   W=Rotation.from_rotvec(wheelrv*fold).as_matrix();Q=W@R;u=center+W@(t+R@C-center)
   legstates.append(sta(R,t));lowerstates.append(sta(R,t+R@C));wheelstates.append(sta(Q,u));matrices.append((R,t,Q,u))
  info[title]={'root':pivot.tolist(),'axle_down':axle.tolist(),'axle_stowed':target.tolist(),'fit_to_original_skin':fitinfo,'fixed_hinge':True,'wheel_swivel':bool(sign),'rect':rect,'door_y':door,'roof_y':roof}
  for name in names:rig[name]={'states':wheelstates if ('Tyre' in name or name.startswith('wheel.')) else legstates,'title':title,'wheel_states':wheelstates,'leg_states':lowerstates if su and not sign and name not in ['UC_Nose_Upper_Strut','UC_Nose_LLights'] else legstates,'matrices':matrices,'axle':axle,'pivot':pivot}
  bays.append((title,rect,door,roof,legstates,wheelstates,matrices,env))
 return rig,info,bays

def kind_of_rig(rig):return 'su27' if any(n.startswith('UC_') for n in rig) else 'mig29'

def add_gears(ac,rig,add,double,sta):
 for o in ac.objects:
  n=o['name']
  if n not in rig:continue
  v=np.array(o['v']);parts={'leg':Mesh(),'wheel':Mesh()};r=rig[n]
  for f in o['f']:
   if len(f)<3:continue
   q=v[f];wheel='Tyre' in n or n.startswith('wheel.')
   if n.startswith('UC_Main_') and n.endswith('Hub'):wheel=q[:,1].mean()<r['axle'][1]+.40
   col=(32,36,40) if 'Tyre' in n or n.startswith('wheel.') or n=='nosewheels' else (164,176,184)
   parts['wheel' if wheel else 'leg'].face([tuple(x) for x in q],col)
  for sub,m in parts.items():
   if not m.f:continue
   states=r['wheel_states'] if sub=='wheel' and r['title']!='N' else r['leg_states'];double(m);add('Gear_'+n+'_'+sub,m,210,states)
 # Visible hinge links connect source upper struts to the fixed fuselage trunnions.
 hinges=Mesh()
 for title in ['L','R']:
  r=next(v for v in rig.values() if v['title']==title);p=r['pivot'];hinges.tube(tuple(p+np.array([-.11,0,0])),tuple(p+np.array([.11,0,0])),.085,(103,119,132),12)
  if kind_of_rig(rig)=='su27':
   sign=1 if title=='L' else -1;link=Mesh();link.tube(tuple(p),(sign*1.90,-.04,-3.70),.059,(152,168,180),12);add('UpperHingeLink'+title,link,210,r['leg_states'])
 add('FixedGearTrunnions',hinges)
 # Articulated nose drag brace: two rigid links share one solved knee joint.
 if kind_of_rig(rig)=='su27':
  r=next(v for v in rig.values() if v['title']=='N');base=np.array([0.,.30,1.98]);attachment=np.array([0.,-.60,2.25]);length=.56;poses=[[],[]]
  for R,t,Q,u in r['matrices']:
   tip=Q@attachment+u;delta=tip-base;distance=np.linalg.norm(delta);assert distance<2*length
   perp=np.array([0.,delta[2],-delta[1]]);perp/=np.linalg.norm(perp)
   if perp[1]<0:perp=-perp
   knee=(base+tip)/2+perp*math.sqrt(length*length-distance*distance/4)
   for i,(a,b) in enumerate([(base,knee),(knee,tip)]):poses[i].append(sta(axis_rotation([0,0,1],b-a),a))
  for i in [0,1]:
   brace=Mesh();brace.tube((0,0,0),(0,0,length),.025,(150,167,179),10);add('NoseDragBrace'+str(i),brace,210,poses[i])
 # Two torque links share an IK knee as the nose oleo telescopes internally.
 if kind_of_rig(rig)=='su27':
  r=next(v for v in rig.values() if v['title']=='N');upper=np.array([0.,-1.00,2.33]);lower=np.array([0.,-1.50,2.30]);length=.31;poses=[[],[]]
  for R,t,Q,u in r['matrices']:
   a=R@upper+t;b=Q@lower+u;delta=b-a;distance=np.linalg.norm(delta);assert distance<2*length
   side=np.cross(delta,[0,1,0]);side=side/np.linalg.norm(side) if np.linalg.norm(side)>1e-8 else np.array([1.,0,0])
   if side[0]<0:side=-side
   knee=(a+b)/2+side*math.sqrt(length*length-distance*distance/4)
   for i,(start,end) in enumerate([(a,knee),(knee,b)]):poses[i].append(sta(axis_rotation([0,0,1],end-start),start))
  for i in [0,1]:
   m=Mesh();m.tube((0,0,0),(0,0,length),.017,(151,169,181),8);add('NoseTorqueLink'+str(i),m,210,poses[i])
 # Short clevis tubes keep the swivel fork attached at the exact axle pivot.
 for title in ['L','R']:
  candidates=[r for n,r in rig.items() if r['title']==title];r=candidates[0];a=r['axle'];up=a+np.array([0,.50,0]);m=Mesh();m.tube(tuple(up),tuple(a),.038,(172,185,192),12);add('AxleFork'+title,m,210,r['leg_states'])

def clip_box_skin(m,rect,ceiling):
 """Cut bottom and side skins inside a bay volume, retain the upper aircraft skin."""
 x0,x1,z0,z1=rect;out=Mesh()
 for ids,c,b in m.f:
  poly=[m.v[i] for i in ids]
  if max(p[0] for p in poly)<=x0 or min(p[0] for p in poly)>=x1 or max(p[2] for p in poly)<=z0 or min(p[2] for p in poly)>=z1 or min(p[1] for p in poly)>=ceiling:
   out.face(poly,c,b);continue
  inside=poly
  for ax,t,pos in [(0,x0,True),(0,x1,False),(2,z0,True),(2,z1,False),(1,ceiling,False)]:
   exterior=clip(inside,ax,t,not pos) if len(inside)>=3 else []
   if len(exterior)>=3:out.face(exterior,c,b)
   inside=clip(inside,ax,t,pos) if len(inside)>=3 else []
 m.v,m.f=out.v,out.f

def sample(m,x,z,upper=False):
 hits=[]
 for f,col,b in m.f:
  q=np.array([m.v[i] for i in f])
  for k in range(1,len(q)-1):
   a,bb,c=q[0],q[k],q[k+1];A=np.array([[a[0]-c[0],bb[0]-c[0]],[a[2]-c[2],bb[2]-c[2]]]);det=np.linalg.det(A)
   if abs(det)<1e-10:continue
   u,v=np.linalg.solve(A,[x-c[0],z-c[2]])
   if min(u,v,1-u-v)>-1e-5:hits.append(u*a[1]+v*bb[1]+(1-u-v)*c[1])
 return (max(hits) if upper else min(hits)) if hits else None

def add_bays(hull,bays,add,double,sta,kind):
 from gear_v3 import normal
 from shapely.geometry import Polygon,box
 from shapely import constrained_delaunay_triangles
 report={};su=kind=='su27'
 for entry in bays:
  title,rect=entry[:2];env=entry[-1];x0,x1,z0,z1=rect;roofcap=(.715 if su else .60) if title=='N' else .47
  # Remove the original lower skin inside the aperture, including old shallow liners.
  # Upper skin is retained; no external housing or enlarged bounding box is added.
  out=Mesh()
  for ids,col,bright in hull.f:
   poly=[hull.v[i] for i in ids];n=normal(poly)
   center=np.array(poly).mean(0);outer_top=float(env.bounds(center.reshape(1,3))[1][0]);upper_exterior=n[1]>.18 and abs(center[1]-outer_top)<.05
   if upper_exterior or min(v[1] for v in poly)>roofcap or max(v[0] for v in poly)<=x0 or min(v[0] for v in poly)>=x1 or max(v[2] for v in poly)<=z0 or min(v[2] for v in poly)>=z1:
    out.face(poly,col,bright);continue
   inside=poly
   for ax,t,pos in [(0,x0,True),(0,x1,False),(2,z0,True),(2,z1,False),(1,roofcap,False)]:
    exterior=clip(inside,ax,t,not pos) if len(inside)>=3 else []
    if len(exterior)>=3:out.face(exterior,col,bright)
    inside=clip(inside,ax,t,pos) if len(inside)>=3 else []
  hull.v,hull.f=out.v,out.f
  def bottom(x,z):return float(env.bounds(np.array([[x,0,z]]))[0][0])
  def top(x,z):return min(float(env.bounds(np.array([[x,0,z]]))[1][0])-.012,roofcap)
  footprint=env.footprint.intersection(box(x0,z0,x1,z1))
  def parts(g):return list(g.geoms) if hasattr(g,'geoms') else [g]
  def triangles(g):
   return [list(t.exterior.coords)[:-1] for poly in parts(g) if isinstance(poly,Polygon) and poly.area>1e-10 for t in constrained_delaunay_triangles(poly).geoms]
  # Curved doors reproduce the source's own lower contour, instead of flat boxes.
  mid=(x0+x1)/2;leaves=[(x0,mid,x0,-1),(mid,x1,x1,1)];well=Mesh();nx=12;nz=24
  for j,(lo,hi,hx,sign) in enumerate(leaves):
   m=Mesh()
   for i in range(nx):
    for k in range(nz):
     xa=lo+(hi-lo)*i/nx;xb=lo+(hi-lo)*(i+1)/nx;za=z0+(z1-z0)*k/nz;zb=z0+(z1-z0)*(k+1)/nz
     patch=footprint.intersection(box(xa,za,xb,zb))
     for tri in triangles(patch):
      q=[(x,bottom(x,z),z) for x,z in tri];m.face(q,(100,127,147) if su else (106,128,127));m.face([(x,y+.012,z) for x,y,z in q[::-1]],(63,76,84))
   leafarea=footprint.intersection(box(lo,z0,hi,z1))
   hinge=[]
   for poly in parts(leafarea):
    if not isinstance(poly,Polygon):continue
    outline=list(poly.exterior.coords)
    hinge.extend([(x,z) for x,z in outline if abs(x-hx)<1e-5])
    for a,b in zip(outline,outline[1:]):
     a=np.array(a);b=np.array(b)
     for k in range(12):
      aa=a+(b-a)*k/12;bb=a+(b-a)*(k+1)/12;ya=bottom(*aa);yb=bottom(*bb);m.face([(aa[0],ya,aa[1]),(bb[0],yb,bb[1]),(bb[0],yb+.012,bb[1]),(aa[0],ya+.012,aa[1])],(90,110,127))
   hz0=min((z for x,z in hinge),default=z0);hz1=max((z for x,z in hinge),default=z1)
   p=np.array([hx,bottom(hx,hz0),hz0]);end=np.array([hx,bottom(hx,hz1),hz1]);axis=end-p;axis/=np.linalg.norm(axis);states=[]
   for g in np.linspace(0,1,21):
    R=Rotation.from_rotvec(axis*sign*math.radians(97)*min(g/.20,1)).as_matrix();states.append(sta(R,p-R@p))
   add('FlushGearDoor'+title+str(j),m,210,states)
  # Interior walls begin exactly at the cut skin and run inward to a roof
  # constrained to remain beneath the original upper envelope.
  for poly in parts(footprint):
   if not isinstance(poly,Polygon):continue
   outline=list(poly.exterior.coords)
   for aa,bb in zip(outline,outline[1:]):
    aa=np.array(aa);bb=np.array(bb)
    for k in range(8):
     a=aa+(bb-aa)*k/8;b=aa+(bb-aa)*(k+1)/8
     q=[(a[0],bottom(*a),a[1]),(b[0],bottom(*b),b[1]),(b[0],top(*b),b[1]),(a[0],top(*a),a[1])];well.face(q,(40,49,56))
  for i in range(16):
   for k in range(24):
    xa=x0+(x1-x0)*i/16;xb=x0+(x1-x0)*(i+1)/16;za=z0+(z1-z0)*k/24;zb=z0+(z1-z0)*(k+1)/24
    for tri in triangles(footprint.intersection(box(xa,za,xb,zb))):well.face([(x,top(x,z),z) for x,z in tri],(35,44,50))
  double(well);add('InternalGearBay'+title,well)
  report[title]={'rect':rect,'source_skin_contour':True,'external_box':False,'interior_roof_cap':roofcap,'doors_before_legs':True}
 return report

def add_brake(m,add,double,sta):
 # Keep the source contour but shorten its rear reach and broaden it slightly.
 q=np.array(m.v);pivot=np.array([0.,1.176,1.05]);q[:,2]=pivot[2]+(q[:,2]-pivot[2])*.71;q[:,0]*=1.18;m.v=[tuple(p) for p in q]
 R=Rotation.from_rotvec([math.radians(45),0,0]).as_matrix();double(m);add('DorsalBrake',m,212,[sta(),sta(R,pivot-R@pivot)])
 topz=-.12;top_y=sample(m,0,topz);top0=np.array([0.,(top_y if top_y is not None else 1.05)-.018,topz]);base=np.array([0.,.25,-.85]);maxd=0;mind=99;poses=[[],[]]
 distances=[]
 for f in np.linspace(0,1,21):
  R=Rotation.from_rotvec([math.radians(45)*f,0,0]).as_matrix();top=pivot+R@(top0-pivot);d=top-base;length=np.linalg.norm(d);distances.append(length)
 # Each section is shorter than the closed spacing and together cover the open spacing.
 tube_length=max(distances)*.52;assert tube_length<min(distances)+.03,(min(distances),max(distances))
 for f in np.linspace(0,1,21):
  R=Rotation.from_rotvec([math.radians(45)*f,0,0]).as_matrix();top=pivot+R@(top0-pivot);d=top-base;d/=np.linalg.norm(d);A=axis_rotation([0,0,1],d)
  poses[0].append(sta(A,base,1 if f>.025 else 0));poses[1].append(sta(A,top-d*tube_length,1 if f>.025 else 0))
 for i in [0,1]:
  rod=Mesh();rod.tube((0,0,0),(0,0,tube_length),.036 if not i else .022,(85,99,110) if not i else (178,190,198),12);add('CompactBrakeDrive'+str(i),rod,214,poses[i])
 return {'panel_length':float(np.ptp(q[:,2])),'panel_width':float(np.ptp(q[:,0])),'cylinder_segment':tube_length,'anchor_distance_range':[min(distances),max(distances)],'base':base.tolist(),'moving_attachment':top0.tolist()}

def add_tip_launchers(add):
 m=Mesh()
 for s in [-1,1]:
  # Lateral bracket touches the original tip rail; weapon centre clears the wing.
  for z in [-6.85,-6.25]:m.box(s*7.71,.34,z,.52,.11,.14,(114,139,157))
  m.box(s*7.90,.34,-6.35,.14,.13,2.05,(101,124,141));m.box(s*7.98,.34,-6.35,.055,.085,2.15,(161,177,186))
 add('WingtipSideLaunchers',m)
 return [(8.04,.34,-6.35),(-8.04,.34,-6.35)]
