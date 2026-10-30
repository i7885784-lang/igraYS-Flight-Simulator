"""Seal the fixed aft nacelle cut and enclose the upper main-gear compartment."""
from pathlib import Path
import sys,numpy as np,json
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon
from shapely import constrained_delaunay_triangles
p,ns=dnm.read(r/'runtime/aircraft/mig29.dnm');ns=[n for n in ns if not dnm.name(n).startswith('MainBay')];caps=Mesh();walls=Mesh();data=json.loads((r/'mig29-boundaries.json').read_text());v=np.array([p for c in data for p in c['vertices']]);q=v[(abs(v[:,2]+2.389)<.002)&(abs(v[:,0])>1.25)&(abs(v[:,0])<1.8)]
for sg in [-1,1]:
 points=q[q[:,0]*sg>0];xy=points[:,:2];hull=ConvexHull(xy);poly=Polygon(xy[hull.vertices])
 for tr in constrained_delaunay_triangles(poly).geoms:
  xy=np.array(tr.exterior.coords)[:-1];caps.face(np.c_[xy,np.full(3,-2.389)],(107,131,132))
 # Outer cheek: follows the fixed wing root, leaving the lower source
 # door opening intact. The upper edge is recessed below the existing wing.
 sections=[(-2.389,1.72,.061,.19),(-1.66,1.68,.064,.19),(-1.,1.67,.080,.21),(-.25,1.58,.10,.23)]
 for a,b in zip(sections[:-1],sections[1:]):
  za,xa,ya,ta=a;zb,xb,yb,tb=b
  walls.face([(sg*xa,ya,za),(sg*xb,yb,zb),(sg*(xb+.10),tb,zb),(sg*(xa+.10),ta,za)],(108,131,131))
 add(p,ns,'MainBayAftCap'+str(sg),double(caps));caps=Mesh()
add(p,ns,'MainBayOuterWalls',double(walls));dnm.write(r/'runtime/aircraft/mig29.dnm',p,ns)
# Close the inner side and bulkheads. The original donor well was removed
# in test 8 for clearance but that left a view through the entire airframe.
from envelope import Envelope
from scipy.spatial import Delaunay
hullnode=next(n for n in ns if dnm.name(n)=='Hull');h=dnm.mesh(p[dnm.fil(hullnode)]);env=Envelope([{'v':h.v,'f':[ids for ids,c,b in h.f]}],step=.015);liner=Mesh();ceiling=Mesh()
for sg in [-1,1]:
 for a,b in [((.34,-2.50),(.34,.21)),((.34,.21),(1.60,.21)),((.34,-2.50),(1.72,-2.50))]:
  pts=np.linspace(a,b,max(2,int(np.linalg.norm(np.array(b)-a)/.05)+1))
  for a,b in zip(pts[:-1],pts[1:]):
   q=np.array([[sg*a[0],0,a[1]],[sg*b[0],0,b[1]]]);top=env.bounds(q)[1]-.012
   liner.face([(sg*a[0],-.24,a[1]),(sg*b[0],-.24,b[1]),(sg*b[0],top[1],b[1]),(sg*a[0],top[0],a[1])],(64,78,85))
 # A recessed ceiling follows the fixed hull rather than a raised box.
 poly=Polygon([(sg*.34,-2.5),(sg*1.72,-2.5),(sg*1.8,-1.7),(sg*1.6,.21),(sg*.34,.21)])
 pts=np.array([[x,z] for x in np.arange(*sorted([sg*.34,sg*1.80]),.075) for z in np.arange(-2.5,.22,.075) if poly.covers(__import__('shapely').Point(x,z))]+list(poly.exterior.coords)[:-1]);top=env.bounds(np.c_[pts[:,0],np.zeros(len(pts)),pts[:,1]])[1]-.012
 for ids in Delaunay(pts).simplices:
  if poly.buffer(.001).covers(Polygon(pts[ids])):
   q=np.c_[pts[ids,0],top[ids],pts[ids,1]];ceiling.face(q[::-1],(118,141,140));ceiling.face(q,(59,74,82))
add(p,ns,'MainBayCeiling',ceiling);add(p,ns,'MainBayInnerLiner',double(liner));dnm.write(r/'runtime/aircraft/mig29.dnm',p,ns)
