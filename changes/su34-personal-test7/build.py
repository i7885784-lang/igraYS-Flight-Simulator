"""PRIVATE test 7: source-derived aircraft, fitted wing-root apertures and connected bogie. Game approximation; aircraft rights remain unresolved.
"""
from pathlib import Path
import sys,json,math,warnings
import numpy as np
from scipy.spatial.transform import Rotation
work=Path(__file__).resolve().parent;root=work;sys.path.insert(0,str(root/'model-source'))
import dnm
from mesh import Mesh,node
from source_parts import read_parts,components
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
r,parts=read_parts(root/'upstream/su34_hi.yft');S=np.array([14.7/19.067,23.34/25.063,6.09/(4.4+1.9873)]);C=np.array([[-S[0],0,0],[0,0,S[2]],[0,S[1],0]])
def cv(v):return np.asarray(v)@C.T+[0,-.8,0]
def sta(R=np.eye(3),t=np.zeros(3)):
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');h,p,b=Rotation.from_matrix(R).as_euler('YXZ')
 return 'STA '+' '.join(map(str,[*np.round(t,7),round(-h*32768/math.pi),round(-p*32768/math.pi),round(b*32768/math.pi),1]))
def rot(axis,p,angle):
 axis=np.array(axis,float);axis/=np.linalg.norm(axis);R=Rotation.from_rotvec(axis*math.radians(angle)).as_matrix();return R,p-R@p
p,ns=dnm.read(work/'baseline/su34.dnm');old={dnm.name(n):n for n in ns}
from source_hull import read_hull
body=read_hull(root/'model-source/legacy_build_model.py',dnm)
from envelope import Envelope
body_env=Envelope([{'v':body.v,'f':[f[0] for f in body.f]}],step=.01)
# Keep the accepted nose system and all controls/other aircraft untouched.
remove=lambda name:name in ['SourceAirframe','GearL','GearR','GearLowerL','GearLowerR','WheelsL','WheelsR'] or name.startswith(('MainDragBrace','MainUpperTrunnion','FlushDoorL','FlushDoorR','InternalWellL','InternalWellR'))
ns=[n for n in ns if not remove(dnm.name(n))]
def add(name,m,cla=99,states=None):
 assert m.f,name
 fn=name+'.srf';p[fn]=m.srf();n=node(name,fn,cla)
 if states:
  i=next(i for i,s in enumerate(n) if s.startswith('NST '));j=next(i for i,s in enumerate(n) if s.startswith('POS '));n[i:j]=['NST '+str(len(states))]+states
 ns.append(n)

doors={};footprints={};door_info={}
for bone,kind in [(8,'Wheel'),(10,'Strut')]:
 selected=[comp for comp in components(parts[bone]) if len(comp) in ([125,69] if bone==8 else [21,16])];pin=r.skeleton[bone]['position'];Rc=Rotation.from_euler('Y',-135 if bone==8 else -70,degrees=True).as_matrix();m=Mesh()
 for comp in selected:
  for q,_,_ in comp:
   v=cv((q-pin)@Rc.T+pin);m.face(v,(135,167,180));m.face(v[::-1],(135,167,180))
 # Adapt the source cover outline to a thin wing-root skin. The donor's
 # inward bulges were crossing the stored wheels; they are not exterior skin.
 raw=m
 # Broaden the wing-root cover within the fixed wing outline so that a
 # full-diameter wheel lies flat without passing through the intake wall.
 raw.v=[(1.28+(v[0]-1.28)*1.65,v[1],v[2]) if kind=='Wheel' else (1.70+(v[0]-1.70)*1.65,v[1],v[2]) for v in raw.v]
 shape=unary_union([Polygon(np.array([raw.v[i] for i in ids])[:,[0,2]]) for ids,_,_ in raw.f]).convex_hull.intersection(body_env.footprint.buffer(-.01))
 if kind=='Strut':shape=shape.union(box(1.72,-1.75,2.58,-1.40)).convex_hull.intersection(box(-100,-100,100,-1.45))
 else:shape=shape.intersection(box(-100,-1.45,100,100))
 def floor_y(x,z):
  return -.245 + .095*np.clip((-z-.8)/.8,0,1) + np.zeros_like(x)
 m=Mesh()
 for tri in constrained_delaunay_triangles(shape).geoms:
  q=np.array(tri.exterior.coords)[:-1];v=np.c_[q[:,0],floor_y(q[:,0],q[:,1]),q[:,1]]
  m.face(v,(135,167,180));m.face((v+[0,.012,0])[::-1],(123,145,156))
 ring=np.array(shape.exterior.coords)
 for a,b in zip(ring[:-1],ring[1:]):
  v=np.array([[a[0],floor_y(*a),a[1]],[b[0],floor_y(*b),b[1]]]);m.face([v[0],v[1],v[1]+[0,.012,0],v[0]+[0,.012,0]],(119,143,158))
 doors[kind]=m;v=np.array(m.v);footprints[kind]=shape.buffer(.008)
 door_info[kind]={'source_bone':bone,'faces':len(m.f),'closed_bounds':[v.min(0).tolist(),v.max(0).tolist()]}
 for side,sg in [('L',1),('R',-1)]:
  mm=Mesh();mm.v=[tuple(np.array(v)*[sg,1,1]) for v in m.v];mm.f=list(m.f)
  # The narrow original cover has a longitudinal outboard hinge.
  pivot=cv(pin);pivot[0]=sg*2.58;pivot[1]=floor_y(abs(pivot[0]),pivot[2]);axis=np.array([0.,0.,1.]);states=[]
  for g in np.linspace(0,1,101):
   opening=np.clip(g/.18,0,1);states.append(sta(*rot(axis,pivot,sg*110*opening)))
  add('OriginalSideDoor'+side+kind,mm,210,states)
# Carve only original panel footprints, never the entire intake-width rectangle.
# Keep exterior forward/back intake and all upper surfaces fixed.
regions={}
for side,sg in [('L',1),('R',-1)]:
 regions[side]=unary_union([Polygon(np.array(poly.exterior.coords)*[sg,1]) for shape in footprints.values() for poly in (list(shape.geoms) if hasattr(shape,'geoms') else [shape])])
# Conformal fixed compartment sides, following the actual cover outline.
# An opening needs enclosing walls; a flat lid alone exposed the stored tyres
# when viewed obliquely even though no triangles intersected.
liner=Mesh()
for side,sg in [('L',1),('R',-1)]:
 outline=regions[side]
 for part in (outline.geoms if hasattr(outline,'geoms') else [outline]):
  ring=np.array(part.exterior.coords)
  for aa,bb in zip(ring[:-1],ring[1:]):
   length=np.linalg.norm(bb-aa);cuts=np.linspace(0,1,max(2,int(length/.055)+1))
   for ta,tb in zip(cuts[:-1],cuts[1:]):
    a=aa+(bb-aa)*ta;b=aa+(bb-aa)*tb;points=np.array([[a[0],0,a[1]],[b[0],0,b[1]]]);_,tops,_=body_env.bounds(points);base=[floor_y(abs(v[0]),v[1]) for v in [a,b]]
    q=[(a[0],base[0],a[1]),(b[0],base[1],b[1]),(b[0],max(base[1]+.015,tops[1]-.008),b[1]),(a[0],max(base[0]+.015,tops[0]-.008),a[1])]
    liner.face(q,(135,167,180));liner.face(q[::-1],(75,94,109))
add('ConformalWingRootBaySides',liner)
new=Mesh();cut=0
# Keep the entire lower intake casing fixed. Only the upper side apertures
# open, and only the original upper exterior remains above the compartment.
from gear_v3 import clip as _clip
def clip(poly,axis,value,positive):return _clip(list(poly),axis,value,positive)
for ids,col,br in body.f:
 q=np.array([body.v[i] for i in ids]);cent=q.mean(0);_,upper,_=body_env.bounds(cent.reshape(1,3))
 samples=np.concatenate([q,cent[None],(q+cent)/2]);_,roof_samples,_=body_env.bounds(samples);delta=roof_samples-samples[:,1];protect_upper=cent[1]>.05 and np.quantile(delta,.75)<.035 and np.median(delta)<.02
 if protect_upper or cent[1]>upper[0]-.012 or max(abs(q[:,0]))<.85 or min(abs(q[:,0]))>2.40 or q[:,2].min()>.65 or q[:,2].max()<-3.75:
  new.face(q,col,br);continue
 lower_piece=clip(q,1,-.28,False)
 if len(lower_piece)>=3:new.face(lower_piece,col,br)
 q=np.array(clip(q,1,-.28,True))
 if len(q)<3:continue
 normal=np.cross(q[1]-q[0],q[2]-q[0]);proj=Polygon(q[:,[0,2]])
 if not proj.is_valid:proj=proj.buffer(0)
 if proj.area<1e-10 or abs(normal[1])<1e-10:new.face(q,col,br);continue
 region=regions['L' if cent[0]>=0 else 'R'];outside=proj.difference(region)
 # An interior duct ceiling is not an exterior wing skin. Remove only its
 # part buried above the fixed intake casing and inside the upper compartment.
 lo,hi,_=body_env.bounds(cent.reshape(1,3))
 if -.28<cent[1]<hi[0]-.012 and abs(normal[1])/np.linalg.norm(normal)>.5:
  sg=1 if cent[0]>=0 else -1;outside=outside.difference(regions['L' if sg>0 else 'R'])
 if abs(outside.area-proj.area)>1e-10:cut+=1
 for tri in constrained_delaunay_triangles(outside).geoms:
  v=np.array(tri.exterior.coords)[:-1];y=q[0,1]-(normal[0]*(v[:,0]-q[0,0])+normal[2]*(v[:,1]-q[0,2]))/normal[1];vv=np.c_[v[:,0],y,v[:,1]]
  if np.dot(np.cross(vv[1]-vv[0],vv[2]-vv[0]),normal)<0:vv=vv[::-1]
  new.face(vv,col,br)
# Restore the accepted nose aperture in the original airframe.
fixed=Mesh()
for ids,col,br in new.f:
 inside=[new.v[i] for i in ids]
 for ax,k,pos in [(0,-.468,True),(0,.468,False),(2,1.16,True),(2,4.35,False),(1,.98,False)]:
  outside=clip(inside,ax,k,not pos) if len(inside)>=3 else []
  if len(outside)>=3:fixed.face(outside,col,br)
  inside=clip(inside,ax,k,pos) if len(inside)>=3 else []
add('SourceAirframe',fixed)
# Correct tandem placement: strut supports the midpoint of the truck.
report={}
for side,sg in [('L',1),('R',-1)]:
 upper=dnm.mesh(p[dnm.fil(old['GearL'])]);lower=dnm.mesh(p[dnm.fil(old['GearLowerL'])]);wheels=dnm.mesh(p[dnm.fil(old['WheelsL'])])
 if sg<0:
  for m in [upper,lower,wheels]:m.v=[tuple(np.array(v)*[-1,1,1]) for v in m.v]
 wheels.shift(0,0,.525*C[2,1]);shift=.025
 for m in [upper,lower,wheels]:m.shift(sg*shift,0,.15)
 q=np.unique(np.round(upper.v,6),axis=0);cap=q[q[:,1]>q[:,1].max()-.08].mean(0);P=np.array([cap[0],.04,cap[2]])
 # Discard the old one-wheel rear support; the tandem truck gets its own hinge.
 ll=Mesh()
 for comp in components([(np.array([lower.v[i] for i in ids]),col,br) for ids,col,br in lower.f]):
  if len(comp)==20:continue
  for q,col,br in comp:ll.face(q,col,br)
 lower=ll
 up=np.array([0.,.996677,.081453]);up/=np.linalg.norm(up);J=np.array([sg*(2.46*S[0]+shift),cv(r.skeleton[42]['position'])[1]+.17*S[2],cv(r.skeleton[42]['position'])[2]+.15])
 wv=np.array(wheels.v);wv[:,0]=J[0]+(wv[:,0]-J[0])*(.30/.441837);wheels.v=[tuple(v) for v in wv]
 F=np.array([sg*(1.887+shift),-1.10,-2.40]);cfg=json.loads((work/'fit.json').read_text());rx,ry,rz,swivel_full,compression,pitch,hy,hz=cfg['parameters'];P[1]=hy;P[2]=hz;ust=[];lst=[];wst=[]
 # A short source-cylinder head connects the fixed trunnion to the actual cap.
 upper.tube(tuple(cap),tuple(P),.065,(147,166,179),12)
 for g in np.linspace(0,1,101):
  fold=1-np.clip((g-.24)/.76,0,1);track=np.array(json.loads((work/'motion-track.json').read_text())['fold_swivel_bogie']);sf=np.interp(fold,track[:,0],track[:,1]);pf=np.interp(fold,track[:,0],track[:,2]);D=np.diag([sg,1,1]);R=D@Rotation.from_euler('XYZ',np.array([rx,ry,rz])*fold,degrees=True).as_matrix()@D;t=P-R@P
  # A swivel about the physical strut axis, followed by the bogie's own
  # pitch hinge. The two tandem wheels remain on a rigid truck.
  swivel=swivel_full*sf;Srot=Rotation.from_rotvec(up*math.radians(sg*swivel)).as_matrix()
  # Rotate lower fork at its connected joint; truck pitch is at its axle.
  A=R@Srot;u=R@(F-Srot@F+up*compression*fold)+t
  target=A@J+u;B=A@Rotation.from_euler('X',pitch*pf,degrees=True).as_matrix()
  ust.append(sta(R,t));lst.append(sta(A,u));wst.append(sta(B,target-B@J))
 add('MainCylinder'+side,upper,210,ust);add('MainInnerStem'+side,lower,210,lst);add('TandemTruck'+side,wheels,210,wst)
 report[side]={'hinge':P.tolist(),'bogie_joint':J.tolist(),'telescopic_stroke_m':compression,'fit_parameters':cfg['parameters'],'strut_swivel_and_bogie_pitch_are_game_approximation':True}
# The donor canard roots stopped short of the fuselage. Extend only the
# buried root band; the moving canard's outer form and control states stay.
for n in ns:
 if dnm.name(n) not in ['Source_aileron_l','Source_aileron_r']:continue
 m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v);sg=1 if v[:,0].mean()>0 else -1;root_x=abs(v[:,0]).min();blend=np.clip(1-(abs(v[:,0])-root_x)/.055,0,1);v[:,0]-=sg*.045*blend;m.v=[tuple(q) for q in v];p[dnm.fil(n)]=m.srf()
from nose_repair import apply
p,ns=apply(p,ns,dnm,sta,body_env)
active={dnm.fil(n) for n in ns};p={k:v for k,v in p.items() if k in active};dest=work/'candidate';(dest/'aircraft').mkdir(parents=True,exist_ok=True)
for name in ['su34.dnm','su34_coarse.dnm']:dnm.write(dest/'aircraft'/name,p,ns)
(work/'prototype.json').write_text(json.dumps({'private_game_test_only':True,'cut_source_faces':cut,'original_doors':door_info,'main':report},indent=2));print('BUILT PROTOTYPE',dest,'cut',cut,flush=True)
