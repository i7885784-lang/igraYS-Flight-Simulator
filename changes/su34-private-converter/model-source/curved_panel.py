"""A watertight curved skin panel, adaptively fitted to the original envelope."""
import numpy as np
from scipy.spatial import Delaunay
from shapely.geometry import Polygon,LineString,Point,box
from shapely import constrained_delaunay_triangles,contains_xy,points,distance,line_locate_point,union_all
from mesh import Mesh

def make_panel(env,region,outer,inner,thickness=.012):
 def parts(g):return list(g.geoms) if hasattr(g,'geoms') else [g]
 def height(xz):
  xz=np.asarray(xz);return env.bounds(np.c_[xz[:,0],np.zeros(len(xz)),xz[:,1]])[0]
 cloud=[]
 def refine(x0,x1,z0,z1,depth):
  u,v=np.meshgrid(np.linspace(0,1,5),np.linspace(0,1,5),indexing='ij');xz=np.c_[x0+(x1-x0)*u.ravel(),z0+(z1-z0)*v.ravel()];h=height(xz).reshape(5,5);a,b,c,d=h[0,0],h[4,0],h[0,4],h[4,4];approx=a*(1-u)*(1-v)+b*u*(1-v)+c*(1-u)*v+d*u*v
  if depth<4 and (abs(h-approx).max()>.006 or abs(a+d-b-c)>.024):
   xm=(x0+x1)/2;zm=(z0+z1)/2
   for lo,hi in [(x0,xm),(xm,x1)]:
    for za,zb in [(z0,zm),(zm,z1)]:refine(lo,hi,za,zb,depth+1)
  else:cloud.extend([[x0,z0],[x1,z0],[x0,z1],[x1,z1],[(x0+x1)/2,(z0+z1)/2]])
 x0,z0,x1,z1=region.bounds;nx=max(1,int(np.ceil((x1-x0)/.12)));nz=max(1,int(np.ceil((z1-z0)/.12)))
 for i in range(nx):
  for k in range(nz):
   a=x0+(x1-x0)*i/nx;b=x0+(x1-x0)*(i+1)/nx;c=z0+(z1-z0)*k/nz;d=z0+(z1-z0)*(k+1)/nz
   if region.intersects(box(a,c,b,d)):refine(a,b,c,d,0)
 for poly in parts(region):
  if not isinstance(poly,Polygon):continue
  for ring in [poly.exterior,*poly.interiors]:
   line=LineString(ring.coords);cloud.extend(line.interpolate(t,normalized=True).coords[0] for t in np.linspace(0,1,max(4,int(np.ceil(line.length/.035))),endpoint=False))
 cloud=np.unique(np.round(cloud,9),axis=0);cloud=cloud[contains_xy(region.buffer(1e-8),cloud[:,0],cloud[:,1])]
 for iteration in range(4):
  dt=Delaunay(cloud);q=cloud[dt.simplices];h=height(cloud)[dt.simplices];samples=np.concatenate([q.mean(1), (q[:,0]+q[:,1])/2,(q[:,1]+q[:,2])/2,(q[:,2]+q[:,0])/2]);linear=np.concatenate([h.mean(1),(h[:,0]+h[:,1])/2,(h[:,1]+h[:,2])/2,(h[:,2]+h[:,0])/2]);actual=height(samples);mask=contains_xy(region.buffer(1e-9),samples[:,0],samples[:,1]);bad=(abs(linear-actual)>.006)&mask
  if not bad.any():break
  cloud=np.unique(np.round(np.concatenate([cloud,samples[bad]]),9),axis=0)
 groups={};all_boundary=[];counter=0
 for ids in Delaunay(cloud).simplices:
  tri=Polygon(cloud[ids]);piece=tri if region.covers(tri) else tri.intersection(region)
  for poly in parts(piece):
   if not isinstance(poly,Polygon) or poly.area<1e-12:continue
   for tr in constrained_delaunay_triangles(poly).geoms:
    xz=np.array(list(tr.exterior.coords)[:-1]);y=height(xz);q=np.c_[xz[:,0],y,xz[:,1]]
    if np.cross(q[1]-q[0],q[2]-q[0])[1]>0:q=q[::-1]
    n=np.cross(q[1]-q[0],q[2]-q[0]);n/=np.linalg.norm(n);offset=float(n@q[0]);precision=4 if abs(n[1])>.20 else 5;key=tuple(np.round(n,precision))+(round(offset,precision),);counter+=1
    groups.setdefault(key,[]).append(Polygon(xz));all_boundary.extend(xz)
 m=Mesh()
 for triangles in groups.values():
  merged=union_all(triangles)
  for poly in parts(merged):
   if not isinstance(poly,Polygon) or poly.area<1e-12:continue
   poly=poly.simplify(.0001,preserve_topology=True)
   for tr in constrained_delaunay_triangles(poly).geoms:
    xz=np.array(list(tr.exterior.coords)[:-1]);y=height(xz);q=np.c_[xz[:,0],y,xz[:,1]]
    if np.cross(q[1]-q[0],q[2]-q[0])[1]>0:q=q[::-1]
    m.face(q,outer);m.face(q[::-1]+np.array([0.,thickness,0.]),inner)
 all_boundary=np.unique(np.round(all_boundary,9),axis=0)
 for poly in parts(region):
  if not isinstance(poly,Polygon):continue
  for ring in [poly.exterior,*poly.interiors]:
   line=LineString(ring.coords);near=all_boundary[distance(points(all_boundary),line)<1e-7]
   near=near[np.argsort(line_locate_point(line,points(near)))];y=height(near)
   for i in range(len(near)):
    j=(i+1)%len(near);a=(near[i,0],y[i],near[i,1]);b=(near[j,0],y[j],near[j,1]);q=[a,b,(b[0],b[1]+thickness,b[2]),(a[0],a[1]+thickness,a[2])];color=tuple((int(o)+int(ii))//2 for o,ii in zip(outer,inner));m.face(q,color);m.face(q[::-1],color)
 return m

# Cache deterministic skin triangulation; fitting hinges does not change the skin.
_uncached_make_panel = make_panel

def panel_cache_key(env,region,outer,inner,thickness=.012):
 import hashlib,json
 h=hashlib.sha256();h.update(env.bottom.tobytes());h.update(env.top.tobytes());h.update(region.wkb);h.update(json.dumps([env.low.tolist(),env.step,list(outer),list(inner),thickness]).encode());return h.hexdigest()

def make_panel(env,region,outer,inner,thickness=.012):
 from pathlib import Path
 import dnm
 path=Path(__file__).resolve().parent/'.panel-cache'/(panel_cache_key(env,region,outer,inner,thickness)+'.srf')
 if path.exists():return dnm.mesh(path.read_text().splitlines())
 m=_uncached_make_panel(env,region,outer,inner,thickness);path.parent.mkdir(exist_ok=True);path.write_text('\n'.join(m.srf())+'\n');return dnm.mesh(path.read_text().splitlines())
