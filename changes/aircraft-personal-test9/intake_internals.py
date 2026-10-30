"""Recessed inside-only duct lining. The accepted inlet lip and exterior stay original."""
from pathlib import Path
import sys,numpy as np,math,json
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'runtime/aircraft/su34.dnm');bp,bns=dnm.read(r/'baseline/su34.dnm');blu={dnm.name(n):n for n in bns}
ns=[n for n in ns if not dnm.name(n).startswith(('IntakeChannel','InsideIntake','Source_prop_'))]
# Retain the actual donor compressor geometry and its depth, rather than
# replacing it with front-mounted decorative fans.
for nm in ['Source_prop_1_slow','Source_prop_2_slow']:
 n=blu[nm];p[dnm.fil(n)]=bp[dnm.fil(n)];ns.append(n)
report={}
for side,sg,offset in [('L',1,.03355),('R',-1,0)]:
 m=Mesh();N=24
 sections=[(-.35,1.035,-.655,.35,.25,4),(-1.3,.99,-.655,.37,.27,3),(-2.4,1.06,-.61,.37,.31,2.5),(-3.49,1.16,-.60,.32,.34,2)]
 def point(sec,a):
  z,cx,cy,rx,ry,n=sec;c,s=math.cos(a),math.sin(a)
  return (sg*(cx+offset+rx*math.copysign(abs(c)**(2/n),c)),cy+ry*math.copysign(abs(s)**(2/n),s),z)
 for j,(s0,s1) in enumerate(zip(sections[:-1],sections[1:])):
  for k in range(N):
   a,b=k*2*math.pi/N,(k+1)*2*math.pi/N
   m.face([point(s0,a),point(s0,b),point(s1,b),point(s1,a)],(54-j*5,64-j*5,72-j*5))
 # Small recessed strengthening rings catch light inside the channel.
 for sec in sections[1:-1]:
  sec2=list(sec);sec2[0]-=.018;sec2[3]*=.985;sec2[4]*=.985
  for k in range(N):
   a,b=k*2*math.pi/N,(k+1)*2*math.pi/N;m.face([point(sec,a),point(sec,b),point(sec2,b),point(sec2,a)],(71,79,85))
 v=np.array(m.v)
 assert v[:,2].max()<=-.35 and v[:,1].max()<-.25 and abs(v[:,0]).max()<1.65
 add(p,ns,'InsideIntake'+side,double(m));report[side]={'bounds':[v.min(0).tolist(),v.max(0).tolist()],'original_inlet_lip_unchanged':True,'first_new_surface_z':-.35,'original_compressors_retained':True}
dnm.write(r/'runtime/aircraft/su34.dnm',p,ns);(r/'intake-internals.json').write_text(json.dumps(report,indent=2));print('Inside-only lining, original exterior and compressors retained')
