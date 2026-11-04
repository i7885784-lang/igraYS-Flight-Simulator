from pathlib import Path
import json,math,numpy as np
from scipy.spatial.transform import Rotation,Slerp
from scipy.spatial import Delaunay
from scipy.interpolate import LinearNDInterpolator,NearestNDInterpolator
from shapely.geometry import Polygon
from shapely.ops import unary_union,triangulate
from common import dnm,Mesh,add,state,transform
r=Path(__file__).resolve().parent.parent
p,ns=dnm.read(r/'baseline/su30sm.dnm');audit={};by={dnm.name(n):n for n in ns}
def position(n):return np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float)
def dup(m):m.f += [(ids[::-1],c,b) for ids,c,b in list(m.f)];return m
def pose(n,u):
 ss=[s for s in n if s.startswith('STA ')];x=u*(len(ss)-1);i=min(len(ss)-2,int(x));a=x-i;A,t=transform(n,i);B,v=transform(n,i+1);return Slerp([0,1],Rotation.from_matrix([A,B]))([a]).as_matrix()[0],t*(1-a)+v*a
# The near-coplanar front inserts obstruct the intake. Retain the outer nacelles.
removed=[]
for n in list(ns):
 name=dnm.name(n)
 if name in ['Fuselage_0_'+str(i) for i in [8,9,10,11,12,14,15,16,17,18]]:
  removed.append(name);ns.remove(n)
for name in ['Fuselage_0_7','Fuselage_0_13']:
 n=by[name];m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v)+position(n);keep=[];count=0
 for ids,c,b in m.f:
  q=v[ids];a=q[1]-q[0];bb=q[2]-q[0];normal=np.cross(a,bb);nn=np.linalg.norm(normal)
  cap=nn>1e-14 and abs(normal[2])>nn*.75 and (q[:,2].min()>-1.4 or (q[:,2].max()<-9.3 and abs(q.mean(0)[0])>.65))
  if cap:count+=1
  else:keep.append((ids,c,b))
 m.f=keep;p[dnm.fil(n)]=m.srf();audit[name+'_cap_faces_removed']=count
audit['intake_obstruction_nodes_removed']=removed
for sign in [-1,1]:
 cx=sign*1.18;cy=-.54;m=Mesh();front=[(cx-.37,-.97,-1.25),(cx+.37,-.97,-1.25),(cx+.37,-.15,-1.25),(cx-.37,-.15,-1.25)];back=[(cx-.31,-.85,-3.1),(cx+.31,-.85,-3.1),(cx+.31,-.23,-3.1),(cx-.31,-.23,-3.1)]
 for k in range(4):j=(k+1)%4;m.face([front[k],front[j],back[j],back[k]],(30,35,41))
 for k in range(28):
  a=2*math.pi*k/28;b=2*math.pi*(k+1)/28
  def pt(ang,rr,z=-3.12):return (cx+rr*math.cos(ang),cy+rr*math.sin(ang),z)
  m.face([pt(a,.31),pt(b,.31),pt(b,.11),pt(a+.12,.11)],(48+k%2*8,53+k%2*8,58+k%2*8));m.face([(cx,cy,-3.115),pt(a,.115),pt(b,.115)],(34,39,43))
 add(p,ns,'IntakeDuct_'+str(sign),dup(m))
# Restore the base nose here; style_finish.py applies the user-authorized probe revision.
audit['nose_probe']={'stage':'style_finish.py','reason':'User supplied side views and explicitly authorized changing the nose'}
# Repair the opaque cabin well: floor, bulkhead and sidewalls remain below the glazing.
ns=[n for n in ns if not dnm.name(n).startswith(('Su30Interior','Su30NozzleThroat_'))]
inside=Mesh();inside.box(0,.53,4.60,.88,.10,4.6,(36,40,45));inside.box(0,.80,2.35,.83,.48,.08,(43,48,53));inside.box(0,.65,6.84,.72,.24,.08,(38,42,47))
for z in [5.12,3.90]:
 inside.box(0,.69,z,.48,.15,.48,(70,77,63));inside.box(0,.92,z-.20,.46,.55,.10,(61,69,57));inside.box(0,1.16,z-.20,.22,.12,.12,(38,43,40))
inside.box(0,.84,6.16,.71,.31,.15,(30,34,37));inside.box(0,1.005,6.14,.76,.025,.24,(24,28,30))
for x in [-.19,.19]:
 inside.box(x,.86,6.07,.25,.19,.012,(15,22,25))
 for yy in [.82,.86,.90]:inside.box(x,yy,6.063,.19,.006,.004,(62,106,87))
for x in [-.43,.43]:inside.box(x,.70,4.55,.07,.24,4.1,(35,40,42))
add(p,ns,'Su30Interior',inside)
# Extend only the buried roots of the forward planes; tips and pivots stay unchanged.
for n in ns:
 if not dnm.name(n).startswith('Front_Stabilizers'):continue
 m=dnm.mesh(p[dnm.fil(n)]);pos=position(n);v=np.array(m.v)+pos;sg=np.sign(pos[0]);inner=np.min(abs(v[:,0]));v[:,0]-=sg*.16*np.clip(1-(abs(v[:,0])-inner)/.18,0,1);m.v=list(map(tuple,v-pos));p[dnm.fil(n)]=m.srf()
# The old nose-well roof followed the CANOPY envelope and protruded into the glass.
# Keep the whole enclosure under the cabin floor, not at the glazing height.
n=by['GearWell_Nose'];m=dnm.mesh(p[dnm.fil(n)]);m.v=[(x,min(y,.43),z) for x,y,z in m.v];p[dnm.fil(n)]=m.srf()
audit['nose_well_max_y']=.43
# Fold the nose assembly under the floor. The deployed geometry is unchanged.
# This is fitted game kinematics, not a claim of factory hinge coordinates.
carrier=by['WheelCarrier_Nose'];oldC=[transform(carrier,k) for k in range(101)];newC=[]
P=np.array([0.,.05,2.17])
def align_y(a,b):
 y=b-a;y/=np.linalg.norm(y);z=np.cross([1.,0,0],y);z/=np.linalg.norm(z);return np.c_[np.cross(y,z),y,z]
for k,(R,C) in enumerate(oldC):
 leg=np.clip((k/100-.20)/.72,0,1);weight=(1-leg)**2;newC.append((R,C+(np.array([0.,.08,3.72])-oldC[0][1])*weight))
def replace_states(n,poses):
 ids=[i for i,line in enumerate(n) if line.startswith('STA ')]
 assert len(ids)==len(poses)
 for i,(R,C) in zip(ids,poses):n[i]=state(R,C)
replace_states(carrier,newC);replace_states(by['GearAxle_Nose'],newC)
struts=[(align_y(P,C),P.copy()) for R,C in newC];replace_states(by['GearUpper_Nose'],struts)
replace_states(by['GearPiston_Nose'],[(R,C-R[:,1]*1.40) for (R,_),(Q,C) in zip(struts,newC)])
for label,pa,pb in [('TorqueUpper',.52,.66),('TorqueLower',.66,.80)]:
 poses=[]
 for R,C in newC:
  v=C-P;Q=P+v*pa;T=P+v*pb;side=align_y(P,C)[:,2]*-.10
  if label=='TorqueUpper':T=T+side
  else:Q=Q+side
  poses.append((align_y(Q,T),Q))
 replace_states(by['GearLink_'+label+'_Nose'],poses)
audit['nose_gear_closed_center']=newC[0][1].tolist()
# Su30SM kit drawing 7314 p5: a narrow long bay door plus a separate wheel shield.
from gear import clip
for n in list(ns):
 name=dnm.name(n)
 if not name.startswith(('GearDoor_Left_','GearDoor_Right_')):continue
 sg=-1 if '_Left_' in name else 1;title='Left' if sg<0 else 'Right';m=dnm.mesh(p[dnm.fil(n)]);Rg,Cg=transform(by['WheelCarrier_'+title],0);R0,t0=transform(n,0);P0=position(n);outer=Mesh();cover=Mesh();fixed=Mesh()
 for ids,c,b in m.f:
  world=np.array([m.v[i] for i in ids])@R0.T+t0+P0;poly=list(world)
  a=clip(poly,0,sg*1.87,sg>0);inner=clip(poly,0,sg*1.87,sg<0)
  if len(a)>=3:outer.face((np.array(a)-t0-P0)@R0,c,b)
  for bound,positive in [(-1.86,False),(-.66,True)]:
   q=clip(inner,2,bound,positive) if len(inner)>=3 else []
   if len(q)>=3:fixed.face(q,c,b)
  q=clip(inner,2,-1.858,True) if len(inner)>=3 else [];q=clip(q,2,-.662,False) if len(q)>=3 else []
  if len(q)>=3:cover.face((np.array(q)-Cg)@Rg,c,b)
 # Rebuild the shield as a sealed curved skin in CLOSED WORLD coordinates.
 # Projecting it after the 145-degree wheel fold incorrectly capped across the tyre.
 cv=np.array(cover.v)@Rg.T+Cg;xy,idx=np.unique(np.round(cv[:,[0,2]],6),axis=0,return_inverse=True);yy=np.full(len(xy),np.inf);np.minimum.at(yy,idx,cv[:,1]);shapes=[]
 for ids,c,b in cover.f:
  poly=Polygon(cv[ids][:,[0,2]])
  if poly.is_valid and poly.area>1e-10:shapes.append(poly)
 domain=unary_union(shapes).convex_hull;closed=Mesh();edgecounts={};edgeverts={}
 for ids in Delaunay(xy).simplices:
  triangle=Polygon(xy[ids])
  if not domain.buffer(2e-6).covers(triangle):continue
  q=np.c_[xy[ids,0],yy[ids],xy[ids,1]];back=q+np.array([0,.006,0]);closed.face((q-Cg)@Rg,(57,50,115));closed.face((back[::-1]-Cg)@Rg,(52,60,68))
  for aa,bb in zip(ids,np.roll(ids,-1)):
   key=tuple(sorted((int(aa),int(bb))));edgecounts[key]=edgecounts.get(key,0)+1;edgeverts[key]=(q[list(ids).index(aa)],q[list(ids).index(bb)])
 for key,count in edgecounts.items():
  if count==1:
   aa,bb=edgeverts[key];q=np.array([aa,bb,bb+[0,.006,0],aa+[0,.006,0]]);closed.face((q-Cg)@Rg,(54,60,68))
 cover=dup(closed)
 p[dnm.fil(n)]=outer.srf();add(p,ns,'MainBayFixedSkin_'+title,fixed)
 # The 2 mm running seam is backed by the existing fully enclosed wheel well.
 states=[]
 for k in range(101):
  R,C=transform(by['WheelCarrier_'+title],k);g=k/100;u=np.clip((g-.20)/.72,0,1);u=u*u*(3-2*u);release=np.clip((u-.35)/.30,0,1);hold=1-release*release*(3-2*release);states.append(state(R,C+R@np.array([-sg*.14*u,0,0])+np.array([0,-.75*math.sin(math.pi*u),(Cg[2]-C[2])*hold])))
 add(p,ns,'GearDoor_'+title+'_WheelShield',cover,210,states)
# Small telescopic carrier links keep the wheel shields mechanically attached
# throughout their guided clearance movement (game linkage, not factory data).
def support_axis(a,b):
 y=b-a;y/=np.linalg.norm(y);helper=np.array([1.,0,0]) if abs(y[0])<.9 else np.array([0.,0,1.]);z=np.cross(helper,y);z/=np.linalg.norm(z);return np.c_[np.cross(y,z),y,z]
for sg,title in [(-1,'Left'),(1,'Right')]:
 shield=next(n for n in ns if dnm.name(n)=='GearDoor_'+title+'_WheelShield');carrier=by['WheelCarrier_'+title];samples=[]
 for k in range(101):
  R,C=transform(carrier,k);S,T=transform(shield,k);samples.append((R@np.array([sg*.05,.55,0])+C,S@np.array([-sg*.17,.55,0])+T))
 lengths=[np.linalg.norm(b-a) for a,b in samples];L=max(lengths)*.56
 for part,rad in [('Cylinder',.022),('Rod',.014)]:
  mesh=Mesh();mesh.tube((0,0,0),(0,L,0),rad,(102,118,128) if part=='Cylinder' else (171,183,187),12);states=[]
  for A,B in samples:
   R=support_axis(A,B);states.append(state(R,A if part=='Cylinder' else B-R[:,1]*L))
  add(p,ns,'GearShieldSupport_'+part+'_'+title,mesh,210,states)
# The nose bay has two short forward leaves and one aft longitudinal panel,
# rather than two full-length hanging slabs (Su30SM instruction 7314 p5).
aft=Mesh();left_node=by['GearDoor_Nose_Inner'];AL,CL=transform(left_node,0);PL=position(left_node)
for node in list(ns):
 if not dnm.name(node).startswith('GearDoor_Nose_'):continue
 mesh=dnm.mesh(p[dnm.fil(node)]);R,C=transform(node,0);P=position(node);front=Mesh()
 for ids,c,b in mesh.f:
  world=np.array([mesh.v[i] for i in ids])@R.T+C+P;back=clip(list(world),2,3.15,False);fore=clip(list(world),2,3.15,True)
  if len(back)>=3:aft.face((np.array(back)-CL-PL)@AL,c,b)
  if len(fore)>=3:front.face((np.array(fore)-C-P)@R,c,b)
 p[dnm.fil(node)]=front.srf()
add(p,ns,'GearDoor_Nose_Aft',aft,210,[line for line in left_node if line.startswith('STA ')])
# Close holes in each door with an inner backing, and provide a narrow recessed seating flange.
for n in list(ns):
 name=dnm.name(n)
 if not name.startswith('GearDoor_') or name.endswith('_WheelShield'):continue
 m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v);polys=[]
 for ids,c,b in m.f:
  q=Polygon(v[ids][:,[0,2]])
  if q.is_valid and q.area>1e-9:polys.append(q)
 shape=unary_union(polys);regions=list(shape.geoms) if hasattr(shape,'geoms') else [shape]
 xz,idx=np.unique(np.round(v[:,[0,2]],6),axis=0,return_inverse=True);yy=np.full(len(xz),-np.inf);np.maximum.at(yy,idx,v[:,1]);linear=LinearNDInterpolator(xz,yy);near=NearestNDInterpolator(xz,yy)
 def height(q):
  a=np.array(q);h=linear(a);return np.where(np.isfinite(h),h,near(a))
 flange=Mesh();R0,t0=transform(n,0);pos=position(n)
 for reg in regions:
  outline=Polygon(reg.exterior)
  for tri in triangulate(outline):
   if not outline.buffer(1e-8).covers(tri):continue
   q=np.array(tri.exterior.coords)[:3];RR,_=transform(n,0);h=height(q)+(.004 if RR[1,1]>=0 else -.004);m.face(np.c_[q[:,0],h,q[:,1]],(47,47,79));m.f.append((m.f[-1][0][::-1],(47,47,79),False))
  coords=np.array(outline.exterior.coords);cen=np.array(outline.centroid.coords[0])
  for a,b in zip(coords[:-1],coords[1:]):
   inset=.015 if '_Nose_' in name else .025;aa=a+(cen-a)/max(np.linalg.norm(cen-a),1e-9)*inset;bb=b+(cen-b)/max(np.linalg.norm(cen-b),1e-9)*inset;q=np.array([a,b,bb,aa]);h=height(q);world=np.c_[q[:,0],h,q[:,1]]@R0.T+t0+pos;world[:,1]+=.010;flange.face(world,(35,39,55));flange.face(world[::-1],(35,39,55))
 p[dnm.fil(n)]=m.srf();add(p,ns,'DoorSeat_'+name,flange)
# Matte tyres and restrained hubs, preserving wheel volume and rolling animation.
for n in ns:
 name=dnm.name(n)
 if not name.startswith(('Wheel_','WheelHub_')):continue
 m=dnm.mesh(p[dnm.fil(n)]);m.f=[(ids,(13,15,17) if name.startswith('Wheel_') else tuple(int(v*.62) for v in c[:3]),False) for ids,c,b in m.f];p[dnm.fil(n)]=m.srf()
# Recessed speed-brake floor follows the original cover, not a plate across the whole fuselage.
brake=next(n for n in ns if dnm.cla(n)==212);bm=dnm.mesh(p[dnm.fil(brake)]);bp=position(brake);floor=Mesh();vv=np.array(bm.v)+bp;center=vv.mean(0)
for ids,c,b in bm.f:
 q=vv[ids].copy();q[:,[0,2]]=center[[0,2]]+(q[:,[0,2]]-center[[0,2]])*1.025;q[:,1]-=.12;floor.face(q,(39,44,54))
add(p,ns,'AirbrakeBayFloor',floor)
# Telescoping actuator: two rigid overlapping components with 21 sampled native poses.
A=bp+np.array([0,-.16,-.12]);B=np.array([0,.90,-.25]);samples=[]
def axis(a,b):
 y=b-a;y/=np.linalg.norm(y);z=np.cross([1.,0,0],y);z/=np.linalg.norm(z);return np.c_[np.cross(y,z),y,z]
for u in np.linspace(0,1,21):
 R,t=pose(brake,float(u));T=R@(B-bp)+bp+t;samples.append((A,T))
lengths=[np.linalg.norm(T-Q) for Q,T in samples];L=max(lengths)*.56;assert min(lengths)>L
for title,rad in [('Cylinder',.038),('Piston',.021)]:
 m=Mesh();m.tube((0,0,0),(0,L,0),rad,(87,99,108) if title=='Cylinder' else (154,166,174),16);states=[]
 for Q,T in samples:
  R=axis(Q,T);origin=Q if title=='Cylinder' else T-R[:,1]*L;states.append(state(R,origin))
 add(p,ns,'AirbrakeActuator_'+title,m,271,states)
audit['airbrake_actuator_lengths']=lengths
# Retain original detailed petals, increase their circumferential overlap, and reduce extremes.
old_profile=json.loads((r/'nozzle-profile.json').read_text());profiles={};nozzles=[]
for n in ns:
 if dnm.cla(n)!=270:continue
 pos=position(n);side='0' if pos[0]<0 else '1';q=old_profile[side][-1];rad=np.array([pos[0]-q['cx'],pos[1]-q['cy'],0]);rad/=np.linalg.norm(rad);tan=np.array([-rad[1],rad[0],0]);m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v);v+=np.outer(v@tan,tan)*.24;m.v=list(map(tuple,v));p[dnm.fil(n)]=m.srf()
 newposes=[pose(n,float(.2+.6*u)) for u in np.linspace(0,1,21)];idxs=[i for i,s in enumerate(n) if s.startswith('STA ')]
 for i,(R,t) in zip(idxs,newposes):n[i]=state(R,t)
 nozzles.append((n,np.array(m.v),pos,side))
for side in ['0','1']:
 axisq=old_profile[side][-1];out=[]
 for k in range(21):
  radii=[];zs=[]
  for n,v,pos,s in nozzles:
   if s!=side:continue
   R,t=transform(n,k);q=v@R.T+pos+t;z=q[:,2].min();band=q[q[:,2]<z+.018];radii.append(np.linalg.norm(band[:,:2]-[axisq['cx'],axisq['cy']],axis=1).min());zs.append(z)
  out.append({'radius':float(np.median(radii)),'z':float(np.mean(zs)),'cx':axisq['cx'],'cy':axisq['cy']})
 profiles[side]=out
# Long recessed exhaust lining, not the old shallow end plug.
for side in ['0','1']:
 q=profiles[side][-1];cx,cy,z=q['cx'],q['cy'],q['z'];rad=q['radius'];m=Mesh()
 for k in range(32):
  a=2*math.pi*k/32;b=2*math.pi*(k+1)/32
  def pt(t,rr,zz):return (cx+rr*math.cos(t),cy+rr*math.sin(t),zz)
  m.face([pt(a,rad*1.08,z+.012),pt(b,rad*1.08,z+.012),pt(b,rad*.84,z+.68),pt(a,rad*.84,z+.68)],(31+k%2*5,35+k%2*5,40+k%2*5));m.face([(cx,cy,z+.70),pt(b,rad*.85,z+.70),pt(a,rad*.85,z+.70)],(16,19,23))
  for depth in [.20,.42,.63]:
   rr=rad*(1.08-.24*depth/.68);m.face([pt(a,rr,z+depth),pt(b,rr,z+depth),pt(b,rr-.012,z+depth+.014),pt(a,rr-.012,z+depth+.014)],(60,56,48))
 add(p,ns,'Su30NozzleThroat_'+side,dup(m))
# Matched, translucent blue reheat with a pale core and shock rings.
for n in list(ns):
 if dnm.cla(n) not in [112,113,114,115]:continue
 side=str((dnm.cla(n)-112)%2);q=profiles[side][-1];cx,cy,z,rad=q['cx'],q['cy'],q['z'],q['radius'];m=Mesh();N=32
 if dnm.cla(n) in [112,113]:
  rings=[(0,.94,105),(.12,.86,135),(.30,.74,115),(.52,.56,80),(.76,.31,35),(1,.015,0)]
  for (ta,ra,al),(tb,rb,be) in zip(rings,rings[1:]):
   for k in range(N):
    a,b=2*math.pi*k/N,2*math.pi*(k+1)/N;m.face([(cx+rad*ra*math.cos(a),cy+rad*ra*math.sin(a),z+.008-2.1*ta),(cx+rad*ra*math.cos(b),cy+rad*ra*math.sin(b),z+.008-2.1*ta),(cx+rad*rb*math.cos(b),cy+rad*rb*math.sin(b),z+.008-2.1*tb),(cx+rad*rb*math.cos(a),cy+rad*rb*math.sin(a),z+.008-2.1*tb)],(65,125,255,(al+be)//2),True)
  for depth in [.25,.60,.95,1.3]:
   rr=rad*(.58-.27*depth/1.3)
   for k in range(N):
    a,b=2*math.pi*k/N,2*math.pi*(k+1)/N;aa=(cx+rr*math.cos(a),cy+rr*math.sin(a),z-depth);bb=(cx+rr*math.cos(b),cy+rr*math.sin(b),z-depth);m.face([(cx,cy,z-depth+.13),aa,bb],(120,185,255,28),True);m.face([(cx,cy,z-depth-.17),bb,aa],(150,205,255,35),True)
  p[dnm.fil(n)]=dup(m).srf()
 # Dry exhaust already uses low opacity; its base needs only the small matching scale change.
 else:
  m=dnm.mesh(p[dnm.fil(n)]);old=old_profile[side][-1];scale=rad/old['radius'];m.v=[(cx+(x-old['cx'])*scale,cy+(y-old['cy'])*scale,zz+(z-old['z'])) for x,y,zz in m.v];p[dnm.fil(n)]=m.srf()
# Save matching animation-to-plume calibration.
lines=['#pragma once','#include <array>','inline std::array<double,5> Su30ExhaustProfile(int engine,double opening){','static const double p[2][21][5]={']
for side in ['0','1']:
 samples=profiles[side];base=samples[-1];lines.append('{'+','.join('{'+','.join(f'{x:.10g}' for x in [q['radius']/base['radius'],q['radius']/base['radius'],0,0,(q['z']-base['z'])/(base['radius']*.94)])+'}' for q in samples)+'},')
lines+=['};','const double u=(opening<0?0:opening>1?1:opening)*20;const int i=(int(u)<20?int(u):19);const double f=u-i;std::array<double,5> r;for(int j=0;j<5;++j)r[j]=p[engine][i][j]+f*(p[engine][i+1][j]-p[engine][i][j]);return r;','}'];(r/'engine/YSFLIGHT/src/vehicle/su30_exhaust_profile.h').write_text('\n'.join(lines)+'\n')
p={fn:ls for fn,ls in p.items() if fn in {dnm.fil(n) for n in ns}}
dnm.write(r/'runtime/aircraft/su30sm.dnm',p,ns)
cn=[n for n in ns if dnm.name(n) in ['Fuselage_0_4','Fuselage_0_5','Fuselage_0_6','Cockpit_cover_6_30','Cockpit_cover_6_31','Su30Interior']];dnm.write(r/'runtime/aircraft/su30smcockpit.dnm',{dnm.fil(n):p[dnm.fil(n)] for n in cn},cn)
s=(r/'baseline/su30sm.dat').read_text().replace('-2.52m','-2.56m');(r/'runtime/aircraft/su30sm.dat').write_text(s)
(r/'profiles-test3.json').write_text(json.dumps(profiles,indent=2));audit['nozzle_radius_ratio']=profiles['0'][-1]['radius']/profiles['0'][0]['radius'];audit['petal_tangent_width_factor']=1.24;(r/'revision.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2),flush=True)
