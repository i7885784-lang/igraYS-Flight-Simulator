"""Test-5 Su-27: fixed intake skins, separate wheel/strut doors, connected fork.
Only the selected original FG geometry is used. No reference-fork mesh is copied.
"""
from pathlib import Path
import sys,json,math,warnings,shutil
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'model-source'))
import dnm
from mesh import Mesh,node
from ac_reference import AC
from gear_v3 import clip,normal
from fit_internal import reference
from envelope import Envelope
rt=root/'runtime/aircraft';base=root/'working-base';base.mkdir(exist_ok=True)
for fn in ['su27.dnm','su27_coarse.dnm']:
 if not (base/fn).exists():shutil.copyfile(rt/fn,base/fn)
packs,nodes=dnm.read(base/'su27.dnm');lookup={dnm.name(n):n for n in nodes};old_names=set(lookup)
ac=AC(root/'model-source/upstream/su27/Su-27.ac')
for o in ac.objects:o['v']=(np.array(o['v'])+[0,0,10]).tolist()
source=[o for o in ac.objects if o['name'].startswith('HULL_Hull_Upper')];env=reference(ac,True)
planes_old=lambda sg:[(0,.35 if sg>0 else -2.15,True),(0,2.15 if sg>0 else -.35,False),(2,-4.02,True),(2,-.72,False),(1,.47,False)]
def carve(poly,planes):
 remaining=list(poly);outside=[]
 for axis,threshold,positive in planes:
  if len(remaining)<3:break
  q=clip(remaining,axis,threshold,not positive)
  if len(q)>=3:outside.append(q)
  remaining=clip(remaining,axis,threshold,positive)
 return outside,remaining

def colour(q):
 c=np.mean(q,0)
 if c[1]<-.45:return (97,117,130)
 if c[1]>.15 and math.sin(c[2]*1.3)+.6*math.cos(c[0]*1.4)>.5:return (79,110,139)
 return (119,151,175)

hull=dnm.mesh(packs[dnm.fil(lookup['Hull'])]);restored=0
work_rects=[(.35,2.30,-4.60,-.70),(-2.30,-.35,-4.60,-.70)]
fixed=Mesh()
for ids,col,bright in hull.f:
 polys=[[hull.v[i] for i in ids]]
 for x0,x1,z0,z1 in work_rects:
  updated=[]
  for q in polys:
   outside,inside=carve(q,[(0,x0,True),(0,x1,False),(2,z0,True),(2,z1,False),(1,.55,False)]);updated.extend(outside)
  polys=updated
 for q in polys:
  if len(q)>=3:fixed.face(q,col,bright)
face_map=json.loads((root/'model-source/su27-main-door-map.json').read_text())
assert __import__('hashlib').sha256((root/'model-source/upstream/su27/Su-27.ac').read_bytes()).hexdigest()==face_map['source_sha256']
# Include the original panel thickness and back faces, which were merged into
# the hull in this older source. Match geometry to the identified original skin.
import trimesh
source_hull=next(o for o in source if o['name']==face_map['object'])
sv=np.array(source_hull['v'])
complete_map={}
for side in ['L','R']:
 triangles=[]
 for face_id in face_map[side]:
  f=source_hull['f'][face_id]
  triangles.extend([[f[0],f[k],f[k+1]] for k in range(1,len(f)-1)])
 panel=trimesh.Trimesh(sv,np.array(triangles),process=False)
 selected=[]
 for face_id,f in enumerate(source_hull['f']):
  q=sv[f]
  if (q[:,0].mean()>0)!=(side=='L'):continue
  if q[:,2].min()<-4.60 or q[:,2].max()>-1.03:continue
  _,distance,_=trimesh.proximity.closest_point_naive(panel,np.concatenate([q,q.mean(0)[None,:]],0))
  if max(distance)<.026:selected.append(face_id)
 selected=sorted(set(selected)|set(range(576,662) if side=='L' else range(1227,1313)))
 complete_map[side]=selected
face_map['complete_original_panel_faces']=complete_map

doors={key:Mesh() for key in ['LWheel','LStrut','RWheel','RStrut']};cut=0;internal_removed=0
port_rects={}
for o in source:
 v=np.array(o['v'])
 for face_id,ids in enumerate(o['f']):
  q=list(v[ids]);door=None
  if o['name']==face_map['object']:
   door=next((title for title in ['L','R'] if face_id in complete_map[title]),None)
  if door:
   for key,poly in [(door+'Wheel',clip(q,2,-2.426,True)),(door+'Strut',clip(q,2,-2.426,False))]:
    if len(poly)>=3:doors[key].face(poly,colour(q));doors[key].face(poly[::-1],colour(q))
   cut+=1;continue
  for x0,x1,z0,z1 in work_rects:
   _,piece=carve(q,[(0,x0,True),(0,x1,False),(2,z0,True),(2,z1,False),(1,.55,False)])
   if len(piece)<3:continue
   # Replace old internal lining within the new upper compartment, while keeping
   # all external intake/airframe skins and a separate fixed air-duct ceiling.
   sg=1 if x0>0 else -1;ix0,ix1=(.85,2.25) if sg>0 else(-2.25,-.85)
   outside,inside=carve(piece,[(0,ix0,True),(0,ix1,False),(2,-4.55,True),(2,-.75,False),(1,-.13,True),(1,.50,False)])
   keep=list(outside)
   if len(inside)>=3:
    c=np.mean(inside,0);lo,hi,_=env.bounds(c.reshape(1,3))
    if c[1]<lo[0]+.012 or c[1]>hi[0]-.012:keep.append(inside)
    else:internal_removed+=1
   for poly in keep:
    if len(poly)>=3:fixed.face(poly,colour(q));fixed.face(poly[::-1],colour(q));restored+=1
hull=fixed;packs[dnm.fil(lookup['Hull'])]=hull.srf();wing=env
for title in ['L','R']:
 v=np.array(doors[title+'Wheel'].v+doors[title+'Strut'].v);port_rects[title]=(float(v[:,0].min()),float(v[:,0].max()),float(v[:,2].min()),float(v[:,2].max()))
door_volume=Envelope([{'v':m.v,'f':[f[0] for f in m.f]} for m in doors.values()],step=.01)
removed={n for n in old_names if n.startswith(('FlushGearDoorL','FlushGearDoorR','InternalGearBayL','InternalGearBayR','UpperHingeLinkL','UpperHingeLinkR')) or n=='FixedGearTrunnions' or n.startswith(('Gear_UC_Main_Left','Gear_UC_Main_Right'))}
nodes=[n for n in nodes if dnm.name(n) not in removed]
def sta(R=np.eye(3),t=np.zeros(3),show=1):
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');h,p,b=Rotation.from_matrix(R).as_euler('YXZ')
 return 'STA '+' '.join(map(str,[*np.round(t,7),round(-h*32768/math.pi),round(-p*32768/math.pi),round(b*32768/math.pi),show]))
def add(name,mesh,cla=99,states=None):
 assert mesh.f,name
 fn=name+'.srf';packs[fn]=mesh.srf();n=node(name,fn,cla)
 if states:
  i=next(i for i,s in enumerate(n) if s.startswith('NST '));j=next(i for i,s in enumerate(n) if s.startswith('POS '));n[i:j]=['NST '+str(len(states))]+states
 nodes.append(n)
def rot(axis,pivot,degrees):
 axis=np.array(axis,float);axis/=np.linalg.norm(axis);R=Rotation.from_rotvec(axis*math.radians(degrees)).as_matrix();return R,pivot-R@pivot

door_info={}
for name,m in doors.items():
 title=name[0];sg=1 if title=='L' else -1;v=np.array(m.v);z0,z1=v[:,2].min(),v[:,2].max();hx=(v[:,0].max() if sg>0 else v[:,0].min())
 ends=np.array([[hx,0,z] for z in [z0,z1]]);ys=[]
 for z in [z0,z1]:
  d=(v[:,0]-hx)**2+(v[:,2]-z)**2;ys.append(float(v[np.argmin(d),1]))
 ys=np.array(ys);pivot=np.array([hx,ys[0]+.006,z0]);axis=np.array([0,ys[1]-ys[0],z1-z0]);angle=105 if name.endswith('Wheel') else 85
 states=[sta(*rot(axis,pivot,sg*angle*np.clip(g/.20,0,1))) for g in np.linspace(0,1,101)];add('RootDoor'+name,m,210,states)
 door_info[name]={'pivot':pivot.tolist(),'axis':(axis/np.linalg.norm(axis)).tolist(),'angle':sg*angle,'faces':len(m.f),'bounds':[v.min(0).tolist(),v.max(0).tolist()]}
 # A recessed well stays INSIDE the original body; nothing projects below the intake.
for title,sg in [('L',1),('R',-1)]:
 x0,x1=(.85,2.25) if sg>0 else(-2.25,-.85);z0,z1=-4.55,-.75;m=Mesh()
 line=[]
 for (xa,za),(xb,zb) in [((x0,z0),(x1,z0)),((x1,z0),(x1,z1)),((x1,z1),(x0,z1)),((x0,z1),(x0,z0))]:
  line.extend((xa+(xb-xa)*t,za+(zb-za)*t) for t in np.linspace(0,1,25,endpoint=False))
 q=np.array([[x,0,z] for x,z in line]);lo,hi,_=env.bounds(q)
 for i in range(len(q)):
  j=(i+1)%len(q);pts=[(q[i,0],lo[i]+.004,q[i,2]),(q[j,0],lo[j]+.004,q[j,2]),(q[j,0],hi[j]-.004,q[j,2]),(q[i,0],hi[i]-.004,q[i,2])];m.face(pts,(45,59,69));m.face(pts[::-1],(45,59,69))
 add('UpperWell'+title,m)
 # The floor of the upper compartment is the FIXED roof of the intake duct.
 dx0,dx1=(.55,1.55) if sg>0 else(-1.55,-.55);floor=Mesh()
 profile=[(-4.55,-.13),(-3.10,-.13),(-2.40,-.25),(-.75,-.30)]
 for (za,ya),(zb,yb) in zip(profile,profile[1:]):
  pts=[(dx0,ya,za),(dx1,ya,za),(dx1,yb,zb),(dx0,yb,zb)];floor.face(pts,(45,59,69));floor.face(pts[::-1],(45,59,69))
 add('FixedDuctRoof'+title,floor)

fit=json.loads((root/'connected-main-fit-track.json').read_text());params=np.array(fit['parameters']);P=np.array(fit['pivot']);F=np.array(fit['fork_joint']);up=np.array(fit['fork_axis']);R1=Rotation.from_euler('XYZ',params[:3],degrees=True);rv=R1.as_rotvec();gears={}
# Change S onset here only when a collision establishes the need.
swivel_start=float(__import__('os').environ.get('SWIVEL_START','.55'))
swivel_path=json.loads((root/'swivel-path.json').read_text())['swivel_fraction']
for title,sg in [('L',1),('R',-1)]:
 mirror=np.diag([sg,1,1]);upper=Mesh();lower=Mesh();wheels=Mesh()
 for n in lookup.values():
  name=dnm.name(n)
  if not name.startswith('Gear_UC_Main_'+('Left' if sg>0 else 'Right')):continue
  m=dnm.mesh(packs[dnm.fil(n)])
  if 'Upper_St_' in name or 'Upper_S_' in name:upper.merge(m)
  elif '_Hub_' in name:
   if name.endswith('_wheel'):
    # Adapt the oversized source brake-rim diameter, preserving the fork neck.
    q=np.array(m.v);center=np.array([sg*2.1808,-1.9942,-3.6305]);weight=np.clip((-1.70-q[:,1])/.15,0,1)
    # The inner brake package must fit inside the bay rather than extend through
    # the duct wall. Keep the axle and stem neck in place; shorten its inboard cap.
    x=sg*q[:,0];xnew=2.146-(2.146-x)*(.176/.3416);q[:,0]=sg*(x+weight*np.maximum(xnew-x,0))
    q[:,1:]=center[1:]+(q[:,1:]-center[1:])*(1-.08*weight[:,None]);m.v=[tuple(v) for v in q]
   lower.merge(m)
  elif '_Tyre_' in name:
   # Su-27 KT-156D nominal outside diameter: 1030 mm (Airwar technical data).
   q=np.array(m.v);center=np.array([-1.9942,-3.6305]);radius=np.linalg.norm(q[:,1:]-center,axis=1).max();q[:,1:]=center+(q[:,1:]-center)*(.515/radius);m.v=[tuple(v) for v in q];wheels.merge(m)
 for mesh in [upper,lower,wheels]:mesh.shift(sg*.0178,0,0)
 q=np.array(upper.v);q[:,0]=sg*P[0]+(q[:,0]-sg*P[0])*.85;q[:,2]=P[2]+(q[:,2]-P[2])*.85;upper.v=[tuple(v) for v in q]
 lower.tube((sg*(P[0]+.09),-1.65,P[2]),(sg*(P[0]+.119),-1.65,P[2]),.025,(147,165,177),10)
 # Local clearance adjustment to the original tyre corners, in the closed pose.
 # This is a fixed mesh adaptation; wheels never change shape during animation.
 Rc=R1.as_matrix();tc=P-Rc@P;Sc=Rotation.from_rotvec(up*math.radians(params[3])).as_matrix();Ac=Rc@Sc;uc=Rc@(F-Sc@F+up*params[4])+tc
 points=np.array(wheels.v);M=mirror@Ac@mirror;tr=mirror@uc;world=points@M.T+tr;lo,hi,dist=env.bounds(world)
 dl,dt,dd=door_volume.bounds(world);lo=np.maximum(lo,np.where(dd<.012,dt,-100));delta=np.maximum(lo+.012-world[:,1],0)-np.maximum(world[:,1]+.012-hi,0)
 maximum=float(np.max(np.abs(delta)));assert maximum<.055,('Tyre clearance requires redesign',maximum)
 wheels.v=[tuple(q) for q in points+delta[:,None]*M[1,:]]
 # Restore a connected pair of torque links after the fork motion is validated.
 states=[];lowerstates=[]
 for g in np.linspace(0,1,101):
  fold=1-np.clip((g-.24)/.76,0,1);R=Rotation.from_rotvec(rv*fold).as_matrix();t=P-R@P;sf=float(np.interp(g,np.linspace(0,1,101),swivel_path));S=Rotation.from_rotvec(up*math.radians(params[3])*sf).as_matrix();A=R@S;u=R@(F-S@F+up*params[4]*fold)+t
  states.append(sta(mirror@R@mirror,mirror@t));lowerstates.append(sta(mirror@A@mirror,mirror@u))
 add('ConnectedMainStrut'+title,upper,210,states);add('ConnectedMainFork'+title,lower,210,lowerstates);add('ConnectedMainWheels'+title,wheels,210,lowerstates)
 from torque_links27 import build as torque_build
 torque=torque_build(title,sg,P,F,rv,up,params,swivel_path,add,sta)
 gears[title]={'fixed_hinge':(mirror@P).tolist(),'fork_joint':(mirror@F).tolist(),'strut_barrel_radial_scale':.85,'brake_housing_adapted':True,'tyre_corner_adjustment_m':maximum,'swivel_start_fold':swivel_start,'torque_links':torque}

# Keep unused packed records out of the actual model, but preserve the baseline on disk.
active={dnm.fil(n) for n in nodes};packs={k:v for k,v in packs.items() if k in active}
for fn in ['su27.dnm','su27_coarse.dnm']:dnm.write(rt/fn,packs,nodes)
(root/'upper-bay-model.json').write_text(json.dumps({'diagnostic_not_validated':True,'restored_intake_skin_pieces':restored,'cut_root_faces':cut,'internal_lining_replaced':internal_removed,'source_main_door_faces':face_map,'ports':port_rects,'doors':door_info,'main_gear':gears,'removed_old_nodes':sorted(removed),'fork_fit':fit,'torque_links_pending':False},indent=2));print('ROOT BAYS BUILT',len(nodes),'nodes; restored',restored,'cut',cut,'doors',[(k,len(v.f)) for k,v in doors.items()],flush=True)
