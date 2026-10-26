import math
import numpy as np
from scipy.spatial import ConvexHull
from mesh import Mesh
import dnm

def rotation(vals):
 h,p,b=[v*math.pi/32768 for v in vals];ch,sh,cp,sp,cb,sb=math.cos(h),math.sin(h),math.cos(p),math.sin(p),math.cos(b),math.sin(b)
 return np.array([[ch,0,-sh],[0,1,0],[sh,0,ch]])@np.array([[1,0,0],[0,cp,sp],[0,-sp,cp]])@np.array([[cb,-sb,0],[sb,cb,0],[0,0,1]])
def build_collision(packs,nodes,rows):
 out=Mesh();col=(100,110,120)
 def face(v):
  if len(v)>=3:out.face(v,col)
 def hull(pts):
  pts=np.unique(np.round(np.array(pts),6),axis=0);h=ConvexHull(pts)
  for inds,eq in zip(h.simplices,h.equations):
   a,b,c=pts[inds];n=np.cross(b-a,c-a)
   if np.dot(n,eq[:3])<0:b,c=c,b
   face([tuple(a),tuple(b),tuple(c)])
 # A low polygon closed loft for the central body.
 rings=[]
 for z,w,t,b in rows:
  ring=[]
  for k in range(12):
   angle=k*math.pi/6;x=w*math.cos(angle);u=abs(math.cos(angle));mid=.25*t+.15*b;y=mid+((t-mid)*(1-u*u)**.62 if math.sin(angle)>=0 else (b-mid)*(1-u*u)**.65);ring.append((x,y,z))
  rings.append(ring)
 for a,b in zip(rings,rings[1:]):
  for k in range(12):face([a[k],a[(k+1)%12],b[(k+1)%12],b[k]])
 face(rings[0][::-1]);face(rings[-1])
 for sg in [-1,1]:
  wing=[(sg*x,z) for x,z in [(2.08,3.30),(7.05,-2.15),(6.88,-3.45),(3.2,-4.48),(2.08,-4.35)]];hull([(x,y,z) for x,z in wing for y in [.075,.152]])
  profiles=[(3,.66,.39,-.68),(1.5,.76,.65,-.23),(0,.77,.65,-.23),(-2,.77,.70,-.17),(-4,.75,.75,-.1),(-6,.71,.69,-.1),(-8.3,.66,.62,-.1),(-9.35,.46,.46,-.1)]
  # Closed convex nacelle approximation, independent of visible detail tessellation.
  hull([(sg*1.44+rx*math.cos(k*math.pi/8),cy+ry*math.sin(k*math.pi/8),z) for z,rx,ry,cy in profiles for k in range(16)])
 parents={v[4:].strip('"'):dnm.name(a) for a in nodes for v in a if v.startswith('CLD ')};byname={dnm.name(a):a for a in nodes}
 def pose(name):
  a=byname[name];v=list(map(float,next(v[4:] for v in a if v.startswith('POS ')).split()));R=rotation(v[3:6]);T=np.array(v[:3]);
  if name in parents:
   rp,tp=pose(parents[name]);T=tp+rp@T;R=rp@R
  return R,T
 for a in nodes:
  if dnm.cla(a) not in [100,188,189,190,191]:continue
  R,T=pose(dnm.name(a));m=dnm.mesh(packs[dnm.fil(a)]);pts=[T+R@np.array(v) for v in m.v]
  if dnm.cla(a)==100:pts += [np.array([x,.70,z]) for x in [-.43,.43] for z in [4.55,7.1]]
  hull(pts)
 return out
