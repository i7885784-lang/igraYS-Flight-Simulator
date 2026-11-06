"""Local Su30SM visual polish, starting only from the verified 08e5e8fc GearBays model."""
from pathlib import Path
import sys,json,hashlib,copy,math,collections
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
base=r/'baseline/su30sm.dnm';assert hashlib.sha256(base.read_bytes()).hexdigest()=='08e5e8fc66098f87cd926526cf508e92d39848888c487d425a7213829465e5b4'
p,ns=dnm.read(base);old={k:list(v) for k,v in p.items()};oldns=copy.deepcopy(ns);lu={dnm.name(n):n for n in ns};audit={}
def replace_states(n,states):
 ids=[i for i,s in enumerate(n) if s.startswith('STA ')];assert len(ids)==len(states)
 for i,s in zip(ids,states):n[i]=s
def position(n):return np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float)
# Preserve rotational paths and deployment timing; reduce the proven-safe clearance slide only.
for n in ns:
 if not dnm.name(n).startswith(('GearDoor_','DoorHingePin_')):continue
 k=0
 for j,s in enumerate(n):
  if s.startswith('STA '):
   a=s.split();a[2]=str(round(float(a[2])+.04*min(1,k/1.5),7));n[j]=' '.join(a);k+=1
audit['doors']={'old_clearance_slide_m':.07,'new_clearance_slide_m':.03,'all_rotations_and_timing_preserved':True,'wheel_strut_and_inner_shutter_curves_unchanged':True}
# The shortened fixed fork still follows the retained 30mm slide, not the old 70mm slide.
source=dnm.mesh(p['DoorHingeForks.srf']);fork=Mesh()
# Existing fork vertex groups have 2 uprights + crossbar; map the lower fork region upward smoothly.
v=np.array(source.v)
# Recreate using exactly the previous construction, substituting just the lower fork height.
for n in ns:
 if not dnm.name(n).startswith('GearDoor_'):continue
 name=dnm.name(n);R,C=transform(n,0);R17,_=transform(n,17);ax=Rotation.from_matrix(R17@R.T).as_rotvec();ax/=np.linalg.norm(ax)
 if ax[2]<0:ax=-ax
 for z in ([-3.03,-1.05] if 'Nose' not in name else ([2.22,2.86] if 'Aft' in name else [3.32,3.93])):
  a=C+ax*(z-C[2])/ax[2]
  for dz in [-.031,.031]:
   e=a+ax*dz;fork.tube(e+[0,.016,0],e+[0,-.044,0],.010,(101,113,116),8)
  fork.tube(a+[0,-.044,0]-ax*.042,a+[0,-.044,0]+ax*.042,.012,(107,120,122),10)
p['DoorHingeForks.srf']=fork.srf()
# Canopy photos show a shallower raised position. This is a visual estimate, not a factory angle claim.
for n in ns:
 if dnm.cla(n)!=211:continue
 states=[s for s in n if s.startswith('STA ')];a=states[-1].split();a[5]=str(round(43/180*32768));replace_states(n,[states[0],' '.join(a)])
audit['canopy']={'old_deg':55,'new_deg':43,'basis':'Comparison with supplied raised-canopy rear photograph; approximate photographic fit, no certified dimension available','pivot_closed_geometry_materials_preserved':True}
# Brake retains original axis, pivot and closed surface. Recompute both actuator ends from actual attachment.
brake=lu['Air_Brake_1_20'];oldbrake=copy.deepcopy(brake);bp=position(brake);states=[s for s in brake if s.startswith('STA ')];a=states[-1].split();a[5]=str(-round(50/180*32768));replace_states(brake,[states[0],' '.join(a)])
cn=lu['AirbrakeActuator_Cylinder'];pn=lu['AirbrakeActuator_Piston'];cm=dnm.mesh(p[dnm.fil(cn)]);pm=dnm.mesh(p[dnm.fil(pn)]);L=max(v[1] for v in pm.v);R,T=transform(pn,0);B=T+R@np.array([0,L,0]);_,A=transform(cn,0)
def axis(a,b):
 y=b-a;y/=np.linalg.norm(y);z=np.cross([1.,0,0],y);z/=np.linalg.norm(z);return np.c_[np.cross(y,z),y,z]
lengths=[];cs=[];ps=[]
for u in np.linspace(0,1,21):
 # Match native YsShellDnmContainer::SetClassStateRecursive forward/up-vector interpolation.
 E=transform(brake,1)[0];z=(1-u)*np.array([0.,0,1])+u*E[:,2];z/=np.linalg.norm(z);y=(1-u)*np.array([0.,1,0])+u*E[:,1];x=np.cross(y,z);x/=np.linalg.norm(x);R=np.c_[x,np.cross(z,x),z];T=R@(B-bp)+bp;Q=axis(A,T);lengths.append(float(np.linalg.norm(T-A)));cs.append(state(Q,A));ps.append(state(Q,T-Q[:,1]*L))
assert min(lengths)>L and max(lengths)<2*L
replace_states(cn,cs);replace_states(pn,ps)
audit['brake']={'old_deg':60,'new_deg':50,'basis':'Conservative photographic fit to supplied raised-brake views; projected angles are perspective-dependent, not an official measured limit','pivot_surface_and_closed_attachment_preserved':True,'actuator_length_m':L,'actuator_attachment_distances_m':lengths,'minimum_telescopic_overlap_m':2*L-max(lengths)}
# The original F13 fan triangles converge on two tips at the nozzle exit, in front of the dark throat.
# Recess only those two confirmed internal apex positions; retain shell/ring and original topology.
n=lu['Fuselage_0_13'];m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v);P=position(n);world=v+P;ids=np.flatnonzero((world[:,2]<-9.5)&(abs(abs(world[:,0])-1.1845)<.015)&(abs(world[:,1]+.4477)<.015));tips=np.unique(np.round(world[ids],6),axis=0);assert len(tips)==2,(tips,len(ids));world[ids,2]=-8.60;m.v=list(map(tuple,world-P));affected=set(map(int,ids));faces=0
for j,(ix,c,b) in enumerate(m.f):
 if affected.intersection(ix):m.f[j]=(ix,(24,27,30),False);faces+=1
p[dnm.fil(n)]=m.srf();audit['engine_centerbodies']={'confirmed_node':'Fuselage_0_13','old_unique_tips':tips.tolist(),'new_tip_z_m':-8.6,'changed_vertex_instances':len(ids),'changed_unique_tip_positions':len(tips),'internal_faces_matte_dark':faces,'all_other_vertices_and_face_indices_preserved':True,'evidence':'Rear-axis rays hit these long cone triangles before Su30NozzleThroat; grey tip visibly protruded in both native rear captures.'}
# Only the rectangular duct walls had artificial outward duplicate rendering faces.
# Keep the same wall surface, oriented towards its actual air volume, and all fan geometry.
for side in [-1,1]:
 fn='IntakeDuct_'+str(side)+'.srf';m=dnm.mesh(p[fn]);v=np.array(m.v);out=[];count=0
 for ix,c,b in m.f:
  q=v[ix]
  if c==(30,35,41) and len(ix)==4:
   N=np.cross(q[1]-q[0],q[2]-q[0]);target=np.array([side*1.18,-.54,q.mean(0)[2]])-q.mean(0)
   if N@target<0:count+=1;continue
  out.append((ix,c,b))
 assert count==4,count;m.f=out;p[fn]=m.srf();audit['IntakeDuct_'+str(side)]={'outward_reverse_wall_faces_removed':count,'all_four_physical_wall_surfaces_retained':True,'fan_unchanged':True,'wall_coordinates_unchanged':True}
# Nozzle petal animation is radial aperture variation, not thrust-vector articulation. Leave it exact.
for n,o in zip(ns,oldns):
 if dnm.cla(n)==270:assert n==o and p[dnm.fil(n)]==old[dnm.fil(n)]
(r/'runtime/aircraft').mkdir(parents=True,exist_ok=True);dnm.write(r/'runtime/aircraft/su30sm.dnm',p,ns)
# The separately loaded cockpit model has the same canopy state records.
cpbase=r/'baseline/su30smcockpit.dnm';cp,cnn=dnm.read(cpbase)
for n in cnn:
 if dnm.cla(n)==211:replace_states(n,[s for s in lu[dnm.name(n)] if s.startswith('STA ')])
dnm.write(r/'runtime/aircraft/su30smcockpit.dnm',cp,cnn)
audit['changed_packs']=[k for k in old if p[k]!=old[k]];audit['changed_nodes']=[dnm.name(n) for n,o in zip(ns,oldns) if n!=o];audit['model_sha256']=hashlib.sha256((r/'runtime/aircraft/su30sm.dnm').read_bytes()).hexdigest();audit['cockpit_sha256']=hashlib.sha256((r/'runtime/aircraft/su30smcockpit.dnm').read_bytes()).hexdigest();(r/'repair-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2));print(json.dumps(audit,ensure_ascii=False,indent=2))
