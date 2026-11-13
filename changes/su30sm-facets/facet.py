"""Facet only MainBayFixedSkin_Left; retain protected PCKs/nodes and paint boundaries."""
from pathlib import Path
import sys,json,hashlib,collections,argparse
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'su30sm-local-skin'))
from repair import dnm,make_panel,polygons
from fit_field import exterior,world,Projected
import numpy as np,shapely,triangle
from shapely.geometry import Polygon,Point,LineString
from shapely.strtree import STRtree
from scipy.spatial import Delaunay,cKDTree
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
 tree=cKDTree(uv);xx,zz=np.meshgrid(np.arange(1.03,1.88,.16),np.arange(-3.38,-.40,.30));samples=np.c_[xx.ravel(),zz.ravel()]
 selected=set(boundary)|set(map(int,tree.query(samples)[1]));rounds=[]
 for iteration in range(80):
  sel=np.array(sorted(selected));macro=Delaunay(uv[sel]);sid=macro.find_simplex(uv,tol=1e-8);assert min(sid)>=0
  tf=macro.transform[sid];b=np.einsum('ijk,ik->ij',tf[:,:2],uv-tf[:,2]);weights=np.c_[b,1-b.sum(1)];h=np.sum(height[sel][macro.simplices[sid]]*weights,axis=1);err=abs(h-height);maximum=float(err.max());rounds.append(maximum)
  if maximum<.008:break
  # Select the worst sample in each 4-cm bin to refine tight curvature locally.
  bins=set();added=[]
  for i in np.argsort(err)[::-1]:
   if err[i]<.006 or len(added)>=120:break
   cell=tuple(np.floor(uv[i]/.04).astype(int))
   if int(i) not in selected and cell not in bins:added.append(int(i));bins.add(cell)
  assert added;selected.update(added)
 else:raise AssertionError('Facet error budget did not converge')
 print('macro facets',len(macro.simplices),'max vertex error',maximum,flush=True)
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
 macro_edges={tuple(sorted((int(a),int(b)))) for ids in macro.simplices for a,b in zip(ids,np.roll(ids,-1))}
 lines.extend(LineString(uv[sel][list(ids)]) for ids in sorted(macro_edges))
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
 class Facets:
  sg=-1
  def height(self,points):
   ids=macro.find_simplex(points,tol=2e-6);assert min(ids)>=0
   tf=macro.transform[ids];b=np.einsum('ijk,ik->ij',tf[:,:2],points-tf[:,2]);return np.sum(height[sel][macro.simplices[ids]]*np.c_[b,1-b.sum(1)],axis=1)
 field=Facets();part={'uv':vertices,'faces':tri,'colors':cols,'domain':domain,'paint_missing_m2':remaining.area,'discarded_disconnected_outline_areas_m2':[]}
 reference=Projected(list(q),-1);actual=field.height(vertices);original=np.array([reference.lower(point,nearest=True) for point in vertices]);deviation=abs(actual-original);assert max(deviation)<.012
 border_deviation=float(max(abs(field.height(uv[boundary])-height[boundary])));assert border_deviation<1e-7
 m,meta=make_panel(part,field,n,.008);p[PACK]=m.srf();assert [k for k in p if p[k]!=old[k]]==[PACK]
 output.parent.mkdir(parents=True,exist_ok=True);dnm.write(output,p,ns)
 audit={'baseline_sha256':BASE,'model_sha256':sha(output.read_bytes()),'changed_pack':PACK,'unchanged_packs':len(p)-1,'all_node_records_exact':True,'coarse_facets':len(macro.simplices),'source_exterior_triangles':len(source),'result_exterior_triangles':len(tri),'max_sampled_shape_deviation_m':float(max(deviation)),'rms_sampled_shape_deviation_m':float(np.sqrt(np.mean(deviation**2))),'max_boundary_height_deviation_m':border_deviation,'adaptation_max_errors_m':rounds,'paint_projection_grid_m':1e-6,'shell':meta}
 output.with_suffix('.audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps({k:v for k,v in audit.items() if k!='shell'},indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--baseline',type=Path,required=True);a.add_argument('--output',type=Path,required=True);x=a.parse_args();run(x.baseline,x.output)
