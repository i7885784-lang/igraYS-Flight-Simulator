"""Ordered planar strips on MainBayFixedSkin_Left; retain protected PCKs/nodes and paint boundaries."""
from pathlib import Path
import sys,json,hashlib,collections,argparse
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'su30sm-local-skin'))
from repair import dnm,make_panel,polygons
from fit_field import exterior,world
import numpy as np,shapely,triangle
from shapely.geometry import Polygon,Point,LineString
from shapely.strtree import STRtree

class StableProjected:
 """Relative barycentric evaluation avoids cancellation on very thin rim faces."""
 def __init__(self,tris,sg):
  self.polys=[];self.origins=[];self.grad=[];self.base=[];self.cache={}
  for q in tris:
   xy=np.c_[sg*q[:,0],q[:,2]];poly=Polygon(xy)
   if poly.area<1e-14:continue
   self.polys.append(poly);self.origins.append(xy[0]);self.base.append(q[0,1]);self.grad.append(np.linalg.solve(xy[1:]-xy[0],q[1:,1]-q[0,1]))
  self.origins=np.array(self.origins);self.base=np.array(self.base);self.grad=np.array(self.grad);self.tree=STRtree(self.polys)
 def lower(self,uv,nearest=False):
  key=tuple(np.round(uv,10))
  if key not in self.cache:
   point=Point(*uv);ids=self.tree.query(point,predicate='intersects')
   if not len(ids):
    if not nearest:return np.nan
    i=int(self.tree.nearest(point));assert self.polys[i].distance(point)<.006;ids=np.array([i])
   self.cache[key]=float(np.min(self.base[ids]+np.einsum('ij,ij->i',np.array(uv)-self.origins[ids],self.grad[ids])))
  return self.cache[key]
Projected=StableProjected
BASE='6f8e20b21990820dcc3aa49f91e92ef4a1771047951671f61732d111256b30c6'
NAME='MainBayFixedSkin_Left';PACK=NAME+'.srf'
def sha(b):return hashlib.sha256(b).hexdigest()
def run(baseline,output):
 assert sha(baseline.read_bytes())==BASE
 p,ns=dnm.read(baseline);old={k:list(v) for k,v in p.items()};n=next(n for n in ns if dnm.name(n)==NAME)
 source=exterior(p[PACK],n);q=np.array([t for t,c in source]);colors=[c for t,c in source]
 uv,inv=np.unique(np.round(np.c_[-q[:,:,0].ravel(),q[:,:,2].ravel()],6),axis=0,return_inverse=True);faces=inv.reshape(-1,3);height=np.full(len(uv),np.inf);np.minimum.at(height,inv,q[:,:,1].ravel())
 edges=collections.Counter(tuple(sorted((a,b))) for ids in faces for a,b in zip(ids,np.roll(ids,-1)))
 boundary=sorted({i for (a,b),count in edges.items() if count==1 for i in (a,b)})
 source_uv=[Polygon(uv[ids]) for ids in faces];domain=max(polygons(shapely.union_all(source_uv,grid_size=1e-6)),key=lambda t:t.area)
 # Sample the already repaired, single-valued surface, including the protected
 # shutter as a READ-ONLY height reference across the 2-mm parameter gap.
 shutter=next(v for v in ns if dnm.name(v)=='MainWheelBayShutter_Left')
 snapped=np.c_[-uv[:,0],height,uv[:,1]][faces]
 reference=Projected([*snapped,*[t for t,c in exterior(p[dnm.fil(shutter)],shutter)]],-1)
 # Refinement adds a whole station, never scattered adaptive points.
 # Preserve the original 40-mm rim; blend into the planes over the next 35 mm.
 xs=np.array([1.03,1.06,1.16,1.28,1.42,1.58,1.74,1.82,1.87])
 zs=np.array([-3.38,-3.34,-2.9,-2.4,-1.86,-1.50,-1.10,-.66,-.45,-.41])
 rounds=[]
 anchors={tuple(uv[i]):height[i] for i in boundary}
 class Strips:
  sg=-1
  def values(self,points):
   ix=np.clip(np.searchsorted(xs,points[:,0],side='right')-1,0,len(xs)-2)
   iz=np.clip(np.searchsorted(zs,points[:,1],side='right')-1,0,len(zs)-2)
   a=(points[:,0]-xs[ix])/(xs[ix+1]-xs[ix]);b=(points[:,1]-zs[iz])/(zs[iz+1]-zs[iz])
   # Same diagonal in each station cell: piecewise planar, no twisted quads.
   v00=grid[ix,iz];v10=grid[ix+1,iz];v01=grid[ix,iz+1];v11=grid[ix+1,iz+1]
   return np.where(a>=b,v00+(v10-v00)*a+(v11-v10)*b,v00+(v11-v01)*a+(v01-v00)*b)
  def height(self,points):
   raw=self.values(points);d=shapely.distance(shapely.points(points),domain.boundary)
   w=np.clip((d-.04)/.035,0,1);w=w*w*(3-2*w)
   for i in np.where(w<1)[0]:raw[i]=w[i]*raw[i]+(1-w[i])*reference.lower(points[i],nearest=True)
   for i,point in enumerate(points):
    if tuple(point) in anchors:raw[i]=anchors[tuple(point)]
   return raw
 field=Strips()
 for iteration in range(120):
  grid=np.array([[reference.lower([x,z],nearest=True) for z in zs] for x in xs])
  approx=field.height(uv);err=abs(approx-height);maximum=float(max(err));rounds.append(maximum)
  print('station fit',iteration,len(xs),len(zs),maximum,uv[int(np.argmax(err))],flush=True)
  if maximum<.018:break
  i=int(np.argmax(err));x,z=uv[i];ix=int(np.clip(np.searchsorted(xs,x)-1,0,len(xs)-2));iz=int(np.clip(np.searchsorted(zs,z)-1,0,len(zs)-2))
  # Choose the station direction with the larger local curvature contribution.
  x0,x1=xs[ix:ix+2];z0,z1=zs[iz:iz+2]
  xerr=abs(reference.lower([x,z],nearest=True)-np.interp(x,[x0,x1],[reference.lower([x0,z],nearest=True),reference.lower([x1,z],nearest=True)]))
  zerr=abs(reference.lower([x,z],nearest=True)-np.interp(z,[z0,z1],[reference.lower([x,z0],nearest=True),reference.lower([x,z1],nearest=True)]))
  if xerr>=zerr:xs=np.sort(np.r_[xs,round((x0+x1)/2,6)])
  else:zs=np.sort(np.r_[zs,round((z0+z1)/2,6)])
 else:raise AssertionError('Ordered station fit did not converge')
 print('ordered stations',len(xs),len(zs),'max bulk error',maximum,flush=True)
 # Paint cuts subdivide geometric facets without changing their planes.
 paint=collections.defaultdict(list)
 for poly,c in zip(source_uv,colors):paint[c].append(poly)
 regs=[];palette=[];remaining=domain
 for c in sorted(paint):
  reg=shapely.union_all(paint[c],grid_size=1e-6).intersection(remaining)
  for poly in polygons(reg):regs.append(poly);palette.append(c)
  remaining=remaining.difference(reg)
 assert remaining.area<1e-7
 lines=[domain.boundary]+[poly.boundary for poly in regs]
 # Conforming cuts at station lines, diagonals, paint and the exact outline.
 for x in xs:lines.append(LineString([(x,zs[0]),(x,zs[-1])]))
 for z in zs:lines.append(LineString([(xs[0],z),(xs[-1],z)]))
 for x0,x1 in zip(xs,xs[1:]):
  for z0,z1 in zip(zs,zs[1:]):lines.append(LineString([(x0,z0),(x1,z1)]))
 # Retain the original fine geometry only in the narrow anchored rim.
 rim=domain.boundary.buffer(.08)
 for poly in source_uv:
  if poly.intersects(rim):lines.append(poly.intersection(rim).boundary)
 graph=shapely.union_all(lines,grid_size=1e-6);coords=set();segments=set()
 for line in shapely.get_parts(graph):
  if line.geom_type!='LineString':continue
  for a,b in zip(line.coords,list(line.coords)[1:]):
   a=tuple(np.round(a,6));b=tuple(np.round(b,6))
   if a!=b:coords.update([a,b]);segments.add(tuple(sorted((a,b))))
 coords=sorted(coords);lookup={v:i for i,v in enumerate(coords)}
 planar=triangle.triangulate({'vertices':np.round(np.array(coords)*1e6),'segments':np.array(sorted((lookup[a],lookup[b]) for a,b in segments),np.int32)},'pQ')
 vertices=np.array(planar['vertices'])/1e6;ptree=STRtree(regs);tri=[];cols=[];tol=shapely.set_precision(domain,0).buffer(2e-6)
 for ids in planar['triangles']:
  poly=Polygon(vertices[ids]);pt=poly.representative_point()
  if not domain.covers(pt):continue
  assert tol.covers(poly) and poly.area>1e-14
  ci=ptree.query(pt,predicate='intersects')
  ci=int(ci[0]) if len(ci) else int(ptree.nearest(pt));assert regs[ci].distance(pt)<2e-6
  tri.append(list(map(int,ids)));cols.append(palette[ci])
 used=sorted({i for ids in tri for i in ids});remap={i:j for j,i in enumerate(used)};vertices=vertices[used];tri=[[remap[i] for i in ids] for ids in tri]
 part={'uv':vertices,'faces':tri,'colors':cols,'domain':domain,'paint_missing_m2':remaining.area,'discarded_disconnected_outline_areas_m2':[]}
 reference=Projected(list(snapped),-1);actual=field.height(vertices);original=np.array([reference.lower(point,nearest=True) for point in vertices]);deviation=abs(actual-original);print('final vertex deviation',float(max(deviation)),vertices[int(np.argmax(deviation))],flush=True);assert max(deviation)<.025
 border_deviation=float(max(abs(field.height(uv[boundary])-height[boundary])));print('boundary delta',border_deviation,flush=True);assert border_deviation<1e-7
 m,meta=make_panel(part,field,n,.008);p[PACK]=m.srf();assert [k for k in p if p[k]!=old[k]]==[PACK]
 output.parent.mkdir(parents=True,exist_ok=True);dnm.write(output,p,ns)
 audit={'baseline_sha256':BASE,'model_sha256':sha(output.read_bytes()),'changed_pack':PACK,'unchanged_packs':len(p)-1,'all_node_records_exact':True,'ordered_x_stations':xs.tolist(),'ordered_z_stations':zs.tolist(),'source_exterior_triangles':len(source),'result_exterior_triangles':len(tri),'max_sampled_shape_deviation_m':float(max(deviation)),'rms_sampled_shape_deviation_m':float(np.sqrt(np.mean(deviation**2))),'max_boundary_height_deviation_m':border_deviation,'adaptation_max_errors_m':rounds,'paint_projection_grid_m':1e-6,'shell':meta}
 output.with_suffix('.audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps({k:v for k,v in audit.items() if k!='shell'},indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--baseline',type=Path,required=True);a.add_argument('--output',type=Path,required=True);x=a.parse_args();run(x.baseline,x.output)
