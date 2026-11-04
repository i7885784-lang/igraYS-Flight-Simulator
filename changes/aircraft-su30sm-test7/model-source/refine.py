from pathlib import Path
import numpy as np,json,math
from common import *
r=Path(__file__).resolve().parent.parent;p,ns=dnm.read(r/'baseline/su30sm.dnm');lu={dnm.name(n):n for n in ns};audit={}
def pos(n):return np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float)
# Keep closed canopy curvature, replace opaque window infill with actual glazing.
n=lu['Cockpit_cover_6_30'];m=dnm.mesh(p[dnm.fil(n)]);count=0;out=[]
for ids,c,b in m.f:
 q=np.array([m.v[i] for i in ids]);z=q[:,2].mean();y=q[:,1].mean()
 # Preserve bottom sill, end frames and the three transverse canopy bows.
 bow=min(abs(z-k) for k in [.03,1.58,3.91])<.055
 if y>-.12-.12*z and not bow:
  c=(110,165,190,42);count+=1
 out.append((ids,c,b))
m.f=out;p[dnm.fil(n)]=m.srf();audit['opaque_canopy_faces_replaced_by_glazing']=count
for name in ['Fuselage_0_7','Fuselage_0_13']:
 n=lu[name];m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v)+pos(n);m.f=[(ids,c,b) for ids,c,b in m.f if v[ids,2].min()<=-1.45];p[dnm.fil(n)]=m.srf()
# Identical intake tunnels, with an offset dark duct instead of exposed add-on fan discs.
for sign in [-1,1]:
 n=lu['IntakeDuct_'+str(sign)];cx=sign*1.18;m=Mesh();rings=[]
 for z,w,h,dy,dx in [(-.41,.37,.41,-.56,0),(-.8,.355,.39,-.55,sign*.03),(-1.15,.33,.35,-.50,sign*.10),(-1.40,.31,.31,-.42,sign*.17)]:
  rings.append([(cx+dx-w,dy-h,z),(cx+dx+w,dy-h,z),(cx+dx+w,dy+h,z),(cx+dx-w,dy+h,z)])
 for a,b in zip(rings,rings[1:]):
  for k in range(4):j=(k+1)%4;m.face([a[k],a[j],b[j],b[k]],(35,41,47));m.face([a[k],b[k],b[j],a[j]],(35,41,47))
 m.face(rings[-1][::-1],(20,24,28));m.face(rings[-1],(20,24,28));p[dnm.fil(n)]=m.srf()
# Shorten the hanging main leg-cover at the aft end. The aft cover closes again
# after the wheel passes; retain the narrow front cover attached to the bay hinge.
for name in ['GearDoor_Left_Inner','GearDoor_Right_Outer']:
 n=lu[name];m=dnm.mesh(p[dnm.fil(n)]);R,t=transform(n,0);v=np.array(m.v)@R.T+t+pos(n);front=Mesh();aft=Mesh()
 def clip(poly,axis,value,positive):
  out=[]
  for a,b in zip(poly,poly[1:]+poly[:1]):
   da=(a[axis]-value)*(1 if positive else -1);db=(b[axis]-value)*(1 if positive else -1)
   if da>=0:out.append(a)
   if (da>=0)!=(db>=0):out.append(a+(b-a)*da/(da-db))
  return out
 for ids,c,b in m.f:
  poly=[v[i] for i in ids]
  for mesh,positive in [(front,True),(aft,False)]:
   q=clip(poly,2,-1.85,positive)
   if len(q)>=3:mesh.face([(a-pos(n)-t)@R for a in q],c,b)
 p[dnm.fil(n)]=front.srf();ss=[s for s in n if s.startswith('STA ')];new=[]
 for i in range(101):
  g=i/100;u=min(1,max(0,(g-.02)/.15),max(0,(.80-g)/.16));idx=min(100,round(u*100));new.append(ss[idx])
 q=add(p,ns,name+'_AftCover',aft,210,new);q[:]=dnm.edit(q,'POS ',' '.join(map(str,pos(n)))+' 0 0 0 1')
# Keep a short separate cover open beside the strut attachment.
for name in ['GearDoor_Left_Inner_AftCover','GearDoor_Right_Outer_AftCover']:
 n=next(n for n in ns if dnm.name(n)==name);m=dnm.mesh(p[dnm.fil(n)]);R,t=transform(n,0);v=np.array(m.v)@R.T+t+pos(n);a=Mesh();b=Mesh()
 for ids,c,bright in m.f:
  for target,positive in [(a,True),(b,False)]:
   q=clip([v[i] for i in ids],2,-2.90,positive)
   if len(q)>=3:target.face([(pt-pos(n)-t)@R for pt in q],c,bright)
 p[dnm.fil(n)]=a.srf();source=lu[name.replace('_AftCover','')];q=add(p,ns,name+'_LegCuff',b,210,[s for s in source if s.startswith('STA ')]);q[:]=dnm.edit(q,'POS ',' '.join(map(str,pos(n)))+' 0 0 0 1')
repair=dnm.mesh((r/'baseline/upper-wing-repair.srf').read_text().splitlines());add(p,ns,'RestoredUpperWingSkin',repair);audit['restored_upper_wing_faces']=len(repair.f)
# Repair single-sided stabilizer faces; preserve neutral geometry, colours and pivots.
for n in ns:
 if not dnm.name(n).startswith(('Elevator_','Flaps_','Aileron_')):continue
 m=dnm.mesh(p[dnm.fil(n)]);m.f += [(ids[::-1],c,b) for ids,c,b in list(m.f)];p[dnm.fil(n)]=m.srf()
# The old brake included a long fixed tail of fuselage skin. Separate that
# portion, keeping the closed surface continuous and the actuator on the leaf.
n=lu['Air_Brake_1_20'];m=dnm.mesh(p[dnm.fil(n)]);leaf=Mesh();fixed=Mesh()
for ids,c,bright in m.f:
 for target,positive in [(leaf,True),(fixed,False)]:
  q=clip([np.array(m.v[i]) for i in ids],2,-2.45,positive)
  if len(q)>=3:target.face(q if positive else [v+pos(n) for v in q],c,bright)
p[dnm.fil(n)]=leaf.srf();add(p,ns,'AirbrakeFixedRearSkin',fixed);audit['moving_brake_length_m']=2.455
# No dimension scaling or smoothing, no changes to livery.
dnm.write(r/'runtime/aircraft/su30sm.dnm',p,ns)
cp,cn=dnm.read(r/'baseline/su30smcockpit.dnm');names={dnm.name(n) for n in cn};cn=[n for n in ns if dnm.name(n) in names];dnm.write(r/'runtime/aircraft/su30smcockpit.dnm',{dnm.fil(n):p[dnm.fil(n)] for n in cn},cn)
(r/'refinement.json').write_text(json.dumps(audit,indent=2));print(audit)
