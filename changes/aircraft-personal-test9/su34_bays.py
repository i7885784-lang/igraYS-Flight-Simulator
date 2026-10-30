from pathlib import Path
import sys,numpy as np,json
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
from shapely.geometry import Polygon
from shapely import union_all,constrained_delaunay_triangles
from envelope import Envelope
from scipy.ndimage import maximum_filter
p,ns=dnm.read(r/'runtime/aircraft/su34.dnm');bp,bns=dnm.read(r/'baseline/su34.dnm');blu={dnm.name(n):n for n in bns}
ns=[n for n in ns if dnm.name(n) not in ['ConformalWingRootBaySides','RecessedGearBaySeals','BayRoofRepair','BayWallRepair','MainBaySeals','RecessedNoseBaySeal']]
orig=dnm.mesh((r/'uncut-su34.srf').read_text().splitlines());env=Envelope([{'v':orig.v,'f':[ids for ids,c,b in orig.f]}],step=.01);env.top=maximum_filter(env.top,size=7)
foot=[]
def floor(x,z):return -.245+.095*np.clip((-z-.8)/.8,0,1)
for n in ns:
 if not dnm.name(n).startswith('OriginalSideDoor'):continue
 old=dnm.mesh(bp[dnm.fil(blu[dnm.name(n)])]);poly=union_all([Polygon(np.array([old.v[i] for i in ids])[:,[0,2]]) for ids,c,b in old.f if c[0]>130]).buffer(.10 if dnm.name(n).endswith('Wheel') else 0,join_style='mitre')
 # Preserve the accepted outboard hinge edge; extend only the corner clearance.
 from shapely.geometry import box

 if dnm.name(n).endswith('Strut'):
  sg=1 if 'DoorL' in dnm.name(n) else -1;extension=Polygon(np.array([[1.55,-1.45],[2.58,-1.45],[2.58,-2.05],[1.72,-2.05]])*[sg,1]);poly=poly.union(extension)
 poly=poly.intersection(box(-100,-1.45,100,100) if dnm.name(n).endswith('Wheel') else box(-100,-100,100,-1.45));poly=poly.intersection(box(-2.662,-100,2.662,100));m=Mesh()
 for tri in constrained_delaunay_triangles(poly).geoms:
  xz=np.array(tri.exterior.coords)[:-1];q=np.c_[xz[:,0],floor(xz[:,0],xz[:,1]),xz[:,1]];m.face(q,(138,169,181));m.face((q+[0,.012,0])[::-1],(120,145,160))
 ring=np.array(poly.exterior.coords)
 for a,b in zip(ring[:-1],ring[1:]):
  q=np.array([(a[0],floor(*a),a[1]),(b[0],floor(*b),b[1])]);m.face([q[0],q[1],q[1]+[0,.012,0],q[0]+[0,.012,0]],(116,141,154))
 p[dnm.fil(n)]=m.srf();foot.append(poly)
 # Retain the accepted original hinge and opening motion.
 original=blu[dnm.name(n)];i=next(i for i,s in enumerate(n) if s.startswith('NST '));j=next(i for i,s in enumerate(n) if s.startswith('POS '));states=[s for s in original if s.startswith('STA ')];n[i:j]=['NST '+str(len(states))]+states
opening=union_all(foot).buffer(.005,join_style='mitre');wall=Mesh();seals=Mesh()
for poly in (opening.geoms if hasattr(opening,'geoms') else [opening]):
 ring=np.array(poly.exterior.coords)
 for a,b in zip(ring[:-1],ring[1:]):
  points=np.linspace(a,b,max(2,int(np.linalg.norm(b-a)/.035)+1))
  for a,b in zip(points[:-1],points[1:]):
   q=np.array([[a[0],0,a[1]],[b[0],0,b[1]]]);top=env.bounds(q)[1]+.003
   wall.face([(a[0],floor(*a),a[1]),(b[0],floor(*b),b[1]),(b[0],top[1],b[1]),(a[0],top[0],a[1])],(128,157,175))
# Preserve the complete accepted airframe, including both raked intake lips.
# Adjust only the rear well's buried inner corner for the rounded tyre.
# The raked entrance and its forward casing (Z > -1.42) remain original.
from gear_v3 import clip
body=dnm.mesh(bp[dnm.fil(blu['SourceAirframe'])]);fixed=Mesh()
def outside(poly,planes):
 inside=list(poly);result=[]
 for axis,value,positive in planes:
  q=clip(inside,axis,value,not positive) if len(inside)>=3 else []
  if len(q)>=3:result.append(q)
  inside=clip(inside,axis,value,positive) if len(inside)>=3 else []
 return result
regions=[[(0,1.55,True),(0,1.82,False),(2,-2.08,True),(2,-1.42,False),(1,-.28,True),(1,.06,False)],[(0,-1.82,True),(0,-1.55,False),(2,-2.08,True),(2,-1.42,False),(1,-.28,True),(1,.06,False)]]
for ids,c,b in body.f:
 polys=[[body.v[i] for i in ids]]
 for region in regions:polys=[q for poly in polys for q in outside(poly,region)]
 for q in polys:fixed.face(q,c,b)
p[dnm.fil(blu['SourceAirframe'])]=fixed.srf();add(p,ns,'ConformalWingRootBaySides',double(wall))
# A narrow hidden seat beyond the opening, rather than a visible offset lid.
region=opening.buffer(.016,join_style='mitre').difference(opening)
for poly in (region.geoms if hasattr(region,'geoms') else [region]):
 for tri in constrained_delaunay_triangles(poly).geoms:
  q=np.array(tri.exterior.coords)[:-1];seals.face(np.c_[q[:,0],floor(q[:,0],q[:,1])+.016,q[:,1]],(92,117,132))
add(p,ns,'MainBaySeals',double(seals))
# Keep the already reviewed nose rim; this repair changes only the main bays.
nose=Mesh();oldseal=dnm.mesh(bp[dnm.fil(blu['RecessedGearBaySeals'])])
for ids,c,b in oldseal.f:
 q=np.array([oldseal.v[i] for i in ids])
 if q[:,2].min()>.7:nose.face(q,c,b)
add(p,ns,'RecessedNoseBaySeal',nose)
dnm.write(r/'runtime/aircraft/su34.dnm',p,ns)
print('main opening',opening.area,'wall faces',len(wall.f))
