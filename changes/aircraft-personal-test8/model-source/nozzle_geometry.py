from common import *
def point(x,y,z,rx,ry,a):return (x+rx*math.cos(a),y+ry*math.sin(a),z)
def chamber(x,y,z,rx,ry,length):
 m=Mesh();N=24
 # Recessed convergent inner liner and longitudinal ribs. No disk at the mouth.
 for i in range(N):
  a,b=2*math.pi*i/N,2*math.pi*(i+1)/N
  for j,(za,zb,ra,rb) in enumerate([(z,z+length*.45,.96,.88),(z+length*.45,z+length,.88,.80)]):
   m.face([point(x,y,za,rx*ra,ry*ra,a),point(x,y,za,rx*ra,ry*ra,b),point(x,y,zb,rx*rb,ry*rb,b),point(x,y,zb,rx*rb,ry*rb,a)],(47+i%2*9,51+i%2*8,57+i%2*8))
  for depth in [.32,.65,.94]:
   zz=z+length*depth;r=.96-.16*depth
   m.face([point(x,y,zz,rx*r,ry*r,a),point(x,y,zz,rx*r,ry*r,b),point(x,y,zz+.018,rx*(r-.025),ry*(r-.025),b),point(x,y,zz+.018,rx*(r-.025),ry*(r-.025),a)],(77,72,66))
  # A deep flameholder ring rather than a flat black end cap.
  a,b=2*math.pi*i/N,2*math.pi*(i+1)/N
  m.face([point(x,y,z+length,rx*.80,ry*.80,a),point(x,y,z+length,rx*.80,ry*.80,b),point(x,y,z+length+.012,rx*.60,ry*.60,b),point(x,y,z+length+.012,rx*.60,ry*.60,a)],(69+i%2*8,63+i%2*6,59+i%2*6))
  m.face([(x,y,z+length+.18),point(x,y,z+length+.18,rx*.80,ry*.80,b),point(x,y,z+length+.18,rx*.80,ry*.80,a)],(22,25,29))
 return double(m)
def petal_shell(x,y,zfront,zback,rx,ry,endrx,endry):
 m=Mesh();N=24
 for k in range(N):
  a,b=2*math.pi*k/N,2*math.pi*(k+1)/N
  # Three axial bands, with narrow overlapping edge strips.
  for j,(t0,t1) in enumerate([(0,.20),(.20,.78),(.78,1)]):
   def ring(t,aa):return point(x,y,zfront+(zback-zfront)*t,rx+(endrx-rx)*t,ry+(endry-ry)*t,aa)
   shade=[(116,119,122),(101,105,112),(83,88,96)][j];c=tuple(v+(k%2)*7 for v in shade)
   m.face([ring(t0,a),ring(t0,b),ring(t1,b),ring(t1,a)],c)
   m.face([ring(t0,b-.016),ring(t0,b),ring(t1,b),ring(t1,b-.016)],(69,75,84))
  # Finite exit lip joins the external petals to the inner liner.
  m.face([point(x,y,zback,endrx,endry,a),point(x,y,zback,endrx,endry,b),point(x,y,zback+.012,endrx*.96,endry*.96,b),point(x,y,zback+.012,endrx*.96,endry*.96,a)],(128,125,121))
 return double(m)
def flame(x,y,z,rx,ry,length=1.65):
 m=Mesh();N=20
 for j,(t0,t1,r0,r1,c) in enumerate([(0,.28,.67,.54,(116,139,230)),(.28,.68,.54,.32,(227,167,99)),(.68,1,.32,.025,(239,119,55))]):
  for i in range(N):
   a,b=2*math.pi*i/N,2*math.pi*(i+1)/N
   m.face([point(x,y,z-length*t0,rx*r0,ry*r0,a),point(x,y,z-length*t0,rx*r0,ry*r0,b),point(x,y,z-length*t1,rx*r1,ry*r1,b),point(x,y,z-length*t1,rx*r1,ry*r1,a)],c,True)
 return double(m)
