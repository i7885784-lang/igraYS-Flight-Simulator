"""Test 2: connected landing-gear rig, genuine bays, dorsal brake and tip launchers."""
import math,copy
import numpy as np
from scipy.spatial.transform import Rotation
from mesh import Mesh
from gear_v3 import clip

def axis_rotation(a,b):
 a=np.array(a,float);b=np.array(b,float);a/=np.linalg.norm(a);b/=np.linalg.norm(b)
 cross=np.cross(a,b);c=np.clip(a@b,-1,1)
 if np.linalg.norm(cross)<1e-9:return np.eye(3) if c>0 else Rotation.from_rotvec(np.array([0.,0,math.pi])).as_matrix()
 return Rotation.from_rotvec(cross/np.linalg.norm(cross)*math.acos(c)).as_matrix()

def construct(kind,ac,sta):
 su=kind=='su27';objects={o['name']:o for o in ac.objects};rig={};info={};bays=[];main_up_positive=None
 for title,sign in [('N',0),('L',1),('R',-1)]:
  if su:
   pivot=np.array([sign*1.63,-.06,-3.37]) if sign else np.array([0.,.15,2.34])
   axle=np.array([sign*2.185,-1.995,-3.62]) if sign else np.array([0.,-1.98,2.20])
   target=np.array([sign*1.50,-.10,0.]) if sign else np.array([0.,0.,0.]);direction=1
   rect=(.83,2.42,-4.05,-.55) if sign>0 else (-2.42,-.83,-4.05,-.55) if sign<0 else (-.36,.36,1.88,5.10)
   door=-.58 if sign else -.43;roof=.40 if sign else .52
   names=[n for n in objects if n.startswith('UC_Main_'+('Left' if sign>0 else 'Right'))] if sign else [n for n in objects if n.startswith('UC_Nose_') and n!='UC_Nose_Rear_Post']
  else:
   pivot=np.array([sign*1.348,.070,-2.09]) if sign else np.array([0.,.029,2.135])
   axle=np.array([sign*1.61,-1.30,-1.80]) if sign else np.array([0.,-1.425,1.74])
   target=np.array([sign*1.32,-.12,0.]) if sign else np.array([0.,.05,0.]);direction=1 if sign else -1
   rect=(.73,1.98,-2.52,.16) if sign>0 else (-1.98,-.73,-2.52,.16) if sign<0 else (-.35,.35,.04,3.36)
   door=-.40 if sign else -.34;roof=.40 if sign else .42
   names=['gear1.'+('L' if sign>0 else 'R'),'gear2.'+('L' if sign>0 else 'R'),'wheel.'+('L' if sign>0 else 'R')] if sign else ['nosegear1','nosegear2','nosewheels','WheelGuard']
  d=axle-pivot
  length=np.linalg.norm(d);target[2]=pivot[2]+direction*math.sqrt(length**2-(target[0]-pivot[0])**2-(target[1]-pivot[1])**2)
  up=axis_rotation(d,target-pivot)
  if su and sign:
   raw=[]
   for name in names:
    if 'Tyre' in name:continue
    o=objects[name];v=np.array(o['v'])
    for f in o['f']:
     if name.endswith('Hub') and v[f,1].mean()<axle[1]+.40:continue
     raw.extend(v[f])
   raw=np.array(raw);axis=(target-pivot)/length;best=None
   for phi in np.linspace(-math.pi,math.pi,145):
    R=Rotation.from_rotvec(axis*phi).as_matrix()@up;q=(raw-pivot)@R.T+pivot;x0,x1,z0,z1=rect
    lo=np.array([x0+.015,door+.04,z0+.03]);hi=np.array([x1-.015,roof-.04,z1-.03]);cost=np.maximum(lo-q,0).sum()+np.maximum(q-hi,0).sum()+.001*abs(phi)
    if best is None or cost<best[0]:best=(cost,R)
   up=best[1]
   if sign>0:main_up_positive=up.copy()
   elif main_up_positive is not None:
    mirror=np.diag([-1.,1,1]);up=mirror@main_up_positive@mirror
  rv=Rotation.from_matrix(up).as_rotvec();wheelrv=Rotation.from_matrix(axis_rotation(up@np.array([1.,0,0]),[0,sign,0])).as_rotvec() if sign else np.zeros(3)
  legstates=[];wheelstates=[];matrices=[]
  for g in np.linspace(0,1,21):
   down=np.clip((g-.24)/.76,0,1);fold=1-down;R=Rotation.from_rotvec(rv*fold).as_matrix();t=pivot-R@pivot;center=R@axle+t
   W=Rotation.from_rotvec(wheelrv*fold).as_matrix();Q=W@R;u=center+W@(t-center)
   legstates.append(sta(R,t));wheelstates.append(sta(Q,u));matrices.append((R,t,Q,u))
  info[title]={'root':pivot.tolist(),'axle_down':axle.tolist(),'axle_stowed':target.tolist(),'fixed_hinge':True,'wheel_swivel':bool(sign),'rect':rect,'door_y':door,'roof_y':roof}
  for name in names:rig[name]={'states':wheelstates if ('Tyre' in name or name.startswith('wheel.')) else legstates,'title':title,'wheel_states':wheelstates,'leg_states':legstates,'matrices':matrices,'axle':axle,'pivot':pivot}
  bays.append((title,rect,door,roof,legstates,wheelstates,matrices))
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
 skin=copy.deepcopy(hull);report={};su=kind=='su27'
 for title,rect,bottom,roof,*_ in bays:
  x0,x1,z0,z1=rect;clip_box_skin(hull,rect,roof-.025);well=Mesh();outer=Mesh()
  # Roof and fully opaque recessed side walls, all ordinary sunlight materials.
  well.box((x0+x1)/2,roof+.018,(z0+z1)/2,x1-x0,.036,z1-z0,(35,44,51))
  sides=[((x0,bottom,z0),(x1,bottom,z0)),((x1,bottom,z0),(x1,bottom,z1)),((x1,bottom,z1),(x0,bottom,z1)),((x0,bottom,z1),(x0,bottom,z0))]
  for a,b in sides:
   poly=[a,b,(b[0],roof,b[2]),(a[0],roof,a[2])];well.face(poly,(55,66,74));well.face(poly[::-1],(119,151,175) if su else (122,147,145))
  for i,(f,c,b) in enumerate(well.f[:6]):
   if all(well.v[j][1]>roof+.02 for j in f):well.f[i]=(f,(119,151,175) if su else (122,147,145),b)
  add('BayWalls'+title,well)
  mid=(x0+x1)/2;halves=[(x0,mid,x0,-1),(mid,x1,x1,1)]
  for j,(lo,hi,pivx,sign) in enumerate(halves):
   m=Mesh();m.box((lo+hi)/2,bottom-.012,(z0+z1)/2,hi-lo,.024,z1-z0,(100,124,140) if su else (99,120,120));pivot=np.array([pivx,bottom,(z0+z1)/2]);states=[]
   for g in np.linspace(0,1,21):
    angle=sign*math.radians(96)*np.clip(g/.20,0,1);R=Rotation.from_rotvec([0,0,angle]).as_matrix();states.append(sta(R,pivot-R@pivot))
   add('BayDoor'+title+str(j),m,210,states)
  report[title]={'rect':rect,'closed_door_y':bottom,'roof_y':roof,'release_order':'doors 0-.20; legs .24-1','no_visibility_hiding':True}
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
