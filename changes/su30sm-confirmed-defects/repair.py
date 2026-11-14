"""Local front-skin repair only: connect measured existing mating sections without a folded rim.
Two fixed skins plus proven imported remnants in the main OUTER door apertures.
Every moving mesh, well, intake, DNM node, paint region and unrelated pack is immutable.
"""
from pathlib import Path
import sys,json,hashlib,collections,argparse
import numpy as np,shapely,triangle
from shapely.geometry import Polygon,Point,box,LineString
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'changes/su30sm-large-panels'));from facet import dnm,exterior,world,Projected,make_panel
from bay_cut import cut
BASE='91a201f3ca02d7c69345d197827b1567cedcc87edb51409ffc0006b8cc0ae61c'
NAMES=['MainBayFixedSkin_Left','MainBayFixedSkin_Right'];sha=lambda b:hashlib.sha256(b).hexdigest()
def parts(g):return [p for p in shapely.get_parts(g) if p.geom_type=='Polygon' and p.area>1e-12]
def graph_mesh(lines,domain):
 graph=shapely.union_all(lines,grid_size=1e-7);pts=set();segments=set()
 for line in shapely.get_parts(graph):
  if line.geom_type!='LineString':continue
  for a,b in zip(line.coords,list(line.coords)[1:]):
   a=tuple(np.round(a,7));b=tuple(np.round(b,7))
   if a!=b:pts.update([a,b]);segments.add(tuple(sorted((a,b))))
 pts=sorted(pts);lookup={p:i for i,p in enumerate(pts)};raw=triangle.triangulate({'vertices':np.array(pts),'segments':np.array([[lookup[a],lookup[b]] for a,b in sorted(segments)])},'pQ')
 uv=raw['vertices'];f=raw['triangles'];return uv,f[shapely.covers(domain,shapely.points(uv[f].mean(1)))]
def build_panel(p,lu,name):
 n=lu[name];sg=-1 if name.endswith('Left') else 1;old=exterior(p[dnm.fil(n)],n);tris=np.array([q for q,c in old]);polys=[Polygon(np.c_[sg*q[:,0],q[:,2]]) for q,c in old];domain=max(parts(shapely.union_all(polys,grid_size=1e-7)),key=lambda x:x.area);holes=sum(Polygon(r).area for r in domain.interiors);assert holes<1e-7;domain=Polygon(domain.exterior.coords);numeric_front_sliver=domain.difference(box(-10,-20,10,-.41)).area;assert numeric_front_sliver<2e-6;domain=domain.intersection(box(-10,-20,10,-.41));reference=Projected(tris,sg)
 rear=-.66;front=-.41;uvold=np.c_[sg*tris[:,:,0].ravel(),tris[:,:,2].ravel()];edge=uvold[(abs(uvold[:,1]-rear)<1e-7)|(abs(uvold[:,1]-front)<1e-7)];xs=np.unique(np.round(edge[:,0],7));xs=xs[(xs>=1.03)&(xs<=1.87)];xs=np.unique(np.r_[1.03,xs,1.87]);h0=np.array([reference.lower([x,rear],nearest=True) for x in xs]);h1=np.array([reference.lower([x,front],nearest=True) for x in xs])
 # Remove only redundant collinear stations; keep all real section corners.
 while len(xs)>2:
  t=(xs[1:-1]-xs[:-2])/(xs[2:]-xs[:-2]);err=np.maximum(abs(h0[1:-1]-((1-t)*h0[:-2]+t*h0[2:])),abs(h1[1:-1]-((1-t)*h1[:-2]+t*h1[2:])));eligible=np.where(err<1e-7)[0]
  if not len(eligible):break
  i=int(eligible[0]+1);xs=np.delete(xs,i);h0=np.delete(h0,i);h1=np.delete(h1,i)
 band=box(1.03,rear,1.87,front);groups=collections.defaultdict(list)
 for poly,(q,c) in zip(polys,old):groups[c].append(poly)
 paint=[(shapely.union_all(reg,grid_size=1e-7).intersection(domain),c) for c,reg in sorted(groups.items())];ptree=STRtree([q for q,c in paint])
 lines=[domain.boundary,band.boundary]+[q.boundary for q,c in paint]
 # The geometry outside the confirmed front band remains exactly on its old triangles.
 for poly in polys:
  q=poly.difference(band)
  if not q.is_empty:lines.append(q.boundary)
 for a,b in zip(xs,xs[1:]):lines.extend([LineString([(a,rear),(a,front)]),LineString([(a,rear),(b,front)])])
 uv,faces=graph_mesh(lines,domain);colors=[]
 for pt in uv[faces].mean(1):
  hits=ptree.query(Point(*pt),predicate='intersects');colors.append(paint[int(hits[0] if len(hits) else ptree.nearest(Point(*pt)))][1])
 class Field:
  def __init__(self):self.sg=sg
  def height(self,points):
   result=np.array([reference.lower(q,nearest=True) for q in points]);inside=(points[:,0]>=1.03)&(points[:,0]<=1.87)&(points[:,1]>=rear)&(points[:,1]<=front);q=points[inside];ix=np.clip(np.searchsorted(xs,q[:,0],side='right')-1,0,len(xs)-2);a=(q[:,0]-xs[ix])/(xs[ix+1]-xs[ix]);b=(q[:,1]-rear)/(front-rear)
   result[inside]=np.where(a>=b,h0[ix]+(h0[ix+1]-h0[ix])*a+(h1[ix+1]-h0[ix+1])*b,h0[ix]+(h1[ix+1]-h1[ix])*a+(h1[ix]-h0[ix])*b)
   return result
 field=Field();height=field.height(uv);oldheight=np.array([reference.lower(q,nearest=True) for q in uv]);inside=(uv[:,0]>=1.03)&(uv[:,0]<=1.87)&(uv[:,1]>=rear)&(uv[:,1]<=front);outside_error=float(max(abs(height[~inside]-oldheight[~inside]),default=0));boundary=(abs(uv[:,1]-rear)<1e-8)|(abs(uv[:,1]-front)<1e-8);boundary_error=float(max(abs(height[boundary]-oldheight[boundary]),default=0));assert outside_error<1e-8 and boundary_error<2e-6,(name,outside_error,boundary_error)
 used=np.unique(faces);remap=np.full(len(uv),-1);remap[used]=np.arange(len(used));uv=uv[used];faces=remap[faces];part={'uv':uv,'faces':faces.tolist(),'colors':colors,'domain':domain,'paint_missing_m2':0,'discarded_disconnected_outline_areas_m2':[]};m,meta=make_panel(part,field,n,.008)
 # Retreat the internal front rim behind the measured stationary joint.
 # Keep X and the existing 8-mm Y thickness; a normal offset folds the
 # very sharp sidewall and was rejected by the self-intersection check.
 half=len(m.v)//2;vv=np.array(m.v);R,T=world(n);q=vv[:half]@R.T+T;w=np.clip((q[:,2]-rear)/(front-rear),0,1);w=w*w*(3-2*w);retreat=np.c_[np.zeros(half),np.zeros(half),-.008*w]@R;vv[half:]+=retreat;m.v=list(map(tuple,vv))
 p[dnm.fil(n)]=m.srf()
 samples=np.unique(uvold.round(7),axis=0);sample_error=field.height(samples)-np.array([reference.lower(q,nearest=True) for q in samples])
 meta.update(front_band_abs_xz_m=[1.03,1.87,rear,front],outside_band_height_error_m=outside_error,mating_sections_height_error_m=boundary_error,max_local_height_correction_m=float(max(abs(sample_error))),x_stations=xs.tolist(),z_stations=[rear,front],numeric_front_sliver_removed_m2=numeric_front_sliver,internal_rim_retreat_z_m=.008,method='planar interpolation between unchanged rear and forward mating profiles; no extrapolated/narrow blend rim')
 print(name,'triangles',len(faces),'stations',len(xs),'max correction',meta['max_local_height_correction_m'],'edge error',boundary_error,flush=True);return meta

def well_roofs(p,lu,side):
 n=lu['GearWell_'+side];m=dnm.mesh(p[dnm.fil(n)]);R,t=world(n);v=np.array(m.v)@R.T+t;out=[]
 for ids,c,b in m.f:
  for j in range(1,len(ids)-1):
   q=v[[ids[0],ids[j],ids[j+1]]];normal=np.cross(q[1]-q[0],q[2]-q[0]);length=np.linalg.norm(normal)
   if length>1e-12 and abs(normal[1])>.6*length and q[:,1].min()>0:out.append(q)
 assert out
 return np.array(out)
def run(base,out):
 assert sha(base.read_bytes())==BASE
 p,ns=dnm.read(base);old={k:list(v) for k,v in p.items()};lu={dnm.name(n):n for n in ns};audit={'baseline_sha256':BASE,'panels':{}}
 for name in NAMES:audit['panels'][name]=build_panel(p,lu,name)
 roofs={side:well_roofs(p,lu,side) for side in ['Left','Right']};audit['internal_body_cut']=cut(p,lu,roofs,dnm,world)
 out.parent.mkdir(parents=True,exist_ok=True);dnm.write(out,p,ns);out.write_bytes(out.read_bytes().replace(b'\r\n',b'\n'));audit.update(model_sha256=sha(out.read_bytes()),changed_packs=[k for k in p if p[k]!=old[k]],all_node_records_exact=True)
 assert set(audit['changed_packs'])=={n+'.srf' for n in NAMES}|{'Fuselage_0_4.srf'}
 out.with_suffix('.audit.json').write_text(json.dumps(audit,indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();run(a.baseline,a.output)
