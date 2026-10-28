"""Personal test 6. Local repairs, always rebuilt from preserved test 5."""
from pathlib import Path
import sys,json,math,warnings
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'model-source'))
import dnm
from mesh import Mesh,node
from ac_reference import AC
from envelope import Envelope
from gear_v3 import clip as _clip
def clip(poly,axis,threshold,positive):return _clip(list(poly),axis,threshold,positive)
p,ns=dnm.read(root/'baseline/su27.dnm');lookup={dnm.name(n):n for n in ns}
removed=['AxleForkL','AxleForkR']
ns=[n for n in ns if dnm.name(n) not in removed]
ac=AC(root/'model-source/upstream/su27/Su-27.ac')
for o in ac.objects:o['v']=(np.array(o['v'])+[0,0,10]).tolist()
source=[o for o in ac.objects if o['name'].startswith('HULL_Hull_Upper')];env=Envelope(source,step=.01)
def state(R=np.eye(3),t=np.zeros(3)):
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');h,pp,b=Rotation.from_matrix(R).as_euler('YXZ')
 return 'STA '+' '.join(map(str,[*np.round(t,7),round(-h*32768/math.pi),round(-pp*32768/math.pi),round(b*32768/math.pi),1]))
def add(name,m,cla=99,states=None):
 fn=name+'.srf';p[fn]=m.srf();n=node(name,fn,cla)
 if states:
  i=n.index('NST 1');j=n.index('POS 0 0 0 0 0 0 1');n[i:j]=['NST '+str(len(states))]+states
 ns.append(n)
def double(m):
 for ids,col,b in list(m.f):m.face([m.v[i] for i in ids[::-1]],col,b)
 return m
# The old rectangular well walls protruded into the real gaps between the
# wing and intakes. Replace them with small internal rims on the ACTUAL hatches.
ns=[n for n in ns if not dnm.name(n).startswith('UpperWell')]
for side,sg in [('L',1),('R',-1)]:
 n=lookup['FixedDuctRoof'+side];m=dnm.mesh(p[dnm.fil(n)]);fixed=Mesh()
 for ids,c,b in m.f:
  q=[m.v[i] for i in ids]
  q=clip(q,0,.85 if sg>0 else -.85,sg>0);q=clip(q,2,-1.10,False) if len(q)>=3 else []
  if len(q)>=3:fixed.face(q,c,b)
 p[dnm.fil(n)]=fixed.srf()
# A vertical min/max envelope alone cannot distinguish the EXTERNAL sides
# of the two intake lobes from an internal floor. Restore original casing faces
# visible along a horizontal ray, while retaining only the intended hatch holes.
from fit_internal import reference
old_env=reference(ac,True)
x_env=Envelope([{'v':np.array(o['v'])[:,[1,0,2]],'f':o['f']} for o in source],step=.01)
complete=json.loads((root/'model-source/main-door-complete-map.json').read_text())
excluded=set(complete['L']+complete['R']);side_skin=Mesh();restored_sides=0
def inside_box(q,planes):
 for ax,k,pos in planes:q=clip(q,ax,k,pos) if len(q)>=3 else []
 return q
for o in source:
 vv=np.array(o['v'])
 for fi,ids in enumerate(o['f']):
  if o['name']=='HULL_Hull_Upper.001' and fi in excluded:continue
  q=list(vv[ids])
  for sg in [1,-1]:
   xa,xb=(.85,2.25) if sg>0 else(-2.25,-.85)
   piece=inside_box(q,[(0,xa,True),(0,xb,False),(2,-4.55,True),(2,-.75,False),(1,-.13,True),(1,.50,False)])
   if len(piece)<3:continue
   c=np.mean(piece,0);lo,hi,_=old_env.bounds(c.reshape(1,3))
   if c[1]<lo[0]+.012 or c[1]>hi[0]-.012:continue
   xl,xh,_=x_env.bounds(c[[1,0,2]].reshape(1,3))
   if min(abs(c[0]-xl[0]),abs(c[0]-xh[0]))<.020:
    side_skin.face(piece,(119,151,175));restored_sides+=1
if side_skin.f:add('RestoredIntakeSideSkins',double(side_skin))

# Restore the exact source faces identified by the native face-ID render
# behind the four marked defects, plus the matching opposite-side source faces.
from scipy.spatial import cKDTree
obj=next(o for o in source if o['name']=='HULL_Hull_Upper.001');vv=np.array(obj['v']);centers=np.array([vv[f].mean(0) for f in obj['f']]);tree=cKDTree(centers)
chosen=set(json.loads((root/'visible-original-casing-faces.json').read_text())['face_ids'])-excluded
for fi in list(chosen):
 target=centers[fi]*[-1,1,1];dist,idx=tree.query(target,k=3)
 for dd,ii in zip(dist,idx):
  if dd<.10 and int(ii) not in excluded:chosen.add(int(ii))
exact_casing=Mesh()
for fi in sorted(chosen):exact_casing.face(vv[obj['f'][fi]],(119,151,175))
if exact_casing.f:add('RestoredMarkedCasing',double(exact_casing))
# Exact original lower fuselage facets make a flush nose hatch, without the
# raster-envelope ridges which protruded at its longitudinal ends.
x0,x1,z0,z1=-.34,.34,1.97,4.77
from shapely.geometry import Polygon,box
from shapely import constrained_delaunay_triangles
# Compute the exact lower envelope of the source facets. Selecting by centroid
# alone accidentally included interior planes above the external lower skin.
facets=[];seen_faces=set()
for o in source:
 vv=np.array(o['v'])
 for ids in o['f']:
  for k in range(1,len(ids)-1):
   q=vv[[ids[0],ids[k],ids[k+1]]];A=np.c_[q[:,0],q[:,2],np.ones(3)]
   if abs(np.linalg.det(A))<1e-10:continue
   area=Polygon(q[:,[0,2]]).intersection(box(x0,z0,x1,z1))
   if area.area<1e-10:continue
   coeff=np.linalg.solve(A,q[:,1]);key=tuple(sorted(tuple(v) for v in np.round(q,6)))
   if key in seen_faces:continue
   seen_faces.add(key);facets.append((area,coeff))
def halfplane(poly,abc):
 pts=list(poly.exterior.coords)[:-1];out=[]
 for a,b in zip(pts,pts[1:]+pts[:1]):
  a,b=np.array(a),np.array(b);fa=abc[0]*a[0]+abc[1]*a[1]+abc[2];fb=abc[0]*b[0]+abc[1]*b[1]+abc[2]
  if fa>1e-7:out.append(a)
  if (fa>1e-7)!=(fb>1e-7):out.append(a+(b-a)*((fa-1e-7)/(fa-fb)))
 return Polygon(out) if len(out)>2 else Polygon()
outer=Mesh();visible_facets=[]
for area,coeff in facets:
 visible=area
 for other,cc in facets:
  if visible.is_empty:break
  if np.linalg.norm(coeff-cc)<1e-7:continue
  if not visible.intersects(other):continue
  bad=halfplane(other,coeff-cc).intersection(other)
  if not bad.is_empty:visible=visible.difference(bad)
 visible_facets.append((visible,coeff))
 for tri in constrained_delaunay_triangles(visible).geoms:
  xz=np.array(tri.exterior.coords)[:-1];y=np.c_[xz,np.ones(len(xz))]@coeff;q=np.c_[xz[:,0],y,xz[:,1]]
  if tri.area>1e-8 and y.max()<.15:outer.face(q,(119,151,175))
__import__('pickle').dump((facets,visible_facets),open(root/'nose-envelope.debug.pkl','wb'))
# The old source cockpit floor is superseded by the game's opaque cockpit
# liner at Y=.715m. Restoring that buried plane across the bay blocks the wheel.
# Keep the actual exterior hatch and the existing cockpit liner instead.
# Preserve the two inherited leaves for now: their exact neutral surface is the
# priority; a different real aircraft variant must not be guessed from screenshots.
newdoors=[]
for side in [0,1]:
 m=Mesh()
 for ids,col,b in outer.f:
  q=clip([outer.v[i] for i in ids],0,0,side==1)
  if len(q)<3:continue
  m.face(q,col);m.face(np.array(q)[::-1]+[0,.008,0],(83,100,113))
 # Add thickness only along the actual panel edges.
 verts=np.array(m.v)
 old=lookup['FlushGearDoorN'+str(side)];n=old.copy();p[dnm.fil(old)]=m.srf()
 # Straight longitudinal hinge fitted to the real fuselage edge, rather than
 # the previous displaced and asymmetrical pivots.
 hx=x0 if side==0 else x1;vv=np.array(outer.v);edge=vv[abs(vv[:,0]-hx)<.001]
 slope,intercept=np.polyfit(edge[:,2],edge[:,1],1);pivot=np.array([hx,intercept,.0]);axis=np.array([0,slope,1.]);axis/=np.linalg.norm(axis)
 sign=-1 if side==0 else 1;states=[]
 for g in np.linspace(0,1,101):
  R=Rotation.from_rotvec(axis*math.radians(sign*92)*min(g/.20,1)).as_matrix();states.append(state(R,pivot-R@pivot))
 i=next(i for i,s in enumerate(old) if s.startswith('NST '));j=next(i for i,s in enumerate(old) if s.startswith('POS '));old[i:j]=['NST 101']+states
 newdoors.append({'name':dnm.name(old),'faces':len(m.f),'axis':axis.tolist(),'pivot':pivot.tolist(),'edge_deviation_m':float(np.max(abs(edge[:,1]-np.polyval([slope,intercept],edge[:,2]))))})
# Bound the nose well by the actual opening, not the previous oversized
# storage rectangle, whose end walls were visible below the closed fuselage.
well=Mesh();outline=[]
for (xa,za),(xb,zb) in [((x0,z0),(x1,z0)),((x1,z0),(x1,z1)),((x1,z1),(x0,z1)),((x0,z1),(x0,z0))]:
 outline.extend((xa+(xb-xa)*t,za+(zb-za)*t) for t in np.linspace(0,1,40,endpoint=False))
# Source lower skin at the panel rim, using exact triangle intersections.
tri=[]
for o in source:
 vv=np.array(o['v'])
 for ids in o['f']:
  q=vv[ids]
  if q[:,2].max()<z0 or q[:,2].min()>z1 or q[:,0].min()>x1 or q[:,0].max()<x0:continue
  tri.extend(q[[0,k,k+1]] for k in range(1,len(q)-1))
def height(x,z):
 hits=[]
 for a,b,c in tri:
  A=np.array([[a[0]-c[0],b[0]-c[0]],[a[2]-c[2],b[2]-c[2]]])
  if abs(np.linalg.det(A))<1e-10:continue
  u,v=np.linalg.solve(A,[x-c[0],z-c[2]])
  if min(u,v,1-u-v)>-1e-6:hits.append(u*a[1]+v*b[1]+(1-u-v)*c[1])
 assert hits,(x,z)
 return min(hits),float(np.interp(z,[1.97,3.2,3.45,4.77],[.95,.95,.710,.710]))
yrim=[height(x,z) for x,z in outline]
for i,(x,z) in enumerate(outline):
 j=(i+1)%len(outline);xx,zz=outline[j];lo,hi=yrim[i];ll,hh=yrim[j]
 well.face([(x,lo+.008,z),(xx,ll+.008,zz),(xx,hh,zz),(x,hi,z)],(68,82,91))
# An internal roof, wholly inside the original fuselage.
for xa,xb in zip(np.linspace(x0,x1,9),np.linspace(x0,x1,9)[1:]):
 for za,zb in zip(np.linspace(z0,z1,25),np.linspace(z0,z1,25)[1:]):
  well.face([(x,height(x,z)[1],z) for x,z in [(xa,za),(xb,za),(xb,zb),(xa,zb)]],(63,77,86))
p[dnm.fil(lookup['InternalGearBayN'])]=double(well).srf()

# Restore the physical root hinge at the top of the source cylinder. Solve
# the closed oleo length against the original body, without the old fake floor.
from fit_internal import fit
from corrections import axis_rotation
objects={o['name']:o for o in ac.objects};names=[k for k in objects if k.startswith('UC_Nose_') and k not in ['UC_Nose_Rear_Post','UC_Nose_Upright_Brace','UC_Nose_BSArm']]
P=np.array([0.,.42,2.34]);axle=np.array([0.,-1.98,2.20]);fitinfo=json.loads((root/'nose-fit-reviewed.json').read_text());target=np.array(fitinfo['target']);C=(P-axle)/np.linalg.norm(P-axle)*fitinfo['compression'];target[1]=.300;short=axle+C-P;target[2]=P[2]+math.sqrt(short@short-(target[1]-P[1])**2);from fit_internal import align;up=align(short,target-P);rv=Rotation.from_matrix(up).as_rotvec();fitinfo['clearance_adjusted_target']=target.tolist();matrices=[]
for g in np.linspace(0,1,101):
 fold=1-np.clip((g-.24)/.76,0,1);R=Rotation.from_rotvec(rv*fold).as_matrix();t=P-R@P;u=t+R@(C*fold);matrices.append((R,t,u))
for name,n in lookup.items():
 if not name.startswith('Gear_UC_Nose_'):continue
 upper=name in ['Gear_UC_Nose_Upper_Strut_leg','Gear_UC_Nose_LLights_leg'];states=[state(R,t if upper else u) for R,t,u in matrices];i=next(i for i,s in enumerate(n) if s.startswith('NST '));end=next(i for i,s in enumerate(n) if s.startswith('POS '));n[i:end]=['NST 101']+states
brace_base=np.array([0.,.30,2.03]);attachment=np.array([0.,-.60,2.25]);length=.56;poses=[[],[]];torques=[[],[]]
for R,t,u in matrices:
 tip=R@attachment+u;delta=tip-brace_base;distance=np.linalg.norm(delta);perp=np.array([0,delta[2],-delta[1]]);perp/=np.linalg.norm(perp)
 if perp[1]<0:perp=-perp
 assert distance<2*length
 knee=(brace_base+tip)/2+perp*math.sqrt(length*length-distance*distance/4)
 for j,(a,b) in enumerate([(brace_base,knee),(knee,tip)]):poses[j].append(state(axis_rotation([0,0,1],b-a),a))
 a=R@np.array([0.,-1.00,2.33])+t;b=R@np.array([0.,-1.50,2.30])+u;delta=b-a;distance=np.linalg.norm(delta);perp=np.cross(delta,[0,1,0]);perp=perp/np.linalg.norm(perp) if np.linalg.norm(perp)>1e-8 else np.array([1.,0,0])
 if perp[0]<0:perp=-perp
 assert distance<.62
 knee=(a+b)/2+perp*math.sqrt(.31**2-distance**2/4)
 for j,(a,b) in enumerate([(a,knee),(knee,b)]):torques[j].append(state(axis_rotation([0,0,1],b-a),a))
for prefix,rows in [('NoseDragBrace',poses),('NoseTorqueLink',torques)]:
 for j in [0,1]:
  n=lookup[prefix+str(j)];i=next(i for i,s in enumerate(n) if s.startswith('NST '));end=next(i for i,s in enumerate(n) if s.startswith('POS '));n[i:end]=['NST 101']+rows[j]
# Keep the original guard outside both tyres; narrowing it would push its
# side plates into them. The correct internal roof now gives it room to stow.
# Only a small fixed clearance fit of the upper casting is required.
n=lookup['Gear_UC_Nose_Upper_Strut_leg'];m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v);R,t,u=matrices[0];world=v@R.T+t;roof=np.interp(world[:,2],[1.97,3.2,3.45,4.77],[.95,.95,.710,.710]);delta=np.maximum(world[:,1]+.008-roof,0);assert delta.max()<.04;v-=delta[:,None]*R[1];m.v=[tuple(q) for q in v];p[dnm.fil(n)]=m.srf()
# Cover the original round access-hole boundaries and a small triangular missing
# lower-casing face. These are fixed lit skins, not fake gear doors.
patch=Mesh();s=np.load(root/'source-boundaries.npz');v=s['v'];edges=s['edges'];adj={}
for a,b in edges:adj.setdefault(int(a),[]).append(int(b));adj.setdefault(int(b),[]).append(int(a))
seen=set();filled=[]
for start in adj:
 if start in seen:continue
 stack=[start];co=set()
 while stack:
  a=stack.pop()
  if a in co:continue
  co.add(a);stack.extend(adj[a])
 seen.update(co);q=v[list(co)];lo,hi=q.min(0),q.max(0)
 eligible=(len(co)==10 and np.ptp(q[:,0])<.001 and .5<abs(q[:,0].mean())<2 and -2<lo[2] and hi[2]<0) or (len(co)==3 and .5<abs(q[:,0].mean())<2 and -4.1<lo[2] and hi[2]<-3)
 if not eligible or any(len(adj[a])!=2 for a in co):continue
 seq=[start];prev=-1;cur=start
 for _ in range(len(co)-1):
  nxt=next(x for x in adj[cur] if x!=prev);seq.append(nxt);prev,cur=cur,nxt
 points=v[seq];center=points.mean(0)
 for a,b in zip(points,np.roll(points,-1,axis=0)):patch.face([center,a,b],(97,117,130))
 filled.append({'vertices':len(co),'bounds':[lo.tolist(),hi.tolist()]})
if patch.f:add('IntakeAccessSkins',double(patch))
# Keep the accepted main-leg fold and fixed hinges. Only advance the swivel
# phase where the restored real casing requires more clearance.
if (root/'swivel-path.json').exists():
 cfg=json.loads((root/'connected-main-fit-track.json').read_text());pa=np.array(cfg['parameters']);MP=np.array(cfg['pivot']);MF=np.array(cfg['fork_joint']);mu=np.array(cfg['fork_axis']);rv=Rotation.from_euler('XYZ',pa[:3],degrees=True).as_rotvec();path=json.loads((root/'swivel-path.json').read_text())['swivel_fraction']
 ns=[n for n in ns if not dnm.name(n).startswith(('TorqueLink','OleoCollar'))]
 for side,sg in [('L',1),('R',-1)]:
  D=np.diag([sg,1,1]);states=[]
  for g,sf in zip(np.linspace(0,1,101),path):
   fold=1-np.clip((g-.24)/.76,0,1);R=Rotation.from_rotvec(rv*fold).as_matrix();t=MP-R@MP;S=Rotation.from_rotvec(mu*math.radians(pa[3])*sf).as_matrix();A=R@S;u=R@(MF-S@MF+mu*pa[4]*fold)+t;states.append(state(D@A@D,D@u))
  for prefix in ['ConnectedMainFork','ConnectedMainWheels']:
   n=lookup[prefix+side];i=next(i for i,s in enumerate(n) if s.startswith('NST '));j=next(i for i,s in enumerate(n) if s.startswith('POS '));n[i:j]=['NST 101']+states
  from torque_links27 import build as build_torques
  build_torques(side,sg,MP,MF,rv,mu,pa,path,add,state)

# Remove coplanar overlap between restored casing pieces and old fragments.
# Keeping both produced the fine flickering lines visible in the last game view.
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
groups={}
for name in ['RestoredIntakeSideSkins','RestoredMarkedCasing']:
 n=next((n for n in ns if dnm.name(n)==name),None)
 if n is None:continue
 m=dnm.mesh(p[dnm.fil(n)])
 for ids,c,b in m.f:
  q=np.array([m.v[i] for i in ids]);N=np.cross(q[1]-q[0],q[2]-q[0]);length=np.linalg.norm(N)
  if length<1e-10:continue
  N/=length;axis=int(np.argmax(abs(N)))
  if N[axis]<0:N=-N
  offset=float(N@q[0]);axes=[i for i in range(3) if i!=axis];poly=Polygon(q[:,axes])
  if not poly.is_valid:poly=poly.buffer(0)
  key=tuple(np.round(N,5))+(round(offset,5),);entry=groups.setdefault(key,{'N':N,'offset':offset,'axis':axis,'axes':axes,'polys':[]});entry['polys'].append(poly)
for group in groups.values():group['shape']=unary_union(group['polys'])
def lift(xy,G):
 q=np.zeros((len(xy),3));q[:,G['axes']]=xy;q[:,G['axis']]=(G['offset']-q@G['N'])/G['N'][G['axis']];return q
h=dnm.mesh(p['Hull.srf']);clean=Mesh()
for ids,c,b in h.f:
 q=np.array([h.v[i] for i in ids]);remaining=None;used=None
 for G in groups.values():
  if np.max(abs(q@G['N']-G['offset']))>2e-5:continue
  poly=Polygon(q[:,G['axes']])
  if not poly.is_valid:poly=poly.buffer(0)
  if poly.area<1e-10 or not poly.intersects(G['shape']):continue
  remaining=poly.difference(G['shape']);used=G;break
 if used is None:clean.face(q,c,b)
 else:
  for tri in constrained_delaunay_triangles(remaining).geoms:
   if tri.area>1e-10:clean.face(lift(np.array(tri.exterior.coords)[:-1],used),c,b)
p['Hull.srf']=clean.srf();casings=Mesh()
for G in groups.values():
 for tri in constrained_delaunay_triangles(G['shape']).geoms:
  if tri.area>1e-10:casings.face(lift(np.array(tri.exterior.coords)[:-1],G),(119,151,175))
ns=[n for n in ns if dnm.name(n) not in ['RestoredIntakeSideSkins','RestoredMarkedCasing']]
if casings.f:add('RestoredFixedCasing',double(casings))

active={dnm.fil(n) for n in ns};p={k:v for k,v in p.items() if k in active}
for f in ['su27.dnm','su27_coarse.dnm']:dnm.write(root/'runtime/aircraft'/f,p,ns)
(root/'repair-su27.json').write_text(json.dumps({'removed_obsolete_gear_parts':removed,'restored_original_external_side_faces':restored_sides,'nose_doors':newdoors,'nose_root_and_oleo_fit':fitinfo,'fixed_access_openings':filled,'not_yet_release_ready':True},indent=2));print('REPAIRED',removed,'nose',newdoors,'fixed holes',len(filled),flush=True)
