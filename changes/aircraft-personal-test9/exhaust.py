"""Own untextured translucent exhaust and recessed engine hardware for all five aircraft."""
from pathlib import Path
import sys,numpy as np,math,json
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
def plume(x,y,z,rx,ry):
 m=Mesh();N=24;length=rx*5.6
 # Two continuous translucent layers, smoothly faded along the jet.
 for layer in [0,1]:
  for j in range(44):
   t0,t1=j/44,(j+1)/44;t=(t0+t1)/2
   base=(.77 if layer==0 else .39);rad=lambda u:base*(1-.78*u)*(1+.055*math.sin(u*math.pi*8))
   alpha=int((38 if layer==0 else 105)*(1-t)**1.6)
   blue=(95+int(90*t),128+int(40*t),245);warm=(205,183,238)
   col=tuple(int(blue[k]*(1-t)+warm[k]*t) for k in range(3))+(max(0,alpha),)
   for k in range(N):
    a,b=2*math.pi*k/N,2*math.pi*(k+1)/N
    def pt(u,ang):return (x+rx*rad(u)*math.cos(ang),y+ry*rad(u)*math.sin(ang),z-length*u)
    m.face([pt(t0,a),pt(t0,b),pt(t1,b),pt(t1,a)],col,True)
 # Repeated faint compression diamonds, not three opaque colored cones.
 for j,center in enumerate([.19,.39,.58,.75]):
  half=.10*(1-center*.35);rr=.24*(1-center*.55);alpha=int(60*(1-center))
  for a0,a1,r0,r1 in [(center-half,center,0,rr),(center,center+half,rr,0)]:
   for k in range(N):
    a,b=k*2*math.pi/N,(k+1)*2*math.pi/N
    def pt(t,rad,ang):return (x+rx*rad*math.cos(ang),y+ry*rad*math.sin(ang),z-length*t)
    m.face([pt(a0,r0,a),pt(a0,r0,b),pt(a1,r1,b),pt(a1,r1,a)],(219,206,248,alpha),True)
 return m
for kind in ['su27','mig29','su34','su47','su57']:
 p,ns=dnm.read(r/'runtime/aircraft'/f'{kind}.dnm');added=[];bp,bns=dnm.read(r/'baseline'/f'{kind}.dnm');blu={dnm.name(n):n for n in bns}
 for n in ns:
  nm=dnm.name(n)
  if nm.startswith(('Afterburner','Flame_')):
   old=dnm.mesh(bp[dnm.fil(blu[nm])]);v=np.array(old.v);x,y=(v[:,:2].max(0)+v[:,:2].min(0))/2;z=v[:,2].max();rx,ry=(v[:,:2].max(0)-v[:,:2].min(0))/(2*.67);p[dnm.fil(n)]=double(plume(x,y,z,rx,ry)).srf()
  if nm.startswith(('NozzleChamber','NozzleInterior')):
   m=dnm.mesh(bp[dnm.fil(blu[nm])]);v=np.array(m.v);x,y=(v[:,:2].max(0)+v[:,:2].min(0))/2;z=v[:,2].min()+.32;rx,ry=(v[:,:2].max(0)-v[:,:2].min(0))/(2*.96)
   # Give the recessed flameholder a visible central tailcone and support vanes.
   for k in range(20):
    a,b=k*2*math.pi/20,(k+1)*2*math.pi/20
    def pt(rad,zz,ang):return (x+rx*rad*math.cos(ang),y+ry*rad*math.sin(ang),zz)
    m.face([pt(.17,z,a),pt(.17,z,b),(x,y,z-.14)],(69,77,84),True)
    m.face([pt(.53,z+.03,a),pt(.75,z+.03,b),pt(.72,z+.045,b+.06),pt(.50,z+.045,a+.06)],(55+k%2*10,64+k%2*10,72+k%2*10),True)
   for k in range(8):
    a=k*math.pi/4;m.face([pt(.18,z,a-.025),pt(.72,z,a-.012),pt(.72,z,a+.012),pt(.18,z,a+.025)],(87,83,76),True)
   p[dnm.fil(n)]=double(m).srf();added.append(nm)
 dnm.write(r/'runtime/aircraft'/f'{kind}.dnm',p,ns)
print('own translucent jets and flameholder/turbine details: all five')
