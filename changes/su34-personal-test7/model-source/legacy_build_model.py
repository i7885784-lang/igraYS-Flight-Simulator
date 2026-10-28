"""PRIVATE Su-34 YFT -> YSFlight geometry adaptation. Distribution held pending rights."""
from pathlib import Path
import math,json,hashlib,re,warnings
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull,cKDTree
from mesh import Mesh,node
import dnm
from source_parts import read_parts,components
HERE=Path(__file__).resolve().parent
DEST=HERE/'runtime/aircraft';DEST.mkdir(parents=True,exist_ok=True)
r,parts=read_parts(HERE.parent/'upstream/su34_hi.yft')
# Omit baked GTA weapons/stores; the game uses its own weapons on source pylons.
for b in [51,57]:parts.pop(b,None)
parts[66]=[face for comp in components(parts[66]) if np.concatenate([f[0] for f in comp])[:,2].min()>2.0 for face in comp]
parts[15]=[face for comp in components(parts[15]) if not (np.concatenate([f[0] for f in comp])[:,2].min()<-.50 and np.abs(np.concatenate([f[0] for f in comp])[:,0]).max()<2.0) for face in comp]
# Source has no right wheel drawable. Reuse its left wheel geometry symmetrically.
parts[44]=[(q*np.array([-1,1,1]),g,s) for q,g,s in parts[42]]
# Normalize to Su-34 envelope, retaining the actual YFT shape and two-seat cabin.
S=np.array([14.7/19.067,23.34/25.063,6.09/(4.4+1.9873)])
C=np.array([[-S[0],0,0],[0,0,S[2]],[0,S[1],0]])
OFFSET=np.array([0.,-.80,0.])
def cv(q):return np.asarray(q)@C.T+OFFSET

def sta(R=np.eye(3),t=np.zeros(3),show=1):
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');h,p,b=Rotation.from_matrix(R).as_euler('YXZ')
 return ' '.join(map(str,[*np.round(t,7),round(-h*32768/math.pi),round(-p*32768/math.pi),round(b*32768/math.pi),show]))
def rotate(axis,pivot,degrees):
 a=np.asarray(axis,float);a/=np.linalg.norm(a);R=Rotation.from_rotvec(a*math.radians(degrees)).as_matrix();p=np.asarray(pivot);return R,p-R@p

def double(m):
 for f,c,b in list(m.f):m.face([m.v[i] for i in f[::-1]],c,b)
 return m
packs={};nodes=[];stats={};hull=Mesh();mesh_by_bone={}
def add(name,m,cla=99,states=None):
 if not m.f:return
 fn=name+'.srf';packs[fn]=m.srf();n=node(name,fn,cla)
 if states:
  i=n.index('NST 1');j=n.index('POS 0 0 0 0 0 0 1');n[i:j]=['NST '+str(len(states))]+['STA '+s for s in states]
 nodes.append(n);stats[name]={'class':cla,'faces':len(m.f),'states':len(states or [1])}

def polygon_clip(poly,n,k,positive=True):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  a=np.asarray(a);b=np.asarray(b);da=np.dot(a,n)-k;db=np.dot(b,n)-k;ia=da>=-1e-9 if positive else da<=1e-9;ib=db>=-1e-9 if positive else db<=1e-9
  if ia:out.append(a)
  if ia!=ib:out.append(a+(b-a)*da/(da-db))
 return out

def split_aileron(q,sign):
 # Actual outer trailing wing strip, distinct from the source's misnamed PGO.
 planes=[(np.array([sign,0,0]),6.70,True),(np.array([sign,0,0]),9.10,False),(np.array([0,0,1]),.50,True),(np.array([0,0,1]),1.15,False),(np.array([.31*sign,1,0]),-3.573,False)]
 inside=list(q);outside=[]
 for n,k,pos in planes:
  if len(inside)<3:break
  out=polygon_clip(inside,n,k,not pos)
  if len(out)>=3:outside.append(out)
  inside=polygon_clip(inside,n,k,pos)
 return inside,outside

moving=[4,5,6,7,47,50,53,56,61,62]
controltree=cKDTree(np.concatenate([np.array([f[0] for f in parts[b]]).reshape(-1,3) for b in moving]))
outer={-1:Mesh(),1:Mesh()};removed=0
for b,faces in parts.items():
 if b in [1,2,3,20,23,25]:continue # duplicated night gauges/fans; source ladder rig handled separately
 m=Mesh()
 for q,geometry,shader in faces:
  if b==15 and np.max(controltree.query(q)[0])<.002:removed+=1;continue
  raw=q.mean(0);c=cv(q).mean(0)
  color=(103,153,174)
  if b in [0,17,64]:color=(61,77,75) if b==0 and geometry==14 else (42,54,59) if geometry==12 else (56,76,77)
  elif b==16:color=(65,116,138,116)
  elif b in [33,41,43,39,40]:color=(159,174,183)
  elif b in [34,42,44]:
   hub=np.array([4.145,-1.499]) if b==34 else np.array([-2.698,-1.472]);radius=.31 if b==34 else .52
   color=(126,142,153) if np.linalg.norm(raw[[1,2]]-hub)<radius*.49 else (32,36,39)
  elif b in [19,22]:color=(49,59,66)
  elif raw[1]>8.55:color=(202,211,210)
  elif raw[2]<.50:color=(135,167,180)
  elif math.sin(raw[1]*.67)+.7*math.cos(raw[0]*.94)>.55:color=(55,109,137)
  if b==15:
   remainder=[list(q)]
   for sign in [-1,1]:
    new=[]
    for poly in remainder:
     strip,rest=split_aileron(poly,sign)
     if len(strip)>=3:outer[sign].face([tuple(p) for p in cv(strip)],color)
     new.extend(rest)
    remainder=new
   for poly in remainder:m.face([tuple(p) for p in cv(poly)],color)
  else:m.face([tuple(p) for p in cv(q)],color)
 mesh_by_bone[b]=m
 if b==15:hull=m;continue
 # Fixed armored glazing. Ordinary opening of the entire canopy is not invented.
 if b in [33,34,39,40,41,42,43,44,8,9,10,11,12,67]:continue
 if b in moving:
  cls={4:248,5:249,6:246,7:247,47:242,53:243,50:244,56:245,61:250,62:251}[b]
  pivot=cv(r.skeleton[b]['position']);axis=(C@(r.skeleton[b]['matrix'][:3,:3]@np.array([0.,0,1.])) if b in [4,5] else np.array([1.,0,0]))
  if b in [50,56]:axis=np.array([1.,0,(-1 if b==50 else 1)*.72])
  degrees=25 if b in [4,5] else 22 if b in [50,56] else -25 if b in [47,53] else 25
  states=[sta(*rotate(axis,pivot,degrees*q)) for q in np.linspace(-1,1,41)]
  double(m);add('Source_'+r.skeleton[b]['name'],m,cls,states)
 else:double(m);add('Source_'+r.skeleton[b]['name'],m)
for sign,cls in [(-1,240),(1,241)]:
 m=outer[sign];pivot=cv([sign*6.7,-5.65,.84]);axis=C@np.array([sign, -.31,0]);degrees=(-1 if sign<0 else 1)*22
 double(m);add('OuterAileron'+str(cls),m,cls,[sta(*rotate(axis,pivot,degrees*q)) for q in np.linspace(-1,1,41)])
# Initial source-derived rig exported below; fit/clearance validation is separate.
from rig import add_rig
rig_info=add_rig(mesh_by_bone,r,C,OFFSET,hull,add,double,sta,cv,rotate)
double(hull);add('SourceAirframe',hull)
# Source engine axes stay fixed. Own plain lit exhaust and AB geometry.
for i,sg in enumerate([-1,1]):
 center=cv([sg*1.53,-8.85,.20]);x,y,z=center;rx=.46;ry=.53;pipe=Mesh();flame=Mesh()
 for k in range(24):
  a=k*math.pi/12;b=(k+1)*math.pi/12
  pipe.face([(x+rx*math.cos(a),y+ry*math.sin(a),z+.6),(x+rx*math.cos(b),y+ry*math.sin(b),z+.6),(x+rx*.86*math.cos(b),y+ry*.86*math.sin(b),z),(x+rx*.86*math.cos(a),y+ry*.86*math.sin(a),z)],(77+k%2*12,87+k%2*12,94+k%2*12))
  flame.face([(x,y,z-1.5),(x+rx*.74*math.cos(b),y+ry*.74*math.sin(b),z-.02),(x+rx*.74*math.cos(a),y+ry*.74*math.sin(a),z-.02)],(242,142,64),True)
 double(pipe);add('FixedNozzle'+str(i),pipe);double(flame);add('Afterburner'+str(i),flame,110+i,[sta(show=0),sta()])
# Small own side brackets join the actual source wing tips to native launch rails.
launchers=Mesh()
for sg in [-1,1]:
 for z in [-4.55,-3.75]:launchers.box(sg*7.24,-.13,z,.36,.09,.12,(114,146,164))
 launchers.box(sg*7.34,-.18,-4.05,.10,.10,1.80,(121,151,167))
add('OwnTipLaunchers',launchers)
# Own polygon insignia; no image/texture from the source pack.
from envelope import Envelope
reference=json.loads((HERE/'envelope-reference.json').read_text());skin=Envelope(reference);marks=Mesh()
for sign in [-1,1]:
 center=np.array([sign*5.75,0.,-4.35]);points=[]
 for k in range(10):
  a=math.pi*k/5;radius=.40 if k%2==0 else .17;x=center[0]+radius*math.sin(a);z=center[2]+radius*math.cos(a);y=float(skin.bounds(np.array([[x,0,z]]))[1][0])+.009;points.append((x,y,z))
 center[1]=float(skin.bounds(center.reshape(1,3))[1][0])+.010
 for k in range(10):
  q=[tuple(center),points[k],points[(k+1)%10]]
  if np.cross(np.array(q[1])-q[0],np.array(q[2])-q[0])[1]<0:q=q[::-1]
  marks.face(q,(188,43,49))
add('OwnWingStars',marks)
# An opaque floor and contoured rear bulkhead seal the cockpit behind both seats.
liner=Mesh();liner.box(0,.05,5.25,1.50,.03,1.65,(34,46,52))
for i in range(24):
 xa=-.75+1.5*i/24;xb=-.75+1.5*(i+1)/24
 ya=float(skin.bounds(np.array([[xa,0,4.415]]))[1][0])-.025;yb=float(skin.bounds(np.array([[xb,0,4.415]]))[1][0])-.025
 a=[(xa,.05,4.40),(xb,.05,4.40),(xb,yb,4.40),(xa,ya,4.40)];b=[(x,y,4.43) for x,y,z in a]
 for q in [a[::-1],b,[a[0],a[1],b[1],b[0]],[a[3],b[3],b[2],a[2]],[a[0],b[0],b[3],a[3]],[a[1],a[2],b[2],b[1]]]:liner.face(q,(38,50,56))
add('OwnCockpitLiner',liner)

from door_kinematics import apply as apply_doors
apply_doors('su34',nodes,HERE,packs)
for fn in ['su34.dnm','su34_coarse.dnm']:dnm.write(DEST/fn,packs,nodes)
coll=Mesh()
# Bound collision hulls to small spatial cells; never bridge the full wing gap.
xc=np.array([-7.5,-4,-2.5,-1.6,-.65,.65,1.6,2.5,4,7.5]);zc=np.array([-12.1,-8.5,-6.5,-4.5,-2.5,0,3,6,9,12.1]);cells={}
for bone in [15,4,5,6,7,47,50,53,56,61,62,16]:
 for sourcepoly,g,shader in parts[bone]:
  original=list(cv(sourcepoly));q=np.array(original)
  for ix in range(len(xc)-1):
   if q[:,0].max()<xc[ix] or q[:,0].min()>xc[ix+1]:continue
   for iz in range(len(zc)-1):
    if q[:,2].max()<zc[iz] or q[:,2].min()>zc[iz+1]:continue
    poly=original
    for axis,k,pos in [(np.array([1.,0,0]),xc[ix],True),(np.array([1.,0,0]),xc[ix+1],False),(np.array([0.,0,1]),zc[iz],True),(np.array([0.,0,1]),zc[iz+1],False)]:
     if len(poly)<3:break
     poly=polygon_clip(poly,axis,k,pos)
    if len(poly)>=3:cells.setdefault((ix,iz),[]).extend(poly)
for points in cells.values():
 pts=np.unique(np.round(points,5),axis=0)
 if len(pts)<4:continue
 try:
  ch=ConvexHull(pts)
  for ids,eq in zip(ch.simplices,ch.equations):
   q=pts[ids]
   if np.dot(np.cross(q[1]-q[0],q[2]-q[0]),eq[:3])<0:q=q[::-1]
   coll.face([tuple(a) for a in q],(90,100,110))
 except Exception:continue
(DEST/'su34coll.srf').write_text('\n'.join(coll.srf())+'\n');(DEST/'su34cockpit.srf').write_text('SURF\nE\n')
dat=(HERE/'su34_template.dat').read_text();params={'IDENTIFY':'"SU-34_FULLBACK"','WEIGHCLN':'22.5t','WEIGFUEL':'12.1t','WEIGLOAD':'8.0t','WINGAREA':'62m^2','MAXSPEED':'1.8MACH','COCKPITP':'-.42m 1.12m 5.72m','LEFTGEAR':'-2.17m -2.53m -3.00m','RIGHGEAR':'2.17m -2.53m -3.00m','WHELGEAR':'0m -2.53m 3.86m','HTRADIUS':'13m'}
for key,val in params.items():dat=re.sub(r'(?m)^'+key+r'\s+.*$',key+' '+val,dat)
stations=[(7.40,-.26,-4.05),(-7.40,-.26,-4.05),(4.60,-.65,-3.27),(-4.60,-.65,-3.27),(3.47,-.65,-2.83),(-3.47,-.65,-2.83)]
dat=re.sub(r'(?m)^HRDPOINT.*\n','',dat)
dat+='\n'+''.join('HRDPOINT '+' '.join(f'{v:.6f}m' for v in p)+' AIM9 AIM9X AIM120 B250 B500HD\n' for p in stations)
(DEST/'su34.dat').write_text(dat)
meta={'private_only':True,'source_commit':'db0191619fb3d1cefc225eb5b216a91267ad7740','reader_meshes':len(r.meshes),'source_triangles':sum(map(len,parts.values())),'root_and_fragment_geometry':True,'baked_GTA_payloads_removed':True,'native_weapon_stations':stations,'source_textures_loaded':False,'scale_xyz':S.tolist(),'collider_spatial_cells':len(cells),'collider_faces':len(coll.f),'nodes':stats,'removed_duplicate_faces':removed,'rig':rig_info,'generated_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in DEST.glob('su34*')}}
(HERE/'model-stats.json').write_text(json.dumps(meta,indent=2));print('SU34 PRIVATE',len(nodes),'nodes',sum(v['faces'] for v in stats.values()),'faces')
