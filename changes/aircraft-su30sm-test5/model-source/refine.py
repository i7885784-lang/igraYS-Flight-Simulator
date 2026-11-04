from pathlib import Path
import numpy as np,json,math
from common import dnm,Mesh,add,state,transform,Rotation
r=Path(__file__).resolve().parent.parent;p,ns=dnm.read(r/'baseline/su30sm.dnm');lu={dnm.name(n):n for n in ns};audit={}
def position(n):return np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float)
def double(m):m.f += [(ids[::-1],c,b) for ids,c,b in list(m.f)];return m
def states_of(n):return [line for line in n if line.startswith('STA ')]
def set_states(n,values):
 ids=[i for i,line in enumerate(n) if line.startswith('STA ')];assert len(ids)==len(values)
 for i,line in zip(ids,values):n[i]=line
# Rudder neutral shape is retained. The hinge is swept in Y/Z and slightly
# canted in X; rotating around global Y had pulled the front edge out of its fin.
for n in ns:
 if not dnm.name(n).startswith('Rudder'):continue
 m=dnm.mesh(p[dnm.fil(n)]);pos=position(n);v=np.array(m.v)+pos;points=[];widths=[]
 for y in np.linspace(1.05,3.05,21):
  hits=[]
  for ids,c,b in m.f:
   for ia,ib in zip(ids,ids[1:]+ids[:1]):
    A,B=v[ia],v[ib]
    if (A[1]<=y<B[1]) or (B[1]<=y<A[1]):hits.append(A+(B-A)*(y-A[1])/(B[1]-A[1]))
  q=np.array(hits);front=q[q[:,2]>q[:,2].max()-.004].mean(0);front[0]=(q[:,0].min()+q[:,0].max())/2;points.append(front);widths.append([float(y),float(np.ptp(q[:,2]))])
 q=np.array(points);sx=np.polyfit(q[:,1],q[:,0],1)[0];sz=np.polyfit(q[:,1],q[:,2],1)[0];axis=np.array([sx,1.,sz]);axis/=np.linalg.norm(axis)
 set_states(n,[state(),state(Rotation.from_rotvec(axis*math.radians(15)).as_matrix()),state(Rotation.from_rotvec(-axis*math.radians(15)).as_matrix())])
 probe=pos+axis*1.6;old=Rotation.from_rotvec(np.array([0.,1.,0])*math.radians(15)).apply(probe-pos)+pos;new=Rotation.from_rotvec(axis*math.radians(15)).apply(probe-pos)+pos
 audit[dnm.name(n)]={'neutral_geometry_unchanged':True,'axis':axis.tolist(),'pivot':pos.tolist(),'max_angle_deg':15,'old_upper_hinge_drift_m':float(np.linalg.norm(old-probe)),'new_upper_hinge_drift_m':float(np.linalg.norm(new-probe)),'neutral_chord_samples_y_z_m':widths}
# Drop the clearance translation that made the wheel shields visibly detach.
# The old curved body patch becomes a separate bay shutter. A new compact
# wheel fairing is a rigid child of the wheel carrier, not a separately animated node.
for sg,title in [(-1,'Left'),(1,'Right')]:
 old=lu['GearDoor_'+title+'_WheelShield'];old_mesh=dnm.mesh(p[dnm.fil(old)]);R0,C0=transform(old,0);world=np.array(old_mesh.v)@R0.T+C0+position(old)
 edge=world[abs(world[:,0]-sg*1.03)<.006]
 if len(edge)<3:edge=world[np.argsort(abs(world[:,0]-sg*1.03))[:10]]
 pivot=edge.mean(0);axis=np.linalg.svd(edge-pivot,full_matrices=False)[2][0]
 if axis[2]<0:axis=-axis
 down_sign=-1 if np.cross(axis,world.mean(0)-pivot)[1]>0 else 1
 inner=Mesh();inner.v=list(map(tuple,world-pivot));inner.f=old_mesh.f.copy();poses=[]
 for k in range(101):
  g=k/100
  a=np.clip((g-.015)/.16,0,1);a=a*a*(3-2*a)
  b=np.clip((1-g)/.20,0,1);b=b*b*(3-2*b)
  u=min(a,b);poses.append(state(Rotation.from_rotvec(axis*math.radians(100)*down_sign*u).as_matrix(),pivot))
 add(p,ns,'MainWheelBayShutter_'+title,inner,210,poses)
 ns.remove(old);ns=[n for n in ns if not dnm.name(n).startswith(('GearShieldSupport_Cylinder_'+title,'GearShieldSupport_Rod_'+title))]
 carrier=lu['WheelCarrier_'+title]
 # Thin six-sided shield with a short upper neck, based on 7314 p5 D19/D20.
 yz=[(-.12,-.28),(.02,.36),(.27,.46),(.58,.24),(.64,-.12),(.26,-.38)];fairing=Mesh();x=-sg*.18;thick=.014
 for side in [-1,1]:
  ring=[(x+side*thick/2,y,z) for y,z in yz];centre=np.mean(ring,axis=0)
  for i in range(len(ring)):
   tri=[centre,ring[i],ring[(i+1)%len(ring)]];fairing.face(tri,(142,169,181) if side*sg<0 else (73,87,96))
 for i in range(len(yz)):
  y,z=yz[i];Y,Z=yz[(i+1)%len(yz)];fairing.face([(x-thick/2,y,z),(x+thick/2,y,z),(x+thick/2,Y,Z),(x-thick/2,Y,Z)],(101,120,132))
 fn='WheelFairing_'+title;add(p,ns,fn,double(fairing))
 brace=Mesh();brace.tube((sg*.23,0,0),(sg*.23,.56,0),.020,(125,139,147),12);brace.tube((sg*.23,.56,0),(-sg*.18,.56,0),.020,(125,139,147),12);brace.tube((-sg*.18,.56,0),(-sg*.18,.32,.08),.017,(125,139,147),12)
 bn='WheelFairingBrace_'+title;add(p,ns,bn,brace)
 children=[line[4:].strip('"') for line in carrier if line.startswith('CLD ')]+[fn,bn]
 carrier[:]=[line for line in carrier if not line.startswith('CLD ')];carrier[:]=dnm.edit(carrier,'NCH ',str(len(children)))
 for child in children:carrier.insert(-1,'CLD "'+child+'"')
 audit['main_'+title]={'wheel_fairing_rigid_child_of':'WheelCarrier_'+title,'no_independent_fairing_translation':True,'bay_shutter_closed_at_gear_up_and_down':True,'fairing_profile_yz_m':yz,'shutter_hinge':pivot.tolist(),'shutter_axis':axis.tolist()}
# The previous door meshes contained overlapping filling faces. Rebuild each
# moving door as one closed thin loft, sampling its original lower envelope.
# The airframe and the neutral fin meshes are not remeshed or smoothed.
for n in ns:
 name=dnm.name(n)
 if not name.startswith(('GearDoor_','MainWheelBayShutter_')):continue
 old=dnm.mesh(p[dnm.fil(n)]);R,C=transform(n,0);P=position(n);v=np.array(old.v)@R.T+C+P;tris=[];colors=[]
 for ids,c,b in old.f:
  for j in range(1,len(ids)-1):tris.append(v[[ids[0],ids[j],ids[j+1]]]);colors.append(c)
 tris=np.array(tris);a=tris[:,0];e=tris[:,1]-a;f=tris[:,2]-a;det=e[:,0]*f[:,2]-e[:,2]*f[:,0];valid=abs(det)>1e-12
 def sample(x,z):
  u=np.divide((x-a[:,0])*f[:,2]-(z-a[:,2])*f[:,0],det,out=np.zeros(len(det)),where=valid);w=np.divide(e[:,0]*(z-a[:,2])-e[:,2]*(x-a[:,0]),det,out=np.zeros(len(det)),where=valid);inside=valid&(u>=-1e-7)&(w>=-1e-7)&(u+w<=1.0000001)
  ids=np.where(inside)[0]
  if not len(ids):
   k=np.argmin((v[:,0]-x)**2+(v[:,2]-z)**2);return float(v[k,1]),(142,169,181)
  ys=a[ids,1]+u[ids]*e[ids,1]+w[ids]*f[ids,1];j=int(np.argmin(ys));return float(ys[j]),colors[int(ids[j])]
 lo,hi=v.min(0),v.max(0);xs=np.linspace(lo[0],hi[0],9);zs=np.linspace(lo[2],hi[2],max(12,int((hi[2]-lo[2])/.08)+1));grid=np.array([[[x,sample(x,z)[0],z] for z in zs] for x in xs]);mesh=Mesh();thick=np.array([0.,.008,0.])
 def face(q,c):mesh.face((np.array(q)-C-P)@R,c)
 for ix in range(len(xs)-1):
  for iz in range(len(zs)-1):
   q=grid[ix:ix+2,iz:iz+2];quad=[q[0,0],q[1,0],q[1,1],q[0,1]];col=sample((xs[ix]+xs[ix+1])/2,(zs[iz]+zs[iz+1])/2)[1]
   for ids in [(0,1,2),(0,2,3)]:
    face([quad[k] for k in ids],col);face([quad[k]+thick for k in ids[::-1]],(98,113,121))
 for edge in [grid[0],grid[-1],grid[:,0],grid[:,-1]]:
  for a,b in zip(edge[:-1],edge[1:]):face([a,b,b+thick,a+thick],(104,120,130))
 p[dnm.fil(n)]=double(mesh).srf();audit['loft_'+name]={'thin_continuous_panel':True,'thickness_y_m':.008,'closed_bounds_m':[lo.tolist(),hi.tolist()]}
p={fn:lines for fn,lines in p.items() if fn in {dnm.fil(n) for n in ns}}
(r/'runtime/aircraft').mkdir(parents=True,exist_ok=True)
tmp=r/'runtime/aircraft/su30sm.dnm.building';dnm.write(tmp,p,ns);tmp.replace(r/'runtime/aircraft/su30sm.dnm')
(r/'refinement.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2),flush=True)
