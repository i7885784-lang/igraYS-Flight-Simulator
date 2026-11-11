import numpy as np
from shapely.geometry import Polygon
def classify(a,b,tol=2e-6):
 n=np.cross(a[1]-a[0],a[2]-a[0]);n/=np.linalg.norm(n);m=np.cross(b[1]-b[0],b[2]-b[0]);m/=np.linalg.norm(m);d=(b-a[0])@n;e=(a-b[0])@m;direction=np.cross(n,m);length=np.linalg.norm(direction)
 if length<1e-8:
  if max(abs(d))>1e-10:return 'touch'
  axes=[i for i in range(3) if i!=np.argmax(abs(n))];area=Polygon(a[:,axes]).intersection(Polygon(b[:,axes])).area
  return 'coplanar_overlap' if area>1e-10 else 'touch'
 direction/=length
 def section(q,sd):
  pts=[]
  for i,j in [(0,1),(1,2),(2,0)]:
   if abs(sd[i])<1e-9:pts.append(q[i])
   if sd[i]*sd[j]<0:pts.append(q[i]+(q[j]-q[i])*sd[i]/(sd[i]-sd[j]))
  return np.array(pts)
 A=section(a,e);B=section(b,d)
 if len(A)<2 or len(B)<2:return 'touch'
 ia=A@direction;ib=B@direction;lo=max(ia.min(),ib.min());hi=min(ia.max(),ib.max())
 if hi-lo<=tol:return 'touch'
 mid=A[0]+direction*((lo+hi)/2-ia[0])
 def interior(q,p):
  normal=np.cross(q[1]-q[0],q[2]-q[0]);normal/=np.linalg.norm(normal)
  return abs((p-q[0])@normal)<1e-8 and min((np.cross(v-u,p-u)@normal)/np.linalg.norm(v-u) for u,v in zip(q,np.roll(q,-1,axis=0)))>tol
 return 'cross' if interior(a,mid) and interior(b,mid) else 'touch'

if __name__=='__main__':
 a=np.array([[-1.,0,0],[1.,0,0],[0,1.,0]])
 b=np.array([[0,.2,-1.],[0,.2,1.],[0,-.5,0]])
 assert classify(a,b)=='cross'
 assert classify(a,a+[0,0,1e-6])=='touch'
 assert classify(a,a+[.1,0,0])=='coplanar_overlap'
 outside=np.array([[2.,.2,-1.],[2.,.2,1.],[2.,-.5,0]])
 assert classify(a,outside)=='touch'
 print('Triangle checker positive, separated, coplanar and outside-point controls passed')
