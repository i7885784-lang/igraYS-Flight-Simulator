import numpy as np,math
from common import *
def clip(poly,axis,t,positive):
 out=[];sg=1 if positive else -1
 for a,b in zip(poly,poly[1:]+poly[:1]):
  da=(a[axis]-t)*sg;db=(b[axis]-t)*sg
  if da>=-1e-10:out.append(a)
  if (da>=0)!=(db>=0):out.append(a+(b-a)*da/(da-db))
 return out

def area(poly):
 return sum(np.linalg.norm(np.cross(poly[j]-poly[0],poly[j+1]-poly[0]))/2 for j in range(1,len(poly)-1))

def extend_fore_opening(p,ns,audit):
 source=[];seen=set();changes=[]
 for n in ns:
  name=dnm.name(n)
  if name not in ['Fuselage_0_4','Fuselage_0_5']:continue
  old=dnm.mesh(p[dnm.fil(n)]);R,C=transform(n,0);P=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);v=np.array(old.v)@R.T+C+P;out=Mesh();out.v=list(old.v);removed=0
  for ids,color,b in old.f:
   q=v[ids];normal=np.cross(q[1]-q[0],q[2]-q[0]);candidate=list(q)
   if abs(normal[1])<np.linalg.norm(normal)*.08 or q[:,1].mean()>-.15:out.f.append((ids,color,b));continue
   for axis,t,positive in [(0,-.38,True),(0,.38,False),(2,4.16,True),(2,4.45,False)]:
    candidate=clip(candidate,axis,t,positive) if len(candidate)>=3 else []
   if len(candidate)<3 or area(candidate)<1e-11:out.f.append((ids,color,b));continue
   todo=list(q)
   for axis,t,positive in [(0,-.38,True),(0,.38,False),(2,4.16,True),(2,4.45,False)]:
    rest=clip(todo,axis,t,not positive) if len(todo)>=3 else []
    if len(rest)>=3 and area(rest)>1e-11:
     # Clipping may retain collinear vertices: never emit zero-area fan triangles.
     local=np.round((np.array(rest)-C-P)@R,6)
     for j in range(1,len(local)-1):
      tri=local[[0,j,j+1]]
      if np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))>2e-12:out.face(tri,color,b)
    todo=clip(todo,axis,t,positive) if len(todo)>=3 else []
   for j in range(1,len(candidate)-1) if normal[1]<0 else []:
    tri=np.round(np.array([candidate[0],candidate[j],candidate[j+1]]),6);key=tuple(sorted(tuple(a) for a in tri))
    if key in seen or np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))<1e-10:continue
    seen.add(key)
    if np.cross(tri[1]-tri[0],tri[2]-tri[0])[1]>0:tri=tri[::-1]
    source.append((tri,color))
   removed+=1
  if removed:p[dnm.fil(n)]=out.srf();changes.append({'name':name,'cut_face_instances':removed,'outside_local_window_preserved':True})
 assert source, 'Missing measured lower exterior surface for nose aperture extension'
 audit['nose_fore_aperture']={'old_front_z_m':4.16,'new_front_z_m':4.45,'half_width_m':.38,'reason':'Original wheel/body and wheel/front-wall collisions at g=.30/.35; unchanged swept tyre reaches Z4.415m. New opening clearance35mm.','original_paint_geometry_retained_on_extended_closed_doors':True,'changed_body_parts':changes}
 return source

def full_nose_compartment(rim,height):
 m=Mesh();x0,x1,z0,z1=-.397,.397,1.973,4.467;ceiling=.455;centre=np.array([0,.1,3.15]);steps=[((x0,z0),(x1,z0)),((x1,z0),(x1,z1)),((x1,z1),(x0,z1)),((x0,z1),(x0,z0))]
 def face(q,c):
  q=np.array(q);n=np.cross(q[1]-q[0],q[2]-q[0])
  if n@(centre-q.mean(0))<0:q=q[::-1]
  m.face(q,c)
 for a,b in steps:
  pts=np.linspace(a,b,max(3,int(math.dist(a,b)/.045)+2));floor=[]
  for x,z in pts:
   y=height(rim,float(np.clip(x,-.3799,.3799)),float(np.clip(z,1.9901,4.4499)),False)
   assert y is not None,('Nose rim has no real support',x,z)
   floor.append([x,y+.025,z])
  for a,b in zip(floor,floor[1:]):face([a,b,[b[0],ceiling,b[2]],[a[0],ceiling,a[2]]],(210,214,200))
 face([[x0,ceiling,z0],[x1,ceiling,z0],[x1,ceiling,z1],[x0,ceiling,z1]],(226,228,215))
 return m
