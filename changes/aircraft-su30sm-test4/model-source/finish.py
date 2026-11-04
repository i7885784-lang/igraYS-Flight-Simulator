from pathlib import Path
import math
from common import dnm,Mesh,add
r=Path(__file__).resolve().parent.parent
p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm')
ns=[n for n in ns if not dnm.name(n).startswith(('Su30Interior','Su30NozzleThroat_'))]
# Light blue, 16% opacity. Keep frames opaque and all normals flat.
for fn,ls in p.items():p[fn]=['C 110 165 190 42' if s=='C 88 138 162 130' else s for s in ls]
inside=Mesh();inside.box(0,.53,4.8,.84,.10,2.9,(27,31,35))
# Simple interior to locate the pilot inside the real canopy envelope; native HUD/panel remains functional.
for z in [5.12,3.90]:
 inside.box(0,.69,z,.48,.15,.48,(47,54,49));inside.box(0,.92,z-.20,.46,.55,.10,(43,50,47));inside.box(0,1.16,z-.20,.22,.12,.12,(31,35,34))
inside.box(0,.84,6.16,.71,.31,.15,(30,34,37));inside.box(0,1.005,6.14,.76,.025,.24,(24,28,30))
for x in [-.19,.19]:
 inside.box(x,.86,6.07,.25,.19,.012,(15,22,25))
 for z in [6.063]:
  for yy in [.82,.86,.90]:inside.box(x,yy,z,.19,.006,.004,(62,106,87))
for x in [-.42,.42]:inside.box(x,.75,4.9,.08,.20,2.4,(35,40,42))
add(p,ns,'Su30Interior',inside)
# Identical recessed, dark nozzle throats hide the source's exposed grey end plugs.
import json
profiles=json.loads((r/'nozzle-profile.json').read_text())
for side in ['0','1']:
 q=profiles[side][-1];m=Mesh();N=32;cx,cy,z=q['cx'],q['cy'],q['z'];rad=q['radius']
 for k in range(N):
  a=2*math.pi*k/N;b=2*math.pi*(k+1)/N
  def point(t,rr,zz):return (cx+rr*math.cos(t),cy+rr*math.sin(t),zz)
  m.face([point(a,rad*1.01,z+.008),point(b,rad*1.01,z+.008),point(b,rad*.87,z+.040),point(a,rad*.87,z+.040)],(35,38,41))
  m.face([(cx,cy,z+.035),point(b,rad*.88,z+.035),point(a,rad*.88,z+.035)],(15,18,21))
  m.face([point(a,rad*.69,z+.034),point(b,rad*.69,z+.034),point(b,rad*.76,z+.034),point(a,rad*.76,z+.034)],(48,44,38))
 add(p,ns,'Su30NozzleThroat_'+side,m)
dnm.write(r/'runtime/aircraft/su30sm.dnm',p,ns)
# A small separate interior avoids loading a second copy of the complete aircraft on 32-bit Windows.
cp={};cn=[]
for n in ns:
 if dnm.name(n) in ['Fuselage_0_4','Fuselage_0_5','Fuselage_0_6','Cockpit_cover_6_30','Cockpit_cover_6_31','Su30Interior']:
  cn.append(n);cp[dnm.fil(n)]=p[dnm.fil(n)]
assert len(cn)==6
dnm.write(r/'runtime/aircraft/su30smcockpit.dnm',cp,cn)
reg=r/'runtime/aircraft/air_su30sm.lst';text=reg.read_text().split();text[3]='aircraft/su30smcockpit.dnm';reg.unlink();reg.write_text(' '.join(text[:4])+'\n')
dat=r/'runtime/aircraft/su30sm.dat';s=dat.read_text();s=s.replace('COCKPITP 0m 1.42m 4.8m','COCKPITP 0m 1.18m 5.55m');dat.unlink();dat.write_text(s)
