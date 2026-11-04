import numpy as np,collections
import shapely
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union,polygonize

def build_surface(v,tri,side,paint,inset=.002,hinge_trim=.025,_excluded=(),_pass=0):
 pts=v[tri];P=[];coeff=[];src=[]
 for k,t in enumerate(pts):
  poly=Polygon(t[:,[0,2]])
  if poly.area<1e-12:continue
  P.append(shapely.set_precision(poly,1e-6));coeff.append(np.linalg.solve(np.c_[t[:,0],t[:,2],np.ones(3)],t[:,1]));src.append(k)
 coeff=np.array(coeff);domain=unary_union(P);safe=domain.buffer(-inset,join_style=2)
 sg=-1 if side=='Left' else 1
 safe=safe.intersection(box(-1.864,-1.853,-1.03-hinge_trim,-.664) if sg<0 else box(1.03+hinge_trim,-1.853,1.864,-.664))
 safe=shapely.set_precision(safe,0)
 if _excluded:safe=safe.difference(unary_union([shapely.Point(x,z).buffer(.0001,quad_segs=4) for x,z in _excluded]))
 paint_polys=[shapely.set_precision(Polygon(t[:,[0,2]]),1e-6) for t,col in paint];paint_colors=[col for t,col in paint];paint_tree=shapely.STRtree(paint_polys)
 paint_groups=collections.defaultdict(list)
 for poly,color in zip(paint_polys,paint_colors):paint_groups[tuple(color)].append(poly)
 paint_regions=[unary_union(polys) for polys in paint_groups.values()]
 lines=[p.boundary for p in paint_regions]+[p.boundary for p in P]+[safe.boundary,LineString([(sg*1.6,-3),(sg*1.6,1)]),LineString([(sg*1.68,-3),(sg*1.68,1)])]
 # Split where overlapping source planes exchange which surface is lowest.
 tree=shapely.STRtree(P)
 for i,p in enumerate(P):
  for j in tree.query(p,predicate='intersects'):
   if j<=i:continue
   overlap=p.intersection(P[j])
   if overlap.area<1e-10:continue
   c=coeff[i]-coeff[j]
   if np.linalg.norm(c[:2])<1e-10:continue
   x,z=np.array(overlap.representative_point().coords[0]);d=np.array([-c[1],c[0]]);d/=np.linalg.norm(d);o=np.array([x,z])-c[:2]*(c[0]*x+c[1]*z+c[2])/(c[:2]@c[:2]);cut=LineString([o-d*10,o+d*10]).intersection(overlap)
   if not cut.is_empty:lines.append(cut)
 # One constrained planar mesh for the whole domain: shared material and
 # source-surface edges are shared segments, never independently capped cells.
 import triangle
 graph=unary_union(shapely.set_precision(unary_union(lines),1e-6));points=[];lookup={};segments=set()
 def index(q):
  q=tuple(np.round(q,6))
  if q not in lookup:lookup[q]=len(points);points.append(q)
  return lookup[q]
 for line in shapely.get_parts(graph):
  if line.geom_type!='LineString':continue
  for a,b in zip(line.coords,list(line.coords)[1:]):
   i,j=index(a),index(b)
   if i!=j:segments.add(tuple(sorted((i,j))))
 order=sorted(range(len(points)),key=lambda i:points[i]);remap={old:new for new,old in enumerate(order)};canonical_segments=sorted({tuple(sorted((remap[a],remap[b]))) for a,b in segments})
 planar=triangle.triangulate({'vertices':np.array([points[i] for i in order]),'segments':np.array(canonical_segments,dtype=np.int32)},'pQ')
 xz=np.array(planar['vertices']);faces=[];outc=[];chosen=[];outside=0;paint_missing=0
 for ids in planar['triangles']:
  q=Polygon(xz[ids]);cen=q.representative_point()
  if not safe.buffer(1e-8).covers(q) or q.area<1e-12:continue
  candidates=tree.query(cen,predicate='covered_by')
  if not len(candidates):outside+=1;continue
  x,z=cen.x,cen.y;c=min(candidates,key=lambda k:coeff[k]@[x,z,1]);chosen.append(int(c));faces.append(ids)
  pc=paint_tree.query(cen,predicate='covered_by');outc.append(paint_colors[int(pc[0])] if len(pc) else (142,169,181));paint_missing+=int(len(pc)==0)
 assert len(faces)>0, 'No covered triangles'
 faces=np.array(faces,dtype=np.int32);heights=collections.defaultdict(list)
 for f,c in zip(faces,chosen):
  for vertex in f:heights[int(vertex)].append(float(coeff[c]@[xz[vertex,0],xz[vertex,1],1]))
 clusters={};max_deviation=0.;chart_splits=0;max_unbridged=0.
 for vertex,values in heights.items():
  groups=[]
  for y in sorted(values):
   if not groups or y-groups[-1][0]>2e-5:groups.append([y])
   else:groups[-1].append(y)
  clusters[vertex]=[g[0] for g in groups];max_deviation=max(max_deviation,max(max(g)-min(g) for g in groups));chart_splits+=int(len(groups)>1)
  if len(groups)>1:max_unbridged=max(max_unbridged,groups[-1][0]-groups[0][0])
 # Distinct height charts are not bridged by invented vertical geometry.
 outv=[];outfaces=[];lookup={}
 for f,c in zip(faces,chosen):
  ids=[]
  for vertex in f:
   x,z=xz[vertex];y=float(coeff[c]@[x,z,1]);y=min(clusters[int(vertex)],key=lambda a:abs(a-y));y-=.008*np.clip((abs(x)-1.6)/.08,0,1)+.00002;q=tuple(np.round([x,y,z],6))
   if q not in lookup:lookup[q]=len(outv);outv.append(q)
   ids.append(lookup[q])
  outfaces.append(ids)
 outv=np.array(outv);faces=np.array(outfaces);outf=[];colors=[];removed=0
 for f,color in zip(faces,outc):
  t=outv[f];normal=np.cross(t[1]-t[0],t[2]-t[0])
  if np.linalg.norm(normal)<1e-11:removed+=1;continue
  if normal[1]>0:f=f[::-1]
  outf.append(f);colors.append(color)
 outf=np.array(outf);outc=colors;edges=collections.Counter(tuple(sorted((int(a),int(b)))) for f in outf for a,b in zip(f,np.roll(f,-1)));cell_count=len(outf)
 boundary_degree=collections.Counter(v for edge,n in edges.items() if n==1 for v in edge);pinches=[i for i,degree in boundary_degree.items() if degree>2]
 if pinches:
  assert _pass<3, 'Unresolved surface pinch'
  cuts=tuple(sorted(set(_excluded)|{tuple(outv[i][[0,2]]) for i in pinches}))
  return build_surface(v,tri,side,paint,inset,hinge_trim,cuts,_pass+1)
 meta={'point_contact_relief_centers_xz_m':_excluded,'point_contact_relief_radius_m':.0001 if _excluded else 0,'paint_cells_missing':paint_missing,'height_chart_splits':chart_splits,'max_unbridged_source_height_jump_m':max_unbridged,'max_source_height_weld_error_m':max_deviation,'discarded_numeric_slivers':removed,'source_projected_area':domain.area,'new_projected_area':safe.area,'projected_area_retained_fraction':safe.area/domain.area,'numeric_outward_guard_m':.00002,'outboard_edge_clearance_m':.006,'rear_edge_clearance_m':.005,'outward_clearance_max_m':.008,'inset_m':inset,'hinge_clearance_m':hinge_trim,'cells':cell_count,'unsupported_cells':outside,'surface_triangles':len(outf),'boundary_edges':sum(n==1 for n in edges.values()),'nonmanifold_edges':sum(n>2 for n in edges.values()),'domain':shapely.to_wkt(domain,rounding_precision=8),'safe_domain':shapely.to_wkt(safe,rounding_precision=8)}
 assert len(outf)>0 and outside==0 and paint_missing==0 and meta['nonmanifold_edges']==0
 assert meta['projected_area_retained_fraction']>.90
 return outv,outf,outc,meta
