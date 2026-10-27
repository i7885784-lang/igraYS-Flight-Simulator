"""Geometry-only FlightGear AC3D -> YSFlight DNM. No FlightGear code is executed."""
from pathlib import Path
import json,math,re,hashlib,copy,warnings
import numpy as np
from scipy.spatial import cKDTree,ConvexHull
from scipy.spatial.transform import Rotation
import xml.etree.ElementTree as ET
from ac_reference import AC
from mesh import Mesh,node
import dnm
from corrections import construct,add_gears,add_bays,add_brake,add_tip_launchers
from gear_v3 import cut_bay
HERE=Path(__file__).resolve().parent
DEST=HERE/'runtime/aircraft';DEST.mkdir(parents=True,exist_ok=True)
META={}
def normal(q):
 return np.sum(np.cross(q,np.roll(q,-1,axis=0)),axis=0)
def double(m):
 for f,c,b in list(m.f):m.face([m.v[i] for i in f[::-1]],c,b)
 return m
def sta(R=np.eye(3),t=np.zeros(3),show=1):
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');h,p,b=Rotation.from_matrix(R).as_euler('YXZ')
 return ' '.join(map(str,[*np.round(t,7),round(-h*32768/math.pi),round(-p*32768/math.pi),round(b*32768/math.pi),show]))
for kind in ['su27','mig29']:
 su=kind=='su27';root=HERE/'upstream'/kind;offset=np.array([0.,0.,10. if su else 8.05]);C=np.array([[0.,-1,0],[0,0,1],[-1,0,0]])
 def cv(q):return C@np.array(q)+offset
 def vec(q):return C@np.array(q)
 ac=AC(root/('Su-27.ac' if su else 'mesh_airframe.ac'))
 for o in ac.objects:o['v']=(np.array(o['v'])+offset).tolist()
 xml=ET.parse(root/('SU-27.xml' if su else 'Mig-29.xml')).getroot();animations=xml.findall('animation')
 packs={};nodes=[];stats={};surfaces={};hull=Mesh();removed_duplicates=0
 def add(name,m,cla=99,states=None):
  if not m.f:return
  name=re.sub('[^A-Za-z0-9_]','_',name);fn=name+'.srf';packs[fn]=m.srf();n=node(name,fn,cla)
  if states:
   i=n.index('NST 1');j=n.index('POS 0 0 0 0 0 0 1');n[i:j]=['NST '+str(len(states))]+['STA '+s for s in states]
  nodes.append(n)
 def rotation(a,deg):
  center=a.find('center');ax=a.find('axis')
  if ax is None:return np.eye(3),np.zeros(3)
  def vals(e,suffix):return [float(e.findtext(k+suffix,'0')) for k in ['x','y','z']]
  if ax.find('x1-m') is not None:
   p=cv(vals(ax,'1-m'));end=cv(vals(ax,'2-m'));axis=end-p
  else:p=offset.copy();axis=vec(vals(ax,''))
  if center is not None:p=cv(vals(center,'-m'))
  axis/=np.linalg.norm(axis);R=Rotation.from_rotvec(axis*math.radians(deg)).as_matrix();return R,p-R@p
 def ctrl(name,prop=None):
  return next((a for a in animations if a.findtext('type')=='rotate' and name in [e.text for e in a.findall('object-name')] and (prop is None or prop in a.findtext('property',''))),None)
 def ctrlstates(a,unipolar=False):
  angle=float(a.findtext('factor','0'));return [sta()]+[sta(*rotation(a,q*angle)) for q in ([1] if unipolar else [1,-1])]
 # Static duplicates in the Su-27 source must not cover the moving parts.
 moving=[o for o in ac.objects if o['name'].startswith(('WNG_','ELV_','TF_')) or o['name']=='HULL_Speedbrake_Outer'] if su else []
 tree=cKDTree(np.concatenate([np.array(o['v']) for o in moving])) if moving else None
 canopytree=cKDTree(np.array(next(o['v'] for o in ac.objects if o['name']=='GLS_Canopy_Rear.001'))) if su else None
 rig,rig_info,bays=construct(kind,ac,sta)
 framemesh=Mesh();glass=Mesh();gearparts=[];restored_doors=Mesh();intake_faces=[];brake_mesh=None
 for o in ac.objects:
  name=o['name'];m=Mesh();v=np.array(o['v']);special=None;states=None;cla=99
  if su and name=='Canopy':continue # duplicate frame layer
  if su and name=='SpeedbrakePushrod':continue # replace with connected telescopic support
  if name in rig or (su and name=='UC_Nose_Rear_Post'):continue
  if not su and name.startswith(('fwdgeardoor','reargeardoor','fwdnosegear','nosegeardoor')):
   for f in o['f']:
    if len(f)>=3:restored_doors.face([tuple(v[i]) for i in f],(95,113,115))
   continue
  if not su and ('well' in name.lower()):continue
  if not su and name.startswith('IntakeScreen'):
   intake_faces.append(o);continue
  if su and name.startswith(('WNG_','ELV_','TF_')):
   cla=220 if 'Left_Flaperon' in name else 221 if 'Right_Flaperon' in name else 226 if name.startswith('TF_') else 228 if name.endswith('Left') else 229
   states=ctrlstates(ctrl(name))
  elif not su and name in ['AileronL','AileronR','FlapsL','FlapsR','SlatsL','SlatsR','RudderL','RudderR','StabilizerL','StabilizerR']:
   cla={'AileronL':220,'AileronR':221,'FlapsL':222,'FlapsR':223,'SlatsL':224,'SlatsR':225,'RudderL':226,'RudderR':227,'StabilizerL':228,'StabilizerR':229}[name];states=ctrlstates(ctrl(name))
  if name in ['AirBrakeU','AirBrakeB']:cla=212;states=ctrlstates(ctrl(name),True)
  if not su and name.startswith('Louvers'):
   cla=217;a=ctrl(name);angle=float(a.findall('interpolation/entry')[-1].findtext('dep'));states=[sta(),sta(*rotation(a,angle))] # native ground protection state
  if not su and name in ['Canopy','CanopyFrame']:
   R=Rotation.from_rotvec(np.array([-.70,0,0])).as_matrix();pivot=np.array([0,1.08,8.05-5.84]);cla=211;states=[sta(),sta(R,pivot-R@pivot)]
  if su and name in ['GLS_Canopy_Rear.001','GLS_Canopy_Rear']:cla=211;R=Rotation.from_rotvec(np.array([-.65,0,0])).as_matrix();pivot=np.array([0,1.05,3.30]);states=[sta(),sta(R,pivot-R@pivot)]
  for inds in o['f']:
   if len(inds)<3:continue
   q=v[inds];c=q.mean(0);col=(119,151,175) if su else (122,147,145)
   # Discard duplicate moving skins merged into static Su-27 hull.
   if su and name=='HULL_Hull_Upper.001':
    if tree is not None and np.max(tree.query(q)[0])<.006:removed_duplicates+=1;continue
    if np.max(canopytree.query(q)[0])<.006:removed_duplicates+=1;continue
    if np.max(abs(q[:,0]))<.56 and q[:,1].min()>.975 and q[:,2].min()>3.295 and q[:,2].max()<5.40:
     framemesh.face([tuple(p) for p in q],(69,88,102));continue
   if su and name=='GLS_Canopy_Rear.001':col=(69,88,102)
   elif ('Canopy' in name or 'Windscreen' in name) and 'Frame' not in name:col=(73,111,139,125)
   elif su and name=='object.001':col=(73,111,139,125)
   elif 'Tyre' in name or 'wheel' in name.lower():col=(32,36,40)
   elif name.startswith('UC_') or name.startswith(('gear1','gear2','nosegear')):col=(165,176,182)
   elif any(s in name.lower() for s in ['well','duct','engine','flameholder','combustion']):col=(34,40,45)
   elif name=='object' or 'interior' in name.lower():col=(36,43,48)
   elif c[2]>(8.0 if su else 6.2):col=(211,218,218)
   elif c[1]<(-.45 if su else -.30):col=(97,117,130) if su else (95,113,115)
   elif c[1]>.15 and (math.sin(c[2]*1.3)+.6*math.cos(c[0]*1.4))>.5:col=(79,110,139) if su else (79,106,104)
   if not su and name=='fuselage' and .30<abs(c[0])<1.12 and -.92<c[1]<.04 and .65<c[2]<2.38:col=(40,51,58)
   m.face([tuple(p) for p in q],col)
  if su and name.startswith('HULL_Hull_Upper'):hull.merge(m);continue
  if not su and name in ['fuselage','WingL','WingR']:hull.merge(m);continue
  if su and name=='HULL_Speedbrake_Outer':brake_mesh=m;continue
  if su and name=='GLS_Canopy_Rear.001':m.merge(framemesh) # frames also added after hull parsed
  if name in ['WingL','WingR','fuselage','Vstabs']:surfaces[name]=copy.deepcopy(m)
  double(m);add(name,m,cla,states);stats[name]={'class':cla,'faces':len(m.f),'states':len(states or [1])}
 if su:
  # Frame faces were collected from the merged hull later than the glass object.
  R=Rotation.from_rotvec(np.array([-.65,0,0])).as_matrix();pivot=np.array([0,1.05,3.30]);double(framemesh);add('CanopyMovingFrame',framemesh,211,[sta(),sta(R,pivot-R@pivot)])
 # Real bay geometry and mechanically connected fold/swivel assembly.
 if not su:hull.merge(restored_doors)
 bay_info=add_bays(hull,bays,add,double,sta,kind)
 double(hull);add('Hull',hull);surfaces['Hull']=hull
 add_gears(ac,rig,add,double,sta)
 brake_info=add_brake(brake_mesh,add,double,sta) if su else None
 tip_stations=add_tip_launchers(add) if su else None
 if not su:
  for i,o in enumerate(intake_faces):
   duct=Mesh();cover=Mesh()
   for ids in o['f']:
    if len(ids)<3:continue
    q=np.array(o['v'])[ids];center=q.mean(0);back=q.copy();back[:,0]=center[0]+(q[:,0]-center[0])*.80;back[:,1]=center[1]+(q[:,1]-center[1])*.80;back[:,2]-=1.60
    for j in range(len(q)):
     k=(j+1)%len(q);duct.face([tuple(q[j]),tuple(q[k]),tuple(back[k]),tuple(back[j])],(53,64,70))
    duct.face([tuple(v) for v in back],(19,25,29));cover.face([tuple(v+np.array([0,0,-.025])) for v in q],(70,82,87))
   double(duct);double(cover);add('OpenIntakeDuct'+str(i),duct);add('GroundFODScreen'+str(i),cover,216,[sta(show=0),sta(show=1)])
 # Seal cockpit behind seat and below instruments: ordinary lit opaque surfaces.
 interior=Mesh();cz=4.5 if su else 3.8;interior.box(0,.35,cz,.80,.15,2.0,(31,38,44));interior.box(0,.72,cz-.95,.78,.85,.12,(35,41,46));add('CockpitLiner',interior)
 if not su:
  seat=Mesh();seat.box(0,.59,3.55,.43,.17,.62,(52,61,60));seat.box(0,.89,3.27,.43,.59,.14,(49,57,56));seat.box(0,1.24,3.27,.29,.18,.16,(37,44,44));add('OwnSeat',seat)
 # Complete the source MiG exhaust from its own editable petal geometry.
 if not su:
  segment=AC(root/'mesh_nozzleseg.ac');petals=Mesh()
  for side in [-1,1]:
   for k in range(18):
    R=Rotation.from_rotvec(np.array([0.,0,k*math.pi/9])).as_matrix()
    for o in segment.objects:
     if not o['name'].endswith('.L'):continue
     v=np.array(o['v'])@R.T+np.array([side*.957,-.176,8.05-13.847])
     for f in o['f']:petals.face([tuple(v[i]) for i in f],(79+(k%2)*12,87+(k%2)*12,95+(k%2)*12))
  double(petals);add('SourceNozzlePetals',petals)
 # Geometry-only exhaust, fixed axes. Own metallic rings and flame geometry.
 if su:engines=[(s*1.235,-.26,-8.32,.54) for s in [-1,1]]
 else:engines=[(s*.957,-.176,8.05-14.55,.43) for s in [-1,1]]
 for side,(x,y,z,r) in enumerate(engines):
  pipe=Mesh()
  for k in range(24):
   a=k*math.pi/12;b=(k+1)*math.pi/12
   q=[(x+r*math.cos(a),y+r*math.sin(a),z+.70),(x+r*math.cos(b),y+r*math.sin(b),z+.70),(x+.84*r*math.cos(b),y+.84*r*math.sin(b),z),(x+.84*r*math.cos(a),y+.84*r*math.sin(a),z)]
   pipe.face(q,(75+(k%2)*12,82+(k%2)*12,90+(k%2)*12))
  pipe.face([(x+r*math.cos(k*math.pi/12),y+r*math.sin(k*math.pi/12),z+.68) for k in range(24)],(19,24,30));double(pipe);add('Exhaust'+str(side),pipe)
  flame=Mesh()
  for k in range(24):
   a=k*math.pi/12;b=(k+1)*math.pi/12
   flame.face([(x,y,z-1.5),(x+r*.75*math.cos(b),y+r*.75*math.sin(b),z-.01),(x+r*.75*math.cos(a),y+r*.75*math.sin(a),z-.01)],(238,133,57),True)
  double(flame);add('Afterburner'+str(side),flame,110+side,[sta(show=0),sta(show=1)])
 # Red stars projected on upper wing; own polygon markings, no source images.
 marks=Mesh();skin=Mesh()
 for m in surfaces.values():skin.merge(m)
 def top(x,z):
  hits=[]
  for f,c,b in skin.f:
   q=np.array([skin.v[i] for i in f])
   for k in range(1,len(q)-1):
    a,b,c=q[0],q[k],q[k+1];A=np.array([[a[0]-c[0],b[0]-c[0]],[a[2]-c[2],b[2]-c[2]]]);det=np.linalg.det(A)
    if abs(det)<1e-10:continue
    u,v=np.linalg.solve(A,[x-c[0],z-c[2]])
    if min(u,v,1-u-v)>-1e-5:hits.append(u*a[1]+v*b[1]+(1-u-v)*c[1])
  return max(hits) if hits else .3
 for s in [-1,1]:
  x=s*(5.8 if su else 4.3);z=-5.1 if su else -3.2;pts=[]
  for k in range(10):
   a=k*math.pi/5;r=.38 if k%2==0 else .16;px=x+r*math.sin(a);pz=z+r*math.cos(a);pts.append((px,top(px,pz)+.012,pz))
  center=(x,top(x,z)+.012,z)
  for k in range(10):marks.face([center,pts[(k+1)%10],pts[k]],(185,39,44))
 double(marks);add('OwnStars',marks)
 for fn in [kind+'.dnm',kind+'_coarse.dnm']:dnm.write(DEST/fn,packs,nodes)
 # Component convex collision hulls; avoid one huge convex hull between wings.
 coll=Mesh()
 for o in ac.objects:
  if any(s in o['name'].lower() for s in ['gear','wheel','uc_','canopy','glass']):continue
  q=np.unique(np.round(o['v'],4),axis=0)
  try:
   h=ConvexHull(q)
   for ids,eq in zip(h.simplices,h.equations):
    p=q[ids]
    if np.dot(np.cross(p[1]-p[0],p[2]-p[0]),eq[:3])<0:p=p[::-1]
    coll.face([tuple(a) for a in p],(90,100,110))
  except Exception:pass
 (DEST/(kind+'coll.srf')).write_text('\n'.join(coll.srf())+'\n');(DEST/(kind+'cockpit.srf')).write_text('SURF\nE\n')
 dat=(HERE/(kind+'_template.dat')).read_text()
 params={'LEFTGEAR':('-2.18m -2.52m -3.64m' if su else '-1.61m -1.74m -1.80m'),'RIGHGEAR':('2.18m -2.52m -3.64m' if su else '1.61m -1.74m -1.80m'),'WHELGEAR':('0m -2.30m 2.20m' if su else '0m -1.74m 1.74m'),'COCKPITP':('0m 1.42m 4.8m' if su else '0m 1.30m 3.7m'),'HTRADIUS':'13m' if su else '10m'}
 for key,val in params.items():dat=re.sub(r'(?m)^'+key+r'\s+.*$',key+' '+val,dat)
 if su:
  lines=dat.splitlines();slots=[i for i,v in enumerate(lines) if v.startswith('HRDPOINT')]
  for idx,xyz in enumerate(tip_stations):
   tail=' '.join(lines[slots[idx]].split()[4:]);lines[slots[idx]]='HRDPOINT '+' '.join(f'{v:.6f}m' for v in xyz)+' '+tail
  dat='\n'.join(lines)+'\n'
 (DEST/(kind+'.dat')).write_text(dat)
 META[kind]={'objects':stats,'duplicate_static_faces_removed':removed_duplicates,'nodes':len(nodes),'faces':sum(len(dnm.mesh(p).f) for p in packs.values()),'collider_faces':len(coll.f),'coordinate_translation':offset.tolist(),'imported_source':'Su-27.ac' if su else 'mesh_airframe.ac','gear_rig':rig_info,'bays':bay_info,'brake_correction':brake_info,'tip_stations':tip_stations,'output_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in DEST.glob(kind+'*')}}
 print(kind,META[kind]['nodes'],META[kind]['faces'],'duplicates',removed_duplicates,flush=True)
(HERE/'model-stats.json').write_text(json.dumps(META,indent=2))
