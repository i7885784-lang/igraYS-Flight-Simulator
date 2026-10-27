"""Restore the source nose opening from its actual adjoining lower skin."""
import numpy as np
from envelope import Envelope

def close_nose(objects):
 bare=Envelope(objects);verts=[];faces=[];nx=8;nz=72
 # Fit the lower cross-section using intact skin beside the original opening.
 # Clamp the reconstructed centre to the original section's lowest point so
 # this patch cannot create a new belly fairing below the source silhouette.
 for z in np.linspace(1.30,4.38,nz+1):
  outside=np.array([-.78,-.70,-.60,-.52,.52,.60,.70,.78]);q=np.c_[outside,np.zeros(len(outside)),np.full(len(outside),z)];y=bare.bounds(q)[0];coef=np.polyfit(outside,y,2)
  xs=np.linspace(-.46,.46,nx+1);ys=np.polyval(coef,xs);section=np.linspace(-.85,.85,121);floor=bare.bounds(np.c_[section,np.zeros(len(section)),np.full(len(section),z)])[0].min();ys=np.maximum(ys,floor+.002)
  # Match the genuine rim, including the asymmetry present in this source.
  ends=bare.bounds(np.array([[-.46,0,z],[.46,0,z]]))[0];blend=(xs+.46)/.92;correction=(ends[0]-ys[0])*(1-blend)+(ends[1]-ys[-1])*blend;ys=np.maximum(ys+correction,floor+.002)
  verts.extend((float(x),float(h),float(z)) for x,h in zip(xs,ys))
 for j in range(nz):
  for i in range(nx):
   a=j*(nx+1)+i;b=a+nx+1;faces.append([a,a+1,b+1,b])
 return {'name':'source_nose_rim_closure','v':verts,'f':faces}
