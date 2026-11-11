"""Repair exactly four panels using one constrained continuous curved reference per side."""
from pathlib import Path
import sys,json,hashlib,collections,argparse
import numpy as np,shapely,triangle
from shapely.geometry import Polygon,Point,box,LineString
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'model-source'))
from common import dnm,Mesh
from fit_field import Field,world,exterior,PAINT,NAMES,blend
BASELINE='bfabbd8ff2728ca417cbb9bb948fff27c750de297a156c718aafb51705d4ce83'
def sha(b):return hashlib.sha256(b).hexdigest()
def polygons(g):return [p for p in shapely.get_parts(g) if p.geom_type=='Polygon' and p.area>1e-12]
def layout(p,n,field,name):
 sg=field.sg;old=exterior(p[dnm.fil(n)],n);pp=[Polygon(np.c_[sg*q[:,0],q[:,2]]) for q,c in old];fixed=name.startswith('MainBayFixedSkin')
 nominal=box(1.03,-3.38,1.87,-.41).difference(box(1.05,-1.86,1.87,-.66)) if fixed else box(1.052,-1.858,1.87,-.662)
 domain=shapely.union_all([nominal,*pp],grid_size=1e-6) if fixed else nominal
 domain=shapely.set_precision(domain,1e-6);pieces=polygons(domain);discarded_outline_areas=sorted([part.area for part in pieces],reverse=True)[1:];domain=max(pieces,key=lambda part:part.area);print('outline fragments',name,discarded_outline_areas,flush=True)
 assert domain.difference(nominal.buffer(.005)).area<1e-8,'Unconfirmed expansion outside original outline'
 groups=collections.defaultdict(list)
 for poly,(q,c) in zip(pp,old):groups[c].append(poly)
 cp=[];cc=[];remaining=domain
 for c in sorted(groups):
  reg=shapely.union_all(groups[c],grid_size=1e-6).intersection(remaining)
  for cut in polygons(reg):cp.append(cut);cc.append(c)
  remaining=remaining.difference(reg)
 print('colors ready',name,len(cp),flush=True);ct=STRtree(cp);missing=remaining.area;assert missing<1e-5,(name,'unpainted',missing)
 anchor=domain.difference(box(1.06,-3.34,1.79,-.45));lines=[domain.boundary]+[poly.boundary for poly in cp]
 for poly in pp:
  if poly.intersects(anchor):lines.append(poly.intersection(anchor).boundary)
 for x in sorted(set(np.round(np.r_[np.arange(1.03,1.87,.01),1.03,1.05,1.052,1.06,1.79,1.85,1.87],6))):lines.append(LineString([(x,-3.39),(x,-.40)]))
 for z in sorted(set(np.round(np.r_[np.arange(-3.38,-.41,.02),-3.38,-3.34,-1.86,-1.858,-.662,-.66,-.45,-.41],6))):lines.append(LineString([(1.02,z),(1.88,z)]))
 print('noding',name,len(lines),flush=True);graph=shapely.union_all(lines,grid_size=1e-6);coords=set();segments=set()
 for line in shapely.get_parts(graph):
  if line.geom_type!='LineString':continue
  for a,b in zip(line.coords,list(line.coords)[1:]):
   a=tuple(np.round(a,6));b=tuple(np.round(b,6))
   if a!=b:coords.update([a,b]);segments.add(tuple(sorted((a,b))))
 coords=sorted(coords);indices={v:i for i,v in enumerate(coords)};print('triangulate',name,len(coords),len(segments),flush=True);planar=triangle.triangulate({'vertices':np.round(np.array(coords)*1e6),'segments':np.array(sorted((indices[a],indices[b]) for a,b in segments),np.int32)},'pQ');uv=np.array(planar['vertices'])/1e6;tolerant_domain=shapely.set_precision(domain,0).buffer(2e-6);print('triangles',name,len(planar['triangles']),flush=True);faces=[];colors=[]
 for ids in planar['triangles']:
  poly=Polygon(uv[ids]);pt=poly.representative_point()
  if not domain.covers(pt):continue
  if not tolerant_domain.covers(poly):
   print('OUTSIDE_TRIANGLE',uv[ids].tolist(),poly.area,poly.difference(domain).area,flush=True);raise AssertionError('Constraint crossed outline')
  if poly.area<1e-14:raise AssertionError('Unresolved numerical triangle')
  ci=ct.query(pt,predicate='intersects')
  color=cc[int(ci[0] if len(ci) else ct.nearest(pt))];faces.append(list(map(int,ids)));colors.append(color)
 used=sorted(set(i for ids in faces for i in ids));remap={i:j for j,i in enumerate(used)};uv=uv[used];faces=[[remap[i] for i in ids] for ids in faces]
 print('layout',name,len(uv),len(faces),flush=True);return {'uv':uv,'faces':faces,'colors':colors,'domain':domain,'paint_missing_m2':missing,'discarded_disconnected_outline_areas_m2':discarded_outline_areas}
def make_panel(part,field,n,thickness):
 uv=part['uv'];height=field.height(uv);vertices=np.c_[field.sg*uv[:,0],height,uv[:,1]];R,t=world(n);faces=[]
 for ids,c in zip(part['faces'],part['colors']):
  if np.cross(vertices[ids[1]]-vertices[ids[0]],vertices[ids[2]]-vertices[ids[0]])[1]>0:ids=ids[::-1]
  faces.append((list(ids),c))
 # Split boundary fans which touch at a parameter-space point. No position
 # changes: the two rim loops must not share one four-valent thickness edge.
 edge_faces=collections.defaultdict(list);vertex_faces=collections.defaultdict(list)
 for fi,(ids,c) in enumerate(faces):
  for i in ids:vertex_faces[i].append(fi)
  for a,b in zip(ids,ids[1:]+ids[:1]):edge_faces[tuple(sorted((a,b)))].append(fi)
 neighbours=collections.defaultdict(lambda:collections.defaultdict(set))
 for (a,b),ii in edge_faces.items():
  if len(ii)==2:
   for v in [a,b]:neighbours[v][ii[0]].add(ii[1]);neighbours[v][ii[1]].add(ii[0])
 points=list(vertices);pinches=0
 for v,incident in vertex_faces.items():
  remaining=set(incident);groups=[]
  while remaining:
   stack=[min(remaining)];remaining.remove(stack[0]);group=[]
   while stack:
    fi=stack.pop();group.append(fi)
    for fj in neighbours[v][fi]:
     if fj in remaining:remaining.remove(fj);stack.append(fj)
   groups.append(group)
  for group in groups[1:]:
   new=len(points);points.append(vertices[v]);pinches+=1
   for fi in group:
    ids,c=faces[fi];faces[fi]=([new if i==v else i for i in ids],c)
 vertices=np.array(points);back=vertices+[0,thickness,0];m=Mesh();m.v=[tuple(np.round(a,10)) for a in (vertices-t)@R]+[tuple(np.round(a,10)) for a in (back-t)@R];nv=len(vertices);edges=collections.Counter()
 for ids,c in faces:
  m.f.append((ids,c,False));m.f.append(([i+nv for i in ids[::-1]],(148,153,148),False))
  for a,b in zip(ids,ids[1:]+ids[:1]):edges[tuple(sorted((a,b)))]+=1
 assert max(edges.values())<=2
 for ids,c in faces:
  for a,b in zip(ids,ids[1:]+ids[:1]):
   if edges[tuple(sorted((a,b)))]==1:m.f.append(([b,a,a+nv,b+nv],(105,118,123),False))
 return m,{'exterior_triangles':len(faces),'boundary_segments':sum(v==1 for v in edges.values()),'pinch_fans_split_without_moving_vertices':pinches,'projected_area_m2':part['domain'].area,'paint_coverage_missing_m2':part['paint_missing_m2'],'discarded_disconnected_outline_areas_m2':part['discarded_disconnected_outline_areas_m2'],'thickness_y_m':thickness,'height_range_m':[float(min(height)),float(max(height))],'source':'shared constrained curved reference; no independent per-triangle height fitting','projected_vertex_grid_m':1e-6}

def repair(baseline,output):
 assert sha(baseline.read_bytes())==BASELINE,'Wrong baseline; no silent rollback'
 p,ns=dnm.read(baseline);old={k:list(v) for k,v in p.items()};lu={dnm.name(n):n for n in ns};parts={};fields={};audit={'baseline_sha256':BASELINE,'panels':{},'fits':{}}
 for side,sg in [('Left',-1),('Right',1)]:
  field=Field(p,ns,sg);fields[sg]=field
  for name in [s for s in NAMES if s.endswith(side)]:parts[name]=layout(p,lu[name],field,name)
  vertices=np.vstack([part['uv'] for name,part in parts.items() if name.endswith(side)]);field.fit(vertices);audit['fits'][side]=field.audit
 for name in NAMES:
  sg=-1 if name.endswith('Left') else 1;m,meta=make_panel(parts[name],fields[sg],lu[name],.008 if name.startswith('MainBayFixedSkin') else .001);p[dnm.fil(lu[name])]=m.srf();audit['panels'][name]=meta
 changed=[k for k in p if p[k]!=old[k]];assert set(changed)=={dnm.fil(lu[n]) for n in NAMES};output.parent.mkdir(parents=True,exist_ok=True);dnm.write(output,p,ns);audit['model_sha256']=sha(output.read_bytes());audit['changed_packs']=changed;audit['all_node_records_exact']=True;audit['unchanged_packs']=len(p)-4;output.with_suffix('.audit.json').write_text(json.dumps(audit,indent=2));print('MODEL',audit['model_sha256'],flush=True);return audit
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();repair(args.baseline,args.output)
