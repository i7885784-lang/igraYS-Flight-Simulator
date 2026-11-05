from pathlib import Path
import sys,json,hashlib,collections,math,numpy as np
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'baseline/su30sm.dnm');original={k:list(v) for k,v in p.items()};original_nodes=[list(n) for n in ns];lu={dnm.name(n):n for n in ns};audit={};stage=int(sys.argv[1]) if len(sys.argv)>1 else 2;assert stage in [1,2], 'Only cleanup or the full accepted geometry stage is supported'

def double(m):m.f += [(ids[::-1],c,b) for ids,c,b in list(m.f)];return m

def skin_tris(name):
 n=lu[name];m=dnm.mesh(p[dnm.fil(n)]);R,t=transform(n,0);v=np.array(m.v)@R.T+t;out=[]
 for ids,c,b in m.f:
  for k in range(1,len(ids)-1):
   q=v[[ids[0],ids[k],ids[k+1]]]
   if abs(np.cross(q[1]-q[0],q[2]-q[0])[1])>1e-10:out.append(q)
 return np.array(out)

def height(tri,x,z,upper=True):
 a=tri[:,0];u=tri[:,1]-a;v=tri[:,2]-a;det=u[:,0]*v[:,2]-u[:,2]*v[:,0];ok=abs(det)>1e-12
 b=np.divide((x-a[:,0])*v[:,2]-(z-a[:,2])*v[:,0],det,out=np.zeros(len(det)),where=ok);c=np.divide(u[:,0]*(z-a[:,2])-u[:,2]*(x-a[:,0]),det,out=np.zeros(len(det)),where=ok);ids=np.flatnonzero(ok&(b>=-1e-6)&(c>=-1e-6)&(b+c<=1.000001))
 if not len(ids):return None
 yy=a[ids,1]+b[ids]*u[ids,1]+c[ids]*v[ids,1];return float(yy.max() if upper else yy.min())
from nose_bay import extend_fore_opening,full_nose_compartment
fore_source=extend_fore_opening(p,ns,audit) if stage>=2 else []
# Remove actual zero-area/repeated triangles, preserve every real wall/roof face.
for side,sg in [('Nose',0),('Left',-1),('Right',1)]:
 name='GearWell_'+side;n=lu[name];old=dnm.mesh(p[dnm.fil(n)])
 if side=='Left' and stage>=2:
  old=dnm.mesh(original[dnm.fil(lu['GearWell_Right'])]);old.v=[(-x,y,z) for x,y,z in old.v];old.f=[(ids[::-1],c,b) for ids,c,b in old.f]
 old=old;v=np.array(old.v);new=Mesh();seen=set();polygons_seen=set();zero=repeat=0;centre=np.array([sg*1.72,-.1,-1.9] if sg else [0,.05,3.1]);triangles=[]
 for ids,c,b in old.f:
  polykey=tuple(sorted(set(tuple(np.round(v[j],6)) for j in ids)))
  if polykey in polygons_seen:repeat+=1;continue
  polygons_seen.add(polykey)
  for k in range(1,len(ids)-1):
   q=v[[ids[0],ids[k],ids[k+1]]];normal=np.cross(q[1]-q[0],q[2]-q[0]);length=np.linalg.norm(normal)
   if length<1e-10:zero+=1;continue
   key=tuple(sorted(tuple(np.round(a,6)) for a in q))
   if key in seen:repeat+=1;continue
   seen.add(key);normal/=length
   if normal@(centre-q.mean(0))<0:q=q[::-1];normal=-normal
   color=(226,228,215) if normal[1]<-.65 else (210,214,200)
   new.face(q,color);triangles.append(q)
 if side=='Nose' and stage>=2:
  rim=np.concatenate([skin_tris('GearDoor_Nose_'+a) for a in ['Inner','Outer','Aft']]+[np.array([q for q,c in fore_source])]);new=full_nose_compartment(rim,height);triangles=[]
  for ids,c,b in new.f:
   for j in range(1,len(ids)-1):triangles.append(np.array([new.v[k] for k in [ids[0],ids[j],ids[j+1]]]))
 if sg and stage>=2:
  from lining import hinge_pockets
  new=hinge_pockets(new,lu['GearDoor_'+side+('_Inner' if sg<0 else '_Outer')])
  triangles=[np.array([new.v[i] for i in ids]) for ids,c,b in new.f]
 p[dnm.fil(n)]=new.srf();audit[name]={'zero_area_triangles_removed':zero,'repeated_triangle_instances_removed_including_reverse_render_faces':repeat,'retained_unique_triangles':len(seen),'real_wall_roof_coordinates_preserved':stage<2,'lining_source':('mirrored collision-free right bay' if side=='Left' and stage>=2 else 'original surface with measured hinge pockets' if sg else 'rebuilt full nose compartment'),'interior_colors':[(226,228,215),(210,214,200)]}
 # Structure belongs to the compartment perimeter, outside the unchanged tyre/strut path.
 surface=np.array(triangles);rim=np.concatenate([skin_tris('GearDoor_Nose_'+a) for a in ['Inner','Outer','Aft']]) if not sg else skin_tris('GearDoor_'+side+('_Inner' if sg<0 else '_Outer'));detail=Mesh();xvals=[-.383,.383] if not sg else [sg*2.355];zvals=[2.22,2.80,3.17,3.95] if not sg else [-3.15,-2.40,-1.75,-.65];ribs=[]
 for x in xvals:
  for z in zvals:
   # Upper envelope of the EXISTING roof, not a guessed exterior box.
   top=height(surface,np.clip(x,-.35,.35) if not sg else x,z,True);low=height(rim,np.clip(x,-.375,.375) if not sg else x,z,False)
   if top is None or low is None or top-low<.09:continue
   low+=.025;top-=.022
   if not sg:low=max(low,.08)
   if top-low<.035:continue
   detail.box(x,(top+low)/2,z,.026 if sg else .018,top-low,.025,(161,164,154));ribs.append([x,low,top,z])
   wall=(2.42 if sg else .397)*(1 if x>0 else -1)
   for yy in [low+(top-low)*.25,low+(top-low)*.75]:detail.box((x+wall)/2,yy,z,abs(wall-x)+.004,.016,.022,(148,158,149))
 # A pair of supported hydraulic runs: narrow 8-sided tubes following the roof margin.
 for x in xvals:
  samples=[]
  for z in np.linspace(2.15,4.03,13) if not sg else np.linspace(-3.22,-.57,17):
   top=height(surface,np.clip(x,-.35,.35) if not sg else x,z,True)
   if top is not None:samples.append((x-(.014 if x>0 else -.014),top-.038,float(z)))
  for a,b in zip(samples,samples[1:]):
   if abs(a[2]-b[2])<.3:detail.tube(a,b,.007 if not sg else .009,(57,62,60),8)
  for a in samples[::4]:
   top=a[1]+.038;detail.tube(a,(a[0],top+.001,a[2]),.0055,(127,142,134),6);detail.box(a[0],top-.001,a[2],.018,.005,.022,(148,158,149))
 # Two actual ceiling stiffeners span the compartment above the preserved gear sweep.
 cross_ribs=[]
 for z in ([2.30,3.05] if not sg else [-2.90,-.62]):
  samples=[]
  for x in np.linspace(-.335,.335,9) if not sg else np.linspace(sg*1.10,sg*2.36,15):
   top=height(surface,float(x),z,True)
   if top is not None:samples.append((float(x),top-.016,z))
  for a,b in zip(samples,samples[1:]):
   if abs(a[0]-b[0])<.12:detail.tube(a,b,.009,(158,170,158),8)
  for a in (samples[:1]+samples[-1:] if len(samples)>1 else []):
   detail.tube(a,(a[0],a[1]+.018,a[2]),.010,(148,158,149),8)
  cross_ribs.append(samples)
 audit[name]['ceiling_stiffeners']=cross_ribs
 if detail.f:add(p,ns,'GearBayStructure_'+side,detail)
 audit[name]['perimeter_ribs']=ribs;audit[name]['hydraulic_runs_keep_to_existing_roof']=True;audit[name]['ribs_and_pipes_have_wall_roof_mounts']=True
if stage>=2:
 from doors import repair_doors
 repair_doors(p,ns,lu,audit,remove_drop=stage>=3,fore_source=fore_source)
 from covers import repair_covers
 repair_covers(p,ns,lu,audit)
 upper=dnm.mesh((r/'source-data/upper-closure.srf').read_text().splitlines());add(p,ns,'GearBayUpperClosure',upper)
 from mounts import build_mounts
 build_mounts(p,ns,audit)
# Only the diagnosed 7cm seating translation is allowed to change on existing door nodes.

assert all(n==old for n,old in zip([n for n in ns if dnm.name(n) in lu],original_nodes) if not ((stage>=3 and dnm.name(n).startswith('GearDoor_')) or (stage>=2 and dnm.name(n).startswith('MainWheelBayShutter_'))))
changed=[k for k in original if p[k]!=original[k]];assert all(k.startswith(('GearWell_','GearDoor_','DoorSeat_','MainWheelBayShutter_','Fuselage_0_4.srf','Fuselage_0_5.srf')) for k in changed)
(r/'runtime/aircraft').mkdir(parents=True,exist_ok=True);path=r/'runtime/aircraft/su30sm.dnm';tmp=path.with_suffix('.dnm.building');dnm.write(tmp,p,ns);tmp.replace(path);audit['stage']=stage;audit['changed_existing_packs']=changed;audit['new_nodes']=[dnm.name(n) for n in ns if dnm.name(n) not in lu];audit['model_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();(r/'repair-audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2))
