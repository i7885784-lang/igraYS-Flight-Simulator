"""Large planar facets on the four confirmed skin/shutter surfaces; immutable animation records."""
from pathlib import Path
import sys,json,hashlib,collections,argparse
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'su30sm-local-skin'))
from repair import dnm,make_panel,polygons
from fit_field import world,PAINT
import numpy as np,shapely,triangle,osqp
from scipy import sparse
from shapely.geometry import Polygon,Point,LineString,MultiPoint
from shapely.strtree import STRtree

def exterior(lines,node):
 """Retain every painted front triangle; do not turn thin faces into holes."""
 m=dnm.mesh(lines);R,t=world(node);v=np.array(m.v)@R.T+t;out=[]
 for ids,c,b in m.f:
  if c not in PAINT:continue
  for j in range(1,len(ids)-1):
   q=v[[ids[0],ids[j],ids[j+1]]]
   if np.cross(q[1]-q[0],q[2]-q[0])[1]<-1e-16:out.append((q,c))
 return out

class StableProjected:
 """Relative barycentric evaluation avoids cancellation on very thin rim faces."""
 def __init__(self,tris,sg):
  self.polys=[];self.origins=[];self.grad=[];self.base=[];self.cache={}
  for q in tris:
   xy=np.c_[sg*q[:,0],q[:,2]];poly=Polygon(xy)
   if poly.area<1e-14:continue
   self.polys.append(poly);self.origins.append(xy[0]);self.base.append(q[0,1]);self.grad.append(np.linalg.solve(xy[1:]-xy[0],q[1:,1]-q[0,1]))
  self.origins=np.array(self.origins);self.base=np.array(self.base);self.grad=np.array(self.grad);self.tree=STRtree(self.polys)
 def heights(self,uv):
  ids=self.tree.query(Point(*uv),predicate='intersects')
  return self.base[ids]+np.einsum('ij,ij->i',np.array(uv)-self.origins[ids],self.grad[ids])
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
NAMES=['MainBayFixedSkin_Left','MainBayFixedSkin_Right','MainWheelBayShutter_Left','MainWheelBayShutter_Right']
def sha(b):return hashlib.sha256(b).hexdigest()
def build_panel(p,ns,name):
 NAME=name;PACK=name+'.srf';side='Left' if name.endswith('Left') else 'Right';sg=-1 if side=='Left' else 1;shutter_panel=name.startswith('MainWheel')
 n=next(n for n in ns if dnm.name(n)==name)
 source=exterior(p[PACK],n);q=np.array([t for t,c in source]);colors=[c for t,c in source]
 uv,inv=np.unique(np.round(np.c_[sg*q[:,:,0].ravel(),q[:,:,2].ravel()],6),axis=0,return_inverse=True);faces=inv.reshape(-1,3);height=np.full(len(uv),np.inf);np.minimum.at(height,inv,q[:,:,1].ravel())
 edges=collections.Counter(tuple(sorted((a,b))) for ids in faces for a,b in zip(ids,np.roll(ids,-1)))
 boundary=sorted({i for (a,b),count in edges.items() if count==1 for i in (a,b)})
 source_uv=[Polygon(uv[ids]) for ids in faces];domain=max(polygons(shapely.union_all(source_uv,grid_size=1e-6)),key=lambda t:t.area)
 numerical_holes=[Polygon(r).area for r in domain.interiors];assert sum(numerical_holes)<1e-7
 domain=Polygon(domain.exterior.coords)
 boundary=[i for i in boundary if domain.boundary.distance(Point(*uv[i]))<2e-6]
 # Every solve samples the clean original companion across the 2-mm gap.
 # Earlier panel results are never fed into the next panel solve.
 other_name=('MainBayFixedSkin_' if shutter_panel else 'MainWheelBayShutter_')+side
 other=next(v for v in ns if dnm.name(v)==other_name)
 snapped=np.c_[sg*uv[:,0],height,uv[:,1]][faces]
 reference=Projected([*snapped,*[t for t,c in exterior(p[dnm.fil(other)],other)]],sg)
 # Refinement adds a whole station, never scattered adaptive points.
 # Pin each original contour; retain a narrow fitting rim before the planes.
 xs=np.array([1.03,1.06,1.20,1.40,1.60,1.78,1.87])
 zs=np.array([-3.38,-3.34,-2.65,-1.86,-1.25,-.66,-.45,-.41])
 rounds=[]
 anchors={tuple(uv[i]):height[i] for i in boundary}
 class Strips:
  def values(self,points):
   ix=np.clip(np.searchsorted(xs,points[:,0],side='right')-1,0,len(xs)-2)
   iz=np.clip(np.searchsorted(zs,points[:,1],side='right')-1,0,len(zs)-2)
   a=(points[:,0]-xs[ix])/(xs[ix+1]-xs[ix]);b=(points[:,1]-zs[iz])/(zs[iz+1]-zs[iz])
   # Same diagonal in each station cell: piecewise planar, no twisted quads.
   v00=grid[ix,iz];v10=grid[ix+1,iz];v01=grid[ix,iz+1];v11=grid[ix+1,iz+1]
   return np.where(a>=b,v00+(v10-v00)*a+(v11-v10)*b,v00+(v11-v01)*a+(v01-v00)*b)
  def basis(self,points):
   ix=np.clip(np.searchsorted(xs,points[:,0],side='right')-1,0,len(xs)-2);iz=np.clip(np.searchsorted(zs,points[:,1],side='right')-1,0,len(zs)-2)
   a=(points[:,0]-xs[ix])/(xs[ix+1]-xs[ix]);b=(points[:,1]-zs[iz])/(zs[iz+1]-zs[iz]);ny=len(zs)
   ids=np.c_[ix*ny+iz,(ix+1)*ny+iz,(ix+1)*ny+iz+1,ix*ny+iz+1]
   w=np.where((a>=b)[:,None],np.c_[1-a,a-b,b,np.zeros(len(a))],np.c_[1-b,np.zeros(len(a)),a,b-a])
   return sparse.csc_matrix((w.ravel(),(np.repeat(np.arange(len(a)),4),ids.ravel())),shape=(len(points),len(xs)*len(zs)))
  def height(self,points):
   raw=self.values(points);d=shapely.distance(shapely.points(points),domain.boundary)
   w=np.clip((d-(.025 if shutter_panel else .04))/.03,0,1);w=w*w*(3-2*w)
   for i in np.where(w<1)[0]:raw[i]=w[i]*raw[i]+(1-w[i])*reference.lower(points[i],nearest=True)
   for i,point in enumerate(points):
    if tuple(point) in anchors:raw[i]=anchors[tuple(point)]
   return raw
 field=Strips();field.sg=sg
 for iteration in range(120):
  grid=np.array([[reference.lower([x,z],nearest=True) for z in zs] for x in xs])
  approx=field.height(uv);err=abs(approx-height);maximum=float(max(err));rounds.append(maximum)
  print('station fit',iteration,len(xs),len(zs),maximum,uv[int(np.argmax(err))],flush=True)
  if maximum<.035:break
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
 rim=domain.boundary.buffer(.06 if shutter_panel else .075)
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
 # Integer noding can detach a micron-scale sliver at a pinched corner.
 edge_faces=collections.defaultdict(list)
 for fi,ids in enumerate(tri):
  for a,b in zip(ids,np.roll(ids,-1)):edge_faces[tuple(sorted((a,b)))].append(fi)
 adjacency=collections.defaultdict(set)
 for adjacent in edge_faces.values():
  if len(adjacent)==2:adjacency[adjacent[0]].add(adjacent[1]);adjacency[adjacent[1]].add(adjacent[0])
 remaining_faces=set(range(len(tri)));components=[]
 while remaining_faces:
  stack=[min(remaining_faces)];remaining_faces.remove(stack[0]);component=[]
  while stack:
   fi=stack.pop();component.append(fi)
   for fj in adjacency[fi]:
    if fj in remaining_faces:remaining_faces.remove(fj);stack.append(fj)
  components.append(component)
 components.sort(key=len,reverse=True);discarded=[]
 for group in components[1:]:
  points=vertices[sorted({i for fi in group for i in tri[fi]})];area=sum(Polygon(vertices[tri[fi]]).area for fi in group);extent=float(max(np.ptp(points,axis=0)));assert area<1e-9 and extent<1e-4,(name,area,extent)
  discarded.append({'area_m2':area,'extent_m':extent})
 keep=sorted(components[0]);tri=[tri[i] for i in keep];cols=[cols[i] for i in keep]
 used=sorted({i for ids in tri for i in ids});remap={i:j for j,i in enumerate(used)};vertices=vertices[used];tri=[[remap[i] for i in ids] for ids in tri]
 part={'uv':vertices,'faces':tri,'colors':cols,'domain':domain,'paint_missing_m2':remaining.area,'discarded_disconnected_outline_areas_m2':[]}
 reference=Projected(list(snapped),sg);clearance={}
 if shutter_panel:
  body_node=next(n for n in ns if dnm.name(n)=='Fuselage_0_4');body_mesh=dnm.mesh(p[dnm.fil(body_node)]);R,t=world(body_node);bv=np.array(body_mesh.v)@R.T+t;body_tris=[]
  for ids,c,b in body_mesh.f:
   for j in range(1,len(ids)-1):
    q=bv[[ids[0],ids[j],ids[j+1]]]
    if (sg*q[:,0]).max()<1.03 or (sg*q[:,0]).min()>1.87 or q[:,2].max()<-1.858 or q[:,2].min()>-.662:continue
    body_tris.append(q)
  projections=[MultiPoint(np.c_[sg*q[:,0],q[:,2]]).convex_hull for q in body_tris];body_tree=STRtree(projections)
  weights=shapely.distance(shapely.points(vertices),domain.boundary);weights=np.clip((weights-.025)/.03,0,1);weights=weights*weights*(3-2*weights)
  h0=np.array([reference.lower(v,nearest=True) for v in vertices])
  for j,v in enumerate(vertices):
   if tuple(v) in anchors:weights[j]=0;h0[j]=anchors[tuple(v)]
  A=field.basis(vertices).multiply(weights[:,None]).tocsr();denseA=A.toarray();offset=(1-weights)*h0
  constraints={};vertical_count=0;inherited=0
  def coords_of(g):
   if g.is_empty:return []
   if g.geom_type=='Polygon':return list(g.exterior.coords)[:-1]
   if g.geom_type in ['LineString','Point']:return list(g.coords)
   return [xy for child in shapely.get_parts(g) for xy in coords_of(child)]
  def body_range(q,point):
   xy=np.c_[sg*q[:,0],q[:,2]];edges=xy[1:]-xy[0];det=np.linalg.det(edges)
   if abs(det)>1e-14:
    uvb=np.linalg.solve(edges.T,np.array(point)-xy[0]);y=q[0,1]+uvb@(q[1:,1]-q[0,1]);return float(y),float(y),False
   delta=xy-xy[0];direction=delta[int(np.argmax(np.linalg.norm(delta,axis=1)))];length=np.linalg.norm(direction)
   if length<1e-12:return float(min(q[:,1])),float(max(q[:,1])),True
   direction=direction/length;tt=delta@direction;t0=(np.array(point)-xy[0])@direction;values=[]
   for i,j in [(0,1),(1,2),(2,0)]:
    if min(tt[i],tt[j])-1e-8<=t0<=max(tt[i],tt[j])+1e-8:
     if abs(tt[j]-tt[i])<1e-12:values.extend([q[i,1],q[j,1]])
     else:values.append(q[i,1]+(q[j,1]-q[i,1])*(t0-tt[i])/(tt[j]-tt[i]))
   assert values;return float(min(values)),float(max(values)),True
  for face_index,ids in enumerate(tri):
   if face_index%5000==0:print(name,'body constraints',face_index,len(constraints),'ambiguous',inherited,flush=True)
   pp=vertices[ids];poly=Polygon(pp);inverse=np.linalg.inv((pp[1:]-pp[0]).T)
   for bi in body_tree.query(poly,predicate='intersects'):
    inter=poly.intersection(projections[int(bi)])
    for point in coords_of(inter):
     pair=inverse@(np.array(point)-pp[0]);bary=np.r_[1-sum(pair),pair];minimum,maximum,is_vertical=body_range(body_tris[int(bi)],point);old_height=reference.lower(point,nearest=True)
     lower=-np.inf;upper=np.inf
     if old_height<=minimum+1e-7:upper=max(old_height,minimum-.001-.0002)
     elif old_height>=maximum-1e-7:lower=min(old_height,maximum+.0002)
     else:
      inherited+=1
      # A projected point can lie on a triangulation seam. Choose the same
      # nearby side as the baseline, without moving its anchored boundary.
      if old_height-(minimum+maximum)/2<0:upper=minimum-.001-.0002
      else:lower=maximum+.0002
     row=bary@denseA[ids];base=float(bary@offset[ids]);nz=np.flatnonzero(abs(row)>1e-14)
     if not len(nz):
      assert lower-base<=1e-5 and upper-base>=-1e-5,(name,'protected boundary conflicts with body');continue
     key=tuple(zip(nz.tolist(),np.round(row[nz],9).tolist()))+(round(base,9),)
     if key in constraints:
      constraints[key][2]=max(constraints[key][2],lower-base);constraints[key][3]=min(constraints[key][3],upper-base)
     else:constraints[key]=[nz,row[nz],lower-base,upper-base]
     vertical_count+=int(is_vertical)
  rows=[];cols_sparse=[];data=[];lo=[];hi=[]
  for index,(nz,values,lower,upper) in enumerate(constraints.values()):
   rows.extend([index]*len(nz));cols_sparse.extend(nz.tolist());data.extend(values.tolist());lo.append(lower);hi.append(upper)
  flat=grid.ravel().copy();count=len(flat);G=sparse.csc_matrix((data,(rows,cols_sparse)),shape=(len(lo),count));C=sparse.vstack([G,sparse.eye(count)],format='csc');low=np.r_[lo,flat-.08];high=np.r_[hi,flat+.08]
  solver=osqp.OSQP();solver.setup(P=2*sparse.eye(count,format='csc'),q=-2*flat,A=C,l=low,u=high,eps_abs=1e-9,eps_rel=1e-9,max_iter=100000,polishing=True,verbose=False,adaptive_rho_interval=100);result=solver.solve();assert result.info.status_val in [1,2],result.info.status
  values=C@result.x;violation=float(max(np.maximum(low-values,0).max(),np.maximum(values-high,0).max()));assert violation<1e-6
  grid=result.x.reshape(grid.shape);clearance={'mesh':'Fuselage_0_4','rows':len(lo),'vertical_constraints':vertical_count,'ambiguous_baseline_samples':inherited,'max_constraint_violation_m':violation,'max_station_adjustment_m':float(max(abs(result.x-flat))),'status':result.info.status};print(name,'clearance',clearance,flush=True)
 actual=field.height(vertices);original=np.array([reference.lower(point,nearest=True) for point in vertices]);deviation=abs(actual-original);print('final vertex deviation',float(max(deviation)),vertices[int(np.argmax(deviation))],flush=True);assert max(deviation)<.08

 border_deviation=float(max(abs(field.height(uv[boundary])-height[boundary])));print('boundary delta',border_deviation,flush=True);assert border_deviation<1e-7
 m,meta=make_panel(part,field,n,.001 if shutter_panel else .008)
 audit={'name':name,'filled_projection_holes_m2':numerical_holes,'clearance':clearance,'discarded_numeric_planar_components':discarded,'ordered_x_stations':xs.tolist(),'ordered_z_stations':zs.tolist(),'source_exterior_triangles':len(source),'result_exterior_triangles':len(tri),'max_sampled_height_deviation_m':float(max(deviation)),'rms_sampled_height_deviation_m':float(np.sqrt(np.mean(deviation**2))),'max_boundary_height_deviation_m':border_deviation,'adaptation_max_errors_m':rounds,'paint_projection_grid_m':1e-6,'shell':meta}
 print(name,'done',audit['max_sampled_height_deviation_m'],flush=True);return m.srf(),audit

def run(baseline,output):
 assert sha(baseline.read_bytes())==BASE
 p,ns=dnm.read(baseline);original={k:list(v) for k,v in p.items()};audit={'baseline_sha256':BASE,'panels':{}}
 for name in NAMES:
  p[name+'.srf'],meta=build_panel(original,ns,name);audit['panels'][name]=meta
 assert set(k for k in p if p[k]!=original[k])=={n+'.srf' for n in NAMES}
 output.parent.mkdir(parents=True,exist_ok=True);dnm.write(output,p,ns);audit.update(model_sha256=sha(output.read_bytes()),all_node_records_exact=True,unchanged_packs=len(p)-len(NAMES));output.with_suffix('.audit.json').write_text(json.dumps(audit,indent=2));print('MODEL',audit['model_sha256'],flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--baseline',type=Path,required=True);a.add_argument('--output',type=Path,required=True);x=a.parse_args();run(x.baseline,x.output)
