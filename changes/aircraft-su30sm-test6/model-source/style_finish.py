from pathlib import Path
import json,math,re,numpy as np
from common import dnm,Mesh
from gear import clip
r=Path(__file__).resolve().parent.parent;p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm');lu={dnm.name(n):n for n in ns}
# Separate slender nose probe, as visible on the supplied side views. Overall tip stays fixed.
n=lu['Fuselage_0_5'];m=dnm.mesh(p[dnm.fil(n)]);pos=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);v=np.array(m.v)+pos;cutz=9.70;tipz=float(v[:,2].max());out=Mesh();rim=[]
for ids,c,b in m.f:
 poly=clip([v[i] for i in ids],2,cutz,False)
 if len(poly)>=3:out.face(np.array(poly)-pos,c,b);rim.extend(q for q in poly if abs(q[2]-cutz)<1e-7)
rim=np.unique(np.round(rim,7),axis=0);center=rim[:,:2].mean(0);angles=np.arctan2(rim[:,1]-center[1],rim[:,0]-center[0]);idx=np.argsort(angles);angles=angles[idx];rim=rim[idx];tipxy=v[v[:,2]>tipz-.001,:2].mean(0);start=10.35;old_count=len(out.f)
for k in range(len(rim)):
 j=(k+1)%len(rim);a,b=angles[k],angles[j];base0=np.r_[center+[.018*math.cos(a),.018*math.sin(a)],start];base1=np.r_[center+[.018*math.cos(b),.018*math.sin(b)],start];end0=np.r_[tipxy+[.005*math.cos(a),.005*math.sin(a)],tipz];end1=np.r_[tipxy+[.005*math.cos(b),.005*math.sin(b)],tipz]
 out.face(np.array([rim[k],rim[j],base1,base0])-pos,(242,246,244));out.face(np.array([base0,base1,end1,end0])-pos,(118,128,135));out.face(np.array([np.r_[tipxy,tipz],end0,end1])-pos,(103,113,120))
out.f += [(ids[::-1],c,b) for ids,c,b in list(out.f[old_count:])];p[dnm.fil(n)]=out.srf()
# Blue/grey patches follow continuous shared-edge contours. Splitting colour
# regions on a face preserves its plane and flat normal; no normal smoothing.
def signal(q):
 x,y,z=q;return math.sin(z*.86+x*.56)+.58*math.sin(x*1.7-z*.30)+.27*math.cos(z*1.9)
def scalar_clip(poly,level,positive):
 out=[]
 for aa,bb in zip(poly,poly[1:]+poly[:1]):
  a,ta=aa;b,tb=bb;va=(ta-level)*(1 if positive else -1);vb=(tb-level)*(1 if positive else -1)
  if va>=-1e-10:out.append((a,ta))
  if (va>=0)!=(vb>=0):
   u=(level-ta)/(tb-ta);out.append((a+(b-a)*u,level))
 return out
from common import transform
for n in ns:
 name=dnm.name(n)
 if name.startswith(('Wheel','GearBearing','GearUpper','GearPiston','GearAxle','GearLink','GearWell','DoorSeat','Su30Interior','Intake','Su30Nozzle','Su30Plume','Su30Dry','Cylinder','AirbrakeActuator','AirbrakeBay')):continue
 old=dnm.mesh(p[dnm.fil(n)])
 if not old.v:continue
 R,t=transform(n,0);pos=np.array(next(line[4:] for line in n if line.startswith('POS ')).split()[:3],float);v=np.array(old.v)@R.T+t+pos;out=Mesh()
 for ids,c,bright in old.f:
  if c[:3] not in [(57,50,115),(47,47,79)]:out.face([old.v[i] for i in ids],c,bright);continue
  if name.startswith('Cockpit_cover'):out.face([old.v[i] for i in ids],(49,66,78),bright);continue
  q=[(v[i],signal(v[i])) for i in ids]
  for lo,hi,color in [(-100,-.48,(77,139,163)),(-.48,.72,(118,166,185)),(.72,100,(147,163,172))]:
   part=scalar_clip(q,lo,True);part=scalar_clip(part,hi,False) if len(part)>=3 else []
   if len(part)<3:continue
   world=np.array([point for point,value in part]);color=(142,169,181) if world[:,1].mean()<-.25 else color
   out.face((world-t-pos)@R,color,bright)
 p[dnm.fil(n)]=out.srf()
dnm.write(r/'runtime/aircraft/su30sm.dnm',p,ns)
cn=[n for n in ns if dnm.name(n) in ['Fuselage_0_4','Fuselage_0_5','Fuselage_0_6','Cockpit_cover_6_30','Cockpit_cover_6_31','Su30Interior']];dnm.write(r/'runtime/aircraft/su30smcockpit.dnm',{dnm.fil(n):p[dnm.fil(n)] for n in cn},cn)
f=r/'runtime/aircraft/su30sm.dat';s=f.read_text()
for key,value in [('LEFTGEAR','-2.05m -2.52m -2.80m'),('RIGHGEAR','2.05m -2.52m -2.80m'),('WHELGEAR','0m -2.52m 2.77m')]:s=re.sub(r'(?m)^'+key+r'[^\n]*',key+' '+value,s)
f.write_text(s)
(r/'nose-revision.json').write_text(json.dumps({'tip_z_unchanged_m':tipz,'probe_length_m':tipz-start,'probe_base_diameter_m':.036,'source':'User-supplied Su-30SM side view; shape adaptation, not factory probe dimensions'},indent=2))
audit=json.loads((r/'revision.json').read_text());audit['nose_probe']={'changed':True,**json.loads((r/'nose-revision.json').read_text())};(r/'revision.json').write_text(json.dumps(audit,indent=2))
print('Nose probe and blue/grey livery complete.',flush=True)
