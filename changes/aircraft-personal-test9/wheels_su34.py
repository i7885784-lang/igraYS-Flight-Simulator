"""Round main tandem tyres, preserving axle centers, diameter and bogie states."""
from pathlib import Path
import sys,numpy as np,math,json
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'runtime/aircraft/su34.dnm');stats=[];bp,bns=dnm.read(r/'baseline/su34.dnm');blu={dnm.name(n):n for n in bns}
for n in ns:
 if dnm.name(n) not in ['TandemTruckL','TandemTruckR']:continue
 old=dnm.mesh(bp[dnm.fil(blu[dnm.name(n)])]);m=Mesh();sg=1 if dnm.name(n).endswith('L') else -1
 # Retain the donor's cast bogie and axle bodies, replace only rubber and hubs.
 for ids,c,b in old.f:
  if c!=(32,36,39):m.face([old.v[i] for i in ids],c,b)
 v=np.array([old.v[i] for ids,c,b in old.f if c==(32,36,39) for i in ids]);split=(v[:,2].min()+v[:,2].max())/2
 for ii,mask in enumerate([v[:,2]<split,v[:,2]>split]):
  q=v[mask];lo,hi=q.min(0),q.max(0);center=(lo+hi)/2;radius=(hi[1]-lo[1])/2;radius_z=(hi[2]-lo[2])/2;width=.30;center[0]=sg*(2.173016-width/2)
  def pt(s,rad,a):return (center[0]+s*width,center[1]+radius*rad*math.cos(a),center[2]+radius_z*rad*math.sin(a))
  profile=[(-.50,.55),(-.48,.69),(-.34,.84),(-.20,.97),(-.10,1),(.10,1),(.20,.97),(.34,.84),(.48,.69),(.50,.55)]
  for k in range(48):
   a,b=k*2*math.pi/48,(k+1)*2*math.pi/48
   for (s0,r0),(s1,r1) in zip(profile[:-1],profile[1:]):m.face([pt(s0,r0,a),pt(s0,r0,b),pt(s1,r1,b),pt(s1,r1,a)],(33,37,40) if abs(s0)>.22 else (25,29,32))
   for face in [-1,1]:
    if face==sg:continue  # Keep the original detailed outer hub.
    m.face([pt(face*.50,.55,a),pt(face*.50,.55,b),pt(face*.46,.40,b),pt(face*.46,.40,a)],(135,151,158))
    m.face([pt(face*.46,.40,a),pt(face*.46,.40,b),pt(face*.46,.13,b),pt(face*.46,.13,a)],(94,113,117))
    m.face([pt(face*.46,.13,a),pt(face*.46,.13,b),(center[0]+face*width*.46,center[1],center[2])],(147,160,166))
  stats.append({'node':dnm.name(n),'wheel':ii,'old_rubber_width':float(hi[0]-lo[0]),'width':width,'diameter':float(radius*2),'fore_aft_diameter':float(radius_z*2),'center':center.tolist()})
 p[dnm.fil(n)]=double(m).srf()
dnm.write(r/'runtime/aircraft/su34.dnm',p,ns);(r/'su34-wheels.json').write_text(json.dumps(stats,indent=2));print(stats)
