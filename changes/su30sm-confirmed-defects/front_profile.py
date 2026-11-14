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

def inboard_floor(p,lu,dnm,world,sg,lo=-1.86,hi=-.66):
 """Exact 1D lower contour of the existing fuselage just inboard of its cut.
 The exposed well is inside this contour; the old skin edge was a chord 5-17mm high.
 """
 n=lu['Fuselage_0_4'];m=dnm.mesh(p[dnm.fil(n)]);R,T=world(n);v=np.array(m.v)@R.T+T;cut=sg*(1.03-1e-6);segments=[]
 for ids,c,b in m.f:
  q=v[ids]
  if q[:,0].min()>cut or q[:,0].max()<cut or q[:,2].min()>hi or q[:,2].max()<lo:continue
  for j in range(1,len(ids)-1):
   tri=q[[0,j,j+1]];points=[]
   for a,b in zip(tri,np.roll(tri,-1,axis=0)):
    if (a[0]>=cut)!=(b[0]>=cut):points.append(a+(b-a)*(cut-a[0])/(b[0]-a[0]))
   if len(points)!=2 or abs(points[1][2]-points[0][2])<1e-10:continue
   a,b=points;slope=(b[1]-a[1])/(b[2]-a[2]);z0=max(lo,min(a[2],b[2]));z1=min(hi,max(a[2],b[2]))
   if z1>z0:segments.append([z0,z1,slope,a[1]-slope*a[2]])
 segments=np.unique(np.round(segments,12),axis=0);knots=set(np.r_[lo,hi,segments[:,:2].ravel()].tolist())
 for z0,z1,a,b in segments:
  den=a-segments[:,2];valid=abs(den)>1e-9;cross=np.divide(segments[:,3]-b,den,out=np.zeros(len(den)),where=valid);valid&=(cross>np.maximum(z0,segments[:,0])+1e-9)&(cross<np.minimum(z1,segments[:,1])-1e-9);knots.update(cross[valid].tolist())
 zs=np.array(sorted(knots));ys=[]
 for z in zs:
  valid=(segments[:,0]<=z+1e-9)&(segments[:,1]>=z-1e-9);assert valid.any(),('missing inboard body contour',sg,z);ys.append(float(np.min(segments[valid,2]*z+segments[valid,3])))
 ys=np.array(ys)
 while len(zs)>2:
  t=(zs[1:-1]-zs[:-2])/(zs[2:]-zs[:-2]);error=abs(ys[1:-1]-((1-t)*ys[:-2]+t*ys[2:]));valid=np.where(error<1e-8)[0]
  if not len(valid):break
  i=int(valid[0]+1);zs=np.delete(zs,i);ys=np.delete(ys,i)
 print('inboard floor',sg,'segments',len(segments),'corners',len(zs),flush=True)
 return zs,ys
