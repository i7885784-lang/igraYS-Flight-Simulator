import numpy as np
from common import *
from nose_bay import clip,area

def hinge_pockets(mesh,door):
 R,C=transform(door,0);A,_=transform(door,17);axis=Rotation.from_matrix(A@R.T).as_rotvec();axis/=np.linalg.norm(axis)
 if axis[2]<0:axis=-axis
 boxes=[]
 for z in [-3.03,-1.05]:
  q=C+axis*(z-C[2])/axis[2];boxes.append([q+[-.022,-.091,-.046],q+[.022,.021,.046]])
 out=Mesh();v=np.array(mesh.v)
 for ids,c,b in mesh.f:
  polys=[list(v[ids])]
  for lo,hi in boxes:
   keep=[]
   for poly in polys:
    inside=poly
    for axis,bound,sg in [(0,lo[0],True),(0,hi[0],False),(1,lo[1],True),(1,hi[1],False),(2,lo[2],True),(2,hi[2],False)]:
     if len(inside)<3:break
     rest=clip(inside,axis,bound,not sg)
     if len(rest)>=3 and area(rest)>1e-12:keep.append(rest)
     inside=clip(inside,axis,bound,sg)
   polys=keep
  for poly in polys:
   for j in range(1,len(poly)-1):
    q=np.round(np.array([poly[0],poly[j],poly[j+1]]),6)
    if np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))>2e-12:out.face(q,c,b)
 return out
