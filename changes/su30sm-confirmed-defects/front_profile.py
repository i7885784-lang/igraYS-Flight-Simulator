"""Trace the actual spatial F4 mating contour; it is not a single Y(X) function."""
import numpy as np,shapely,networkx as nx
from shapely.geometry import LineString,Point
from shapely.ops import nearest_points

def extract(p,lu,dnm,world,ends):
 n=lu['Fuselage_0_4'];m=dnm.mesh(p[dnm.fil(n)]);R,C=world(n);v=np.array(m.v)@R.T+C;z=-.40999;lines=[]
 for ids,c,b in m.f:
  q=v[ids]
  if q[:,2].max()<z or q[:,2].min()>z:continue
  pts=[]
  for a,b in zip(q,np.roll(q,-1,axis=0)):
   if (a[2]>=z)!=(b[2]>=z):pts.append(a+(b-a)*(z-a[2])/(b[2]-a[2]))
  if len(pts)==2 and np.linalg.norm(pts[0]-pts[1])>1e-8:lines.append(LineString(np.array(pts)[:,:2]))
 graph=shapely.union_all(lines,grid_size=1e-5);graph=shapely.snap(graph,graph,2e-5);graph=shapely.union_all(shapely.get_parts(graph),grid_size=1e-6);G=nx.Graph()
 for line in shapely.get_parts(graph):
  if line.geom_type!='LineString':continue
  for a,b in zip(line.coords,list(line.coords)[1:]):
   a=tuple(np.round(a,6));b=tuple(np.round(b,6))
   if a!=b:G.add_edge(a,b,weight=float(np.linalg.norm(np.array(a)-b)))
 result={}
 for side,sg in [('Left',-1),('Right',1)]:
  vertices=[]
  for xy in ends[side]:
   dist,a,b,seg=min(((LineString([a,b]).distance(Point(xy)),a,b,LineString([a,b])) for a,b in G.edges),key=lambda t:t[0]);pt=tuple(np.array(nearest_points(Point(xy),seg)[1].coords)[0].round(6));assert dist<2e-5,(side,xy,dist)
   if pt not in [a,b]:G.add_edge(a,pt,weight=float(np.linalg.norm(np.array(a)-pt)));G.add_edge(pt,b,weight=float(np.linalg.norm(np.array(b)-pt)));G.remove_edge(a,b)
   vertices.append(pt)
  path=nx.shortest_path(G,*vertices,weight='weight');line=LineString([(sg*x,y) for x,y in path]).simplify(2e-5);assert line.is_simple;front=np.array(line.coords);inside=shapely.offset_curve(line,.008,join_style='mitre',mitre_limit=2);assert inside.geom_type=='LineString' and inside.is_simple
  result[side]={'outside':front,'inside':np.array(inside.coords),'extraction_z':z,'simplification_tolerance_m':2e-5}
  print(side,'spatial front profile',len(front),'inside',len(inside.coords),'overhang',bool(np.any(np.diff(front[:,0])<0)),flush=True)
 return result
