"""Parallel orthographic visibility rays for a group sharing one view direction."""
import numpy as np

def occluded(tri,points,direct):
 d=np.array(direct,dtype=float);d/=np.linalg.norm(d);helper=np.array([0,1.,0]) if abs(d[1])<.9 else np.array([1.,0,0]);u=np.cross(d,helper);u/=np.linalg.norm(u);v=np.cross(d,u);basis=np.c_[u,v];xy=tri@basis;depth=tri@d;pp=points@basis;pd=points@d
 a=xy[:,0];b=xy[:,1]-a;c=xy[:,2]-a;det=b[:,0]*c[:,1]-c[:,0]*b[:,1];valid=abs(det)>1e-10;xy=xy[valid];a=a[valid];b=b[valid];c=c[valid];det=det[valid];depth=depth[valid];results=[]
 for i in range(0,len(points),64):
  delta=pp[i:i+64,None,:]-a[None,:,:];f=(delta[:,:,0]*c[:,1]-delta[:,:,1]*c[:,0])/det;g=(b[:,0]*delta[:,:,1]-b[:,1]*delta[:,:,0])/det;z=(1-f-g)*depth[:,0]+f*depth[:,1]+g*depth[:,2];covered=(f>=-1e-6)&(g>=-1e-6)&(f+g<=1.000001)&(z>pd[i:i+64,None]+.0001)&(z<pd[i:i+64,None]+20);results.extend(covered.any(1))
 return np.array(results,bool)
