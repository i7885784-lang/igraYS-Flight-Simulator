from pathlib import Path
import numpy as np,json,math
from scipy.spatial import cKDTree
from common import dnm,Mesh,add,state,transform,Rotation
r=Path(__file__).resolve().parent.parent;p,ns=dnm.read(r/'baseline/su30sm.dnm');lu={dnm.name(n):n for n in ns};audit={}
def position(n):return np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float)
def setstates(n,ss):
 ids=[i for i,s in enumerate(n) if s.startswith('STA ')];a,b=ids[0],ids[-1]+1;n[a-1:b]=['NST '+str(len(ss))]+ss

def worldmesh(n):
 m=dnm.mesh(p[dnm.fil(n)]);R,t=transform(n,0);v=np.array(m.v)@R.T+t+position(n);return m,v

def store_world(n,m):
 R,t=transform(n,0);m.v=[tuple((np.array(v)-position(n)-t)@R) for v in m.v];p[dnm.fil(n)]=m.srf()

# Keep the current paint and lateral silhouette. Reduce only transverse thickness.
for n in ns:
 name=dnm.name(n)
 if not name.startswith(('Fuselage_','Rudder_')):continue
 m=dnm.mesh(p[dnm.fil(n)]);pos=position(n);v=np.array(m.v)+pos;before=v.copy();count=0
 for i,q in enumerate(v):
  if abs(q[0])<1.75 or abs(q[0])>2.4 or q[1]<.38 or q[2]>-3.0:continue
  # Full change above the root blending band; root blend remains attached.
  amount=float(np.clip((q[1]-.38)/.50,0,1));factor=1-.56*amount
  center=math.copysign(2.055,q[0]);q[0]=center+(q[0]-center)*factor;count+=1
 if count:
  m.v=[tuple(q-pos) for q in v];p[dnm.fil(n)]=m.srf();audit[name]={'modified_vertices':count,'max_transverse_factor_above_root':.44,'side_silhouette_yz_unchanged':bool(np.array_equal(v[:,1:],before[:,1:]))}
# Closed canopy/glass are unchanged. Opening angle is a visual estimate from photo2.
for n in ns:
 if dnm.cla(n)==211:
  old=[s for s in n if s.startswith('STA ')];setstates(n,[old[0],state(Rotation.from_euler('x',-43,degrees=True).as_matrix())]);audit[dnm.name(n)]={'old_open_degrees':55,'open_degrees':43,'closed_mesh_unchanged':True}
# Dorsal brake: keep closed cover fit, raise rear edge to photographed inclination.
brake=lu['Air_Brake_1_20'];bp=position(brake);old=[s for s in brake if s.startswith('STA ')];setstates(brake,[old[0],state(Rotation.from_euler('x',65,degrees=True).as_matrix())])
ns[:]=[n for n in ns if not dnm.name(n).startswith('AirbrakeActuator_')]
def axis(a,b):
 y=b-a;y/=np.linalg.norm(y);z=np.cross([1.,0,0],y);z/=np.linalg.norm(z);return np.c_[np.cross(y,z),y,z]
bm=dnm.mesh(p[dnm.fil(brake)]);vv=np.array(bm.v);q=vv[(abs(vv[:,0])<.25)&(abs(vv[:,2]+1.72)<.22)];by=float(np.median(q[:,1])) if len(q) else -.35
A=bp+np.array([0,-.22,-.42]);B=np.array([0,by-.025,-1.72]);samples=[]
for u in np.linspace(0,1,21):samples.append((A,bp+Rotation.from_euler('x',65*u,degrees=True).apply(B)))
lengths=[float(np.linalg.norm(T-Q)) for Q,T in samples];L=max(lengths)*.56
for title,rad,col in [('Cylinder',.042,(87,99,108)),('Piston',.022,(154,166,174))]:
 m=Mesh();m.tube((0,0,0),(0,L,0),rad,col,14);ss=[]
 for Q,T in samples:
  R=axis(Q,T);ss.append(state(R,Q if title=='Cylinder' else T-R[:,1]*L))
 add(p,ns,'AirbrakeActuator_'+title,m,271,ss)
# Clevis at both real endpoints; one is part of the moving leaf.
m=Mesh();m.tube(A+[-.075,0,0],A+[.075,0,0],.055,(87,99,108),12);add(p,ns,'AirbrakeBaseClevis',m)
m=Mesh();m.tube(B+[-.07,0,0],B+[.07,0,0],.043,(87,99,108),12);n=add(p,ns,'AirbrakeLeafClevis',m,212,[old[0],state(Rotation.from_euler('x',65,degrees=True).as_matrix())]);n[:]=dnm.edit(n,'POS ',' '.join(map(str,bp))+' 0 0 0 1')
audit['airbrake']={'hinge_degrees':65,'visible_rear_edge_inclination_approx_degrees':52,'actuator_base':A.tolist(),'leaf_attachment_local':B.tolist(),'actuator_lengths':lengths}

# Clean shared nacelle/wing-root cross-sections replace jagged overlapping patches.
xs=np.array([.58,.78,1.03,1.20,1.40,1.50,1.62,1.74,1.87,2.4]);zs=np.array([-3.38,-2.2,-1.3,-.41])
ys=np.array([[-.62,-.91,-1.10,-1.10,-1.07,-1.01,-.74,-.55,-.47,-.08],[-.65,-.94,-1.14,-1.14,-1.10,-1.02,-.74,-.52,-.46,-.04],[-.66,-.95,-1.16,-1.15,-1.10,-1.00,-.70,-.45,-.25,-.04],[-.66,-.95,-1.16,-1.14,-1.07,-.99,-.35,-.16,-.03,.01]])
def lower(x,z):return float(np.interp(z,zs,[np.interp(abs(x),xs,row) for row in ys]))
def palette(names):
 pts=[];colors=[]
 for name in names:
  m,v=worldmesh(lu[name])
  for ids,c,b in m.f:
   if b:continue
   pts.append(v[ids].mean(0)[[0,2]]);colors.append(c)
 tree=cKDTree(pts)
 return lambda x,z:colors[int(tree.query([x,z])[1])]
def sheet(n,xlo,xhi,zlo,zhi,color,thick=.009):
 m=Mesh();xx=np.linspace(xlo,xhi,max(3,int(abs(xhi-xlo)/.12)+1));zz=np.linspace(zlo,zhi,max(3,int((zhi-zlo)/.16)+1))
 def v(x,z,top=0):return (x,lower(x,z)+top,z)
 for a,b in zip(xx,xx[1:]):
  for c,d in zip(zz,zz[1:]):
   pts=[v(a,c),v(b,c),v(b,d),v(a,d)];m.face(pts,color((a+b)/2,(c+d)/2));m.face([v(x,z,thick) for x,_,z in pts[::-1]],(98,113,121))
 for x in [xx[0],xx[-1]]:
  for a,b in zip(zz,zz[1:]):m.face([v(x,a),v(x,b),v(x,b,thick),v(x,a,thick)],(104,120,130))
 for z in [zz[0],zz[-1]]:
  for a,b in zip(xx,xx[1:]):m.face([v(a,z),v(b,z),v(b,z,thick),v(a,z,thick)],(104,120,130))
 store_world(n,m)
for title,sg in [('Left',-1),('Right',1)]:
 fixed=lu['MainBayFixedSkin_'+title];shutter=lu['MainWheelBayShutter_'+title];door=lu['GearDoor_'+('Left_Inner' if title=='Left' else 'Right_Outer')]
 def color(x,z):
  y=lower(x,z)
  if y<-.25:return (142,169,181)
  signal=math.sin(z*.86+x*.56)+.58*math.sin(x*1.7-z*.30)+.27*math.cos(z*1.9)
  return (77,139,163) if signal<-.48 else (118,166,185) if signal<.72 else (147,163,172)
 # Fixed skin around shutter opening; matching edges use exactly the same section.
 m=Mesh()
 for xa,xb,za,zb in [(.58,1.03,-3.38,-.41),(1.03,1.87,-3.38,-1.85),(1.03,1.87,-.66,-.41)]:
  temp=[s for s in fixed];sheet(temp,sg*xa,sg*xb,za,zb,color);m.merge(dnm.mesh(p[dnm.fil(fixed)]))
 p[dnm.fil(fixed)]=m.srf()
 sheet(shutter,sg*1.03,sg*1.87,-1.85,-.66,color)
 sheet(door,sg*1.87,sg*2.4,-3.38,-.41,color)
 # Bay liner: no copied jagged outline or walls hanging below the shell.
 well=lu['GearWell_'+title];m=Mesh();xx=np.linspace(.58,2.4,18);zz=np.linspace(-3.38,-.41,22);col=(45,53,60)
 for a,b in zip(xx,xx[1:]):
  for c,d in zip(zz,zz[1:]):m.face([(sg*a,.27,c),(sg*b,.27,c),(sg*b,.27,d),(sg*a,.27,d)],col)
 for x in [.58,2.4]:
  for a,b in zip(zz,zz[1:]):m.face([(sg*x,lower(x,a)+.018,a),(sg*x,lower(x,b)+.018,b),(sg*x,.27,b),(sg*x,.27,a)],col)
 for z in [-3.38,-.41]:
  for a,b in zip(xx,xx[1:]):m.face([(sg*a,lower(a,z)+.018,z),(sg*b,lower(b,z)+.018,z),(sg*b,.27,z),(sg*a,.27,z)],col)
 p[dnm.fil(well)]=m.srf()
 # Seats stay entirely inside the closed skins, following repaired outer seam.
 seat=lu['DoorSeat_'+dnm.name(door)];sheet(seat,sg*1.875,sg*2.395,-3.375,-.415,color,thick=.012)
 sm=dnm.mesh(p[dnm.fil(seat)]);sm.v=[(x,y+.018,z) for x,y,z in sm.v];p[dnm.fil(seat)]=sm.srf()
 audit['lower_'+title]={'shared_sections_x':xs.tolist(),'sections_z':zs.tolist(),'shutter_opening_z':[-1.85,-.66],'paint':'original test4/5 colour rule and palette retained on replacement panels'}
# Split the broad aft nose panel into two opposing doors, avoiding a single large hanging flap.
aft=lu['GearDoor_Nose_Aft'];am,av=worldmesh(aft);R0,t0=transform(aft,0);new=[]
for side,sg,source in [('Left',-1,'GearDoor_Nose_Inner'),('Right',1,'GearDoor_Nose_Outer')]:
 # Reuse the existing sampled hinge poses and closed Y section.
 src=lu[source];m=Mesh();cols=[c for ids,c,b in am.f];color=cols[0];xx=np.linspace(-.38,0,5) if sg<0 else np.linspace(0,.38,5);zz=np.linspace(1.99,3.15,12)
 def yy(z):return float(np.interp(z,[1.99,2.4,2.85,3.15],[-.12,-.20,-.31,-.36]))
 for x0,x1 in zip(xx,xx[1:]):
  for z0,z1 in zip(zz,zz[1:]):
   q=[(x0,yy(z0),z0),(x1,yy(z0),z0),(x1,yy(z1),z1),(x0,yy(z1),z1)];m.face(q,color);m.face([(x,y+.008,z) for x,y,z in q[::-1]],(98,113,121))
 for x in [xx[0],xx[-1]]:
  for z0,z1 in zip(zz,zz[1:]):m.face([(x,yy(z0),z0),(x,yy(z1),z1),(x,yy(z1)+.008,z1),(x,yy(z0)+.008,z0)],color)
 for z in [zz[0],zz[-1]]:m.face([(xx[0],yy(z),z),(xx[-1],yy(z),z),(xx[-1],yy(z)+.008,z),(xx[0],yy(z)+.008,z)],color)
 n=add(p,ns,'GearDoor_Nose_Aft_'+side,m,210,[s for s in src if s.startswith('STA ')]);store_world(n,m);new.append(dnm.name(n))
ns.remove(aft);audit['nose_aft_split']=new
# No vertex normal R records: retain flat shaded appearance.
output=r/'runtime/aircraft/su30sm.dnm';tmp=output.with_suffix('.dnm.building');dnm.write(tmp,p,ns);tmp.replace(output);cp,cn=dnm.read(r/'runtime/aircraft/su30smcockpit.dnm'); names={dnm.name(n) for n in cn}; cn=[n for n in ns if dnm.name(n) in names];dnm.write(r/'runtime/aircraft/su30smcockpit.dnm',{dnm.fil(n):p[dnm.fil(n)] for n in cn},cn);(r/'refinement.json').write_text(json.dumps(audit,indent=2));print('test6 written',output)
