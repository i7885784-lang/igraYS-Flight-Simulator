from pathlib import Path
import sys,math,json,hashlib,shutil
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
from collections import Counter
from read_p3d import Reader
from mesh import Mesh,node
import dnm
lab=Path(__file__).resolve().parent;source=lab/'upstream' if (lab/'upstream').exists() else lab.parent/'su47-source';dest=lab/'runtime/aircraft';dest.mkdir(parents=True,exist_ok=True)
lods=Reader(source/'Su_47_Berkut.p3d').parse();l=lods[0];mem=lods[4]
scale=np.array([16.7/(8.2107048+8.13426876),6.4/(6.29496384+.13029006),-22.6/(9.4914093+15.16970253)])
origin=np.array([.03821802,3.0,-2.8391466])
def cv(v):return (np.array(v[:3])-origin)*scale
p=np.array([cv(v) for v in l['points']]);npnt=len(p);nf=len(l['faces']);tags=l['tags']
select=lambda name:set(i for i,b in enumerate(tags.get(name,bytes(npnt+nf))[npnt:]) if b)
def axis(name):
 t=mem['tags'][name];q=np.unique(np.round(np.array([cv(v) for i,v in enumerate(mem['points']) if t[i]]),5),axis=0);u,sv,v=np.linalg.svd(q-q.mean(0),full_matrices=False);a=v[0];
 if a[np.argmax(abs(a))]<0:a=-a
 return q.mean(0),a
excluded=set()
for name in tags:
 if name.lower().startswith('proxy:') or name in ['ladder','missile pos']:excluded|=select(name)
parts={};assigned={};groups={
 'Canopy':('Canopy',100,'canopy_axis',-.65,0),
 'AileronL':('aileron_l',180,'aileron_l_axis',.40,-.40),'AileronR':('aileron_r',181,'aileron_r_axis',-.40,.40),
 'FlapL':('flap_l',182,'flap_l_axis',-.40,.40),'FlapR':('flap_r',183,'flap_r_axis',-.40,.40),
 'SlatL':('volet_l',184,'volet_l_axis',.20,-.20),'SlatR':('volet_r',185,'volet_r_axis',.20,-.20),
 'CanardL':('canard_l',186,'canards_axis',.30,-.30),'CanardR':('canard_r',187,'canards_axis',.30,-.30),
 'RudderL':('rudder_l',188,'rudder_l_axis',.375,-.375),'RudderR':('rudder_r',189,'rudder_r_axis',.375,-.375),
 'ElevatorL':('elevator_l',190,'elevator_l_axis',.35,-.35),'ElevatorR':('elevator_r',191,'elevator_r_axis',.35,-.35),
 'GearN':('gear_n',140,'gear_n_axis',-1.693,0),'GearL':('gear_l',141,'gear_l_axis',-1.50,0),'GearR':('gear_r',142,'gear_r_axis',1.50,0),
 'DoorN':('F_Door',143,'F_Door_axis',0,math.pi/2),'DoorL':('L_Door',144,'L_Door_axis',0,math.radians(100)),'DoorR':('R_Door',145,'R_Door_axis',0,math.radians(-100))}
for name,(sel,*_) in groups.items():
 ids=select(sel)
 if name=='GearN':ids|=select('gear_n_steering')|select('wheel_n')
 if name=='GearL':ids|=select('wheel_l')|select('gear_l2')|select('pick')
 if name=='GearR':ids|=select('wheel_r')|select('gear_r2')
 assigned[name]=ids
# Claim moving faces first; exclude foreign proxy triangles entirely.
owner={i:name for name,ids in assigned.items() for i in ids};glass=select('Glass_Canopy01_default')|select('Glass_default')|select('Glass_HUD_default')
for i,f in enumerate(l['faces']):
 if i in excluded or i in select('EngineL') or i in select('EngineR'):continue
 name=owner.get(i,'Hull');m=parts.setdefault(name,Mesh());pts=p[[v[0] for v in f['v']]]
 if len(pts)<3:continue
 normal=np.sum([np.array(l['normals'][v[1]])/scale for v in f['v']],axis=0)
 if np.dot(np.cross(pts[1]-pts[0],pts[2]-pts[0]),normal)>0:pts=pts[::-1]
 center=pts.mean(0);col=(63,69,76)
 if i in glass:col=(79,115,138,135)
 elif 'Gear' in name:
  col=(153,163,171) if center[1]>-2.25 else (29,32,35)
 elif name.startswith('Door'):col=(59,65,72)
 elif i in select('Eject_Seat'):col=(49,57,49)
 elif abs(center[0])>7.45 or center[2]>9.15:col=(211,217,216)
 elif center[1]<-.7:col=(45,50,57)
 m.face([tuple(a) for a in pts],col)
 # Glass and inner cockpit surfaces must also be visible from the other side.
 if i in glass:m.face([tuple(a) for a in pts[::-1]],col)
# Opaque skin is visible from both sides; never let an inverted source polygon become a window.
for ids,c,b in list(parts['Hull'].f):
 if len(c)==3:parts['Hull'].face([parts['Hull'].v[i] for i in ids[::-1]],c,b)
packs={};nodes=[];stats={}
def state(angle,a):
 R=Rotation.from_rotvec(a*angle).as_matrix();h,pit,b=Rotation.from_matrix(R).as_euler('YXZ');return f'0 0 0 {round(-h*32768/math.pi)} {round(-pit*32768/math.pi)} {round(b*32768/math.pi)} 1'
def add(name,m,cla=99,pivot=(0,0,0),states=None):
 fn=name+'.srf';packs[fn]=m.srf();n=node(name,fn,cla);n=dnm.edit(n,'POS ',' '.join(map(str,pivot))+' 0 0 0 1')
 if states:
  a=n.index('NST 1');b=next(i for i,s in enumerate(n) if s.startswith('POS '));n[a:b]=['NST '+str(len(states))]+['STA '+s for s in states]
 nodes.append(n)
for name,m in parts.items():
 if name in groups:
  sel,cla,ax,a0,a1=groups[name];pivot,a=axis(ax)
  if name=='Canopy':
   q=np.array(m.v);rear=q[q[:,2]<q[:,2].min()+.06];pivot=np.array([rear[:,0].mean(),rear[:,1].min(),rear[:,2].mean()]);a=np.array([1.,0,0])
  if name in ['GearL','GearR']:a=np.array([1.,0,0]);a0=-math.pi/2
  m.shift(*(-pivot));st=[state(a0,a),state(a1,a)] if name.startswith('Gear') else [state(a0,a),state(a1,a)] if name.startswith('Door') else [state(0,a),state(a0,a)] if name=='Canopy' else [state(0,a),state(a0,a),state(a1,a)]
  add(name,m,cla,pivot,st);stats[name]={'pivot':pivot.tolist(),'axis':a.tolist(),'angles':[a0,a1]}
 else:add(name,m,0 if name=='Hull' else 99)
# Recessed gear wells: doors removed from the hull, their original edges retained.
# Double sided walls and an inset backing prevent daylight through the open bays.
for name in ['DoorN','DoorL','DoorR']:
 ids=assigned[name];well=Mesh();edges=Counter();points={}
 for i in ids:
  f=l['faces'][i];vs=[tuple(np.round(p[v[0]],6)) for v in f['v']]
  # Keep only the main door sheet, not its bevels.
  for a,b in zip(vs,vs[1:]+vs[:1]):edges[tuple(sorted((a,b)))]+=1
  back=[(x,min(y+.45,-.12),z) for x,y,z in vs];well.face(back,(38,43,48));well.face(back[::-1],(38,43,48))
 for (a,b),count in edges.items():
  if count!=1:continue
  aa=(a[0],min(a[1]+.45,-.12),a[2]);bb=(b[0],min(b[1]+.45,-.12),b[2]);vs=[a,b,bb,aa];well.face(vs,(56,61,66));well.face(vs[::-1],(56,61,66))
 add('Well'+name,well,151)
# Hidden opaque body shell from the source geometric LOD, with real bay cutouts.
from gear_v3 import cut_bay
coarse=lods[2];cp=np.array([cv(v) for v in coarse['points']]);cp[:,0]*=.96;cp[:,1]+=.10
ids=set()
for sel in ['component01','component02','component05']:
 ids|={i for i,b in enumerate(coarse['tags'][sel][len(cp):]) if b}
inner=Mesh()
for i in ids:inner.face([tuple(cp[v[0]]) for v in coarse['faces'][i]['v']],(36,41,47))
for rect in [(-.48,.48,4.05,6.45),(-1.94,-.70,-4.15,-.52),(.70,1.94,-4.15,-.52)]:cut_bay(inner,rect)
# Double sided only on the hidden inner shell, not emissive.
for inds,c,b in list(inner.f):inner.face([inner.v[i] for i in inds[::-1]],c)
add('OpaqueInternalHull',inner)

# Dark recessed backs behind the source intake fans: no daylight between blades.
backs=Mesh()
for sel in ['rotor','rotor_R']:
 q=p[sorted({v[0] for i in select(sel) for v in l['faces'][i]['v']})];lo=q.min(0);hi=q.max(0);c=(lo+hi)/2
 backs.box(c[0],c[1],c[2]-.06,hi[0]-lo[0]+.06,hi[1]-lo[1]+.06,.05,(23,27,32))
add('IntakeBacks',backs)

# Opaque cockpit floor and rear bulkhead, independent of the moving canopy.
liner=Mesh();liner.box(0,.02,5.00,.78,.20,2.40,(29,34,39));liner.box(0,.34,3.92,.80,.76,.12,(31,36,41));add('CockpitLiner',liner)
# Fixed non-vectoring nozzles. No thrust-vectoring animation is assumed for S-37.
for side,sel,cla in [('L','EngineL',110),('R','EngineR',111)]:
 ids=select(sel);q=p[sorted({v[0] for i in ids for v in l['faces'][i]['v']})];center=q.mean(0);x,y=center[:2];z=q[:,2].min();root=q[:,2].max();r=.40
 inner=Mesh()
 for k in range(24):
  aa=k*math.pi/12;bb=(k+1)*math.pi/12
  poly=[(x+.60*math.cos(aa),y+.60*math.sin(aa),root+.04),(x+.60*math.cos(bb),y+.60*math.sin(bb),root+.04),(x+.365*math.cos(bb),y+.365*math.sin(bb),z+.012),(x+.365*math.cos(aa),y+.365*math.sin(aa),z+.012)]
  inner.face(poly,(28,33,39));inner.face(poly[::-1],(28,33,39))
 back=[(x+.60*math.cos(k*math.pi/12),y+.60*math.sin(k*math.pi/12),root+.04) for k in range(24)]
 inner.face(back,(18,21,25));inner.face(back[::-1],(18,21,25));add('NozzleInterior'+side,inner)
 # Overlapping rigid petals hinge at the nozzle root; class 120 follows throttle.
 root=q[:,2].max();length=root-z
 for k in range(20):
  theta=(k+.5)*2*math.pi/20;radial=np.array([math.cos(theta),math.sin(theta),0.]);tangent=np.array([-math.sin(theta),math.cos(theta),0.]);pivot=np.array([x,y,root])+radial*.58
  petal=Mesh();a=np.array([x,y,root])+radial*.58;b=np.array([x,y,z])+radial*.43
  verts=[a-tangent*.112,a+tangent*.112,b+tangent*.112,b-tangent*.112]
  # The wide overlapping leaves cover their neighbours throughout opening.
  outer=[tuple(v-pivot) for v in verts];inner=[tuple(np.array(v)-radial*.018) for v in outer]
  n=np.cross(np.array(outer[1])-outer[0],np.array(outer[2])-outer[0])
  if np.dot(n,radial)<0:outer=outer[::-1];inner=inner[::-1]
  petal.face(outer,(93+(k%2)*8,100+(k%2)*8,108+(k%2)*8));petal.face(inner[::-1],(40,45,50))
  for j in range(4):jj=(j+1)%4;petal.face([outer[j],inner[j],inner[jj],outer[jj]],(70,77,84))
  add('NozzlePetal'+side+str(k),petal,120,pivot,[state(0,tangent),state(-.14,tangent)])
 collar=Mesh();collar.tube((x,y,root+.12),(x,y,root-.04),.61,(66,73,81),24,inner=.55);add('NozzleCollar'+side,collar)

 flame=Mesh()
 for k in range(20):
  a=k*2*math.pi/20;b=(k+1)*2*math.pi/20
  flame.face([(x,y,z-1.65),(x+r*math.cos(b),y+r*math.sin(b),z),(x+r*math.cos(a),y+r*math.sin(a),z)],(238,135,62),True)
 add('Afterburner'+side,flame,cla,states=['0 0 0 0 0 0 0','0 0 0 0 0 0 1'])
liner=Mesh();liner.box(0,-.42,1.55,2.10,.60,3.0,(33,38,44));add('InnerFuselageSeal',liner)
# Red stars in the plane's own low-poly style, projected to actual wing surfaces.
def top_y(x,z):
 hits=[]
 for m in parts.values():
  # Parts are now pivot-local: only hull is needed for the fixed wing markings.
  if m is not parts.get('Hull'):continue
  for inds,c,b in m.f:
   pts=np.array([m.v[i] for i in inds])
   for k in range(1,len(pts)-1):
    a,bb,cc=pts[0],pts[k],pts[k+1];A=np.array([[a[0]-cc[0],bb[0]-cc[0]],[a[2]-cc[2],bb[2]-cc[2]]]);det=np.linalg.det(A)
    if abs(det)<1e-10:continue
    u,v=np.linalg.solve(A,[x-cc[0],z-cc[2]])
    if min(u,v,1-u-v)>-1e-6:hits.append(u*a[1]+v*bb[1]+(1-u-v)*cc[1])
 return max(hits) if hits else .1
marks=Mesh()
for sg in [-1,1]:
 cx=sg*6.5;cz=-2.8;pts=[]
 for k in range(10):
  a=k*math.pi/5;r=.40 if k%2==0 else .17;x=cx+r*math.sin(a);z=cz+r*math.cos(a);pts.append((x,top_y(x,z)+.012,z))
 center=(cx,top_y(cx,cz)+.012,cz)
 for k in range(10):
  poly=[center,pts[k],pts[(k+1)%10]]
  if np.cross(np.array(poly[1])-poly[0],np.array(poly[2])-poly[0])[1]<0:poly=poly[::-1]
  marks.face(poly,(188,42,46))
add('Stars',marks)
for fn in ['su47.dnm','su47_coarse.dnm']:dnm.write(dest/fn,packs,nodes)
# Use the source's separate geometric collision LOD; excludes all foreign proxies.
c=lods[2];coll=Mesh()
for f in c['faces']:coll.face([tuple(cv(c['points'][v[0]])) for v in f['v']],(90,100,110))
# Extend the coarse source collider to cover the actual wing tips and nose/probe.
for q in [p[p[:,2]>8],p[(p[:,0]>2)&(p[:,2]<-.9)&(p[:,2]>-6)&(abs(p[:,1])<.65)],p[(p[:,0]<-2)&(p[:,2]<-.9)&(p[:,2]>-6)&(abs(p[:,1])<.65)]]:
 q=np.unique(np.round(q,6),axis=0);h=ConvexHull(q)
 for tri,eq in zip(h.simplices,h.equations):
  a,b,c=q[tri]
  if np.dot(np.cross(b-a,c-a),eq[:3])<0:b,c=c,b
  coll.face([tuple(a),tuple(b),tuple(c)],(90,100,110))
# Also cover the actual canards, fin tips and long tail booms omitted by the coarse LOD.
extra=[p[p[:,2]<-8.5]]
for sel in ['canard_l','canard_r']:
 extra.append(p[sorted({v[0] for i in select(sel) for v in l['faces'][i]['v']})])
for sg in [-1,1]:extra.append(p[(p[:,0]*sg>2)&(p[:,0]*sg<3.1)&(p[:,1]>.25)&(p[:,2]<-5.2)])
for q in extra:
 q=np.unique(np.round(q,6),axis=0);h=ConvexHull(q)
 for tri,eq in zip(h.simplices,h.equations):
  a,b,c=q[tri]
  if np.dot(np.cross(b-a,c-a),eq[:3])<0:b,c=c,b
  coll.face([tuple(a),tuple(b),tuple(c)],(90,100,110))
(dest/'su47coll.srf').write_text('\n'.join(coll.srf())+'\n');(dest/'su47cockpit.srf').write_text('SURF\nE\n')
dat=(lab/'baseline_template.dat' if (lab/'baseline_template.dat').exists() else Path('/workspace/igraYS-Flight-Simulator/changes/su57-test-2/model-source/baseline_su57.dat')).read_text().replace('SU-57_FELON','SU-47_BERKUT').replace('COCKPITP 0m 1.46m 5.90m','COCKPITP 0m .65m 4.80m').replace('LEFTGEAR -2.0m -2.0m -2.3m','LEFTGEAR -1.6m -3.12m -3.32m').replace('RIGHGEAR 2.0m -2.0m -2.3m','RIGHGEAR 1.6m -3.12m -3.32m').replace('WHELGEAR 0m -2.0m 4.95m','WHELGEAR 0m -3.04m 4.34m').replace('18.5t','19.5t').replace('10.3t','9.0t')
dat=dat.replace('HTRADIUS 10.0m','HTRADIUS 12.0m').replace('MACHNGUN 1.15m .5m 4.3m','MACHNGUN .9m .55m 2.6m').replace('VAPORPO0 7.0m .12m -3.0m','VAPORPO0 -8.1m .0m -1.3m').replace('VAPORPO1 7.0m .12m -3.0m','VAPORPO1 8.1m .0m -1.3m');(dest/'su47.dat').write_text(dat)
(lab/'model-stats.json').write_text(json.dumps({'scale':scale.tolist(),'dimensions_m':[16.7,6.4,22.6],'source_sha256':hashlib.sha256((source/'Su_47_Berkut.p3d').read_bytes()).hexdigest(),'source_lods':len(lods),'excluded_foreign_proxy_faces':len(excluded),'moving_parts':stats,'nodes':len(nodes),'faces':sum(len(dnm.mesh(packs[dnm.fil(n)]).f) for n in nodes)},indent=2));print('MODEL',len(nodes),'nodes',len(p),'points')
