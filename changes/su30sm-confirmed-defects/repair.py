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
from front_profile import extract as extract_front,inboard_floor
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
def build_panel(p,lu,name,profile):
 n=lu[name];sg=-1 if name.endswith('Left') else 1;old=exterior(p[dnm.fil(n)],n);tris=np.array([q for q,c in old]);polys=[Polygon(np.c_[sg*q[:,0],q[:,2]]) for q,c in old];domain=max(parts(shapely.union_all(polys,grid_size=1e-7)),key=lambda x:x.area);holes=sum(Polygon(r).area for r in domain.interiors);assert holes<1e-7;domain=Polygon(domain.exterior.coords);numeric_front_sliver=domain.difference(box(-10,-20,10,-.41)).area;assert numeric_front_sliver<2e-6;domain=domain.intersection(box(-10,-20,10,-.41));front_notches=box(1.03,-.66,1.87,-.41).difference(domain).area;assert front_notches<1e-6,(name,front_notches);domain=domain.union(box(1.03,-.66,1.87,-.41));reference=Projected(tris,sg)
 rear=-.66;front=-.41;uvold=np.c_[sg*tris[:,:,0].ravel(),tris[:,:,2].ravel()];edge=uvold[(abs(uvold[:,1]-rear)<1e-7)|(abs(uvold[:,1]-front)<1e-7)];xs=np.unique(np.round(edge[:,0],7));xs=xs[(xs>=1.03)&(xs<=1.87)];xs=np.unique(np.r_[1.03,xs,1.87]);h0=np.array([reference.lower([x,rear],nearest=True) for x in xs]);h1=np.array([reference.lower([x,front],nearest=True) for x in xs])
 # Arc length retains the measured overhang instead of collapsing multiple
 # heights onto one X. Both end profiles are immutable spatial curves.
 rear_curve=np.c_[xs,h0]
 def arc(q):return np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
 rear_arc=arc(rear_curve);rear_arc/=rear_arc[-1];front_curve=profile['outside'];inside_curve=profile['inside'];front_arc=arc(front_curve);front_arc/=front_arc[-1];assert len(inside_curve)==len(front_curve),'Offset correspondence changed';inside_arc=front_arc.copy()
 knot_u=np.unique(np.r_[rear_arc,front_arc,inside_arc]);xs=np.interp(knot_u,rear_arc,rear_curve[:,0]);rxy=np.c_[xs,np.interp(xs,rear_curve[:,0],rear_curve[:,1])];fxy=np.c_[np.interp(knot_u,front_arc,front_curve[:,0]),np.interp(knot_u,front_arc,front_curve[:,1])];ixy=np.c_[np.interp(knot_u,inside_arc,inside_curve[:,0]),np.interp(knot_u,inside_arc,inside_curve[:,1])]
 band=box(1.03,rear,1.87,front);side_rear=-1.86;side_front=-.66;side_band=box(1.03,side_rear,1.05,side_front);body_z,body_y=inboard_floor(p,lu,dnm,world,sg,side_rear,side_front);numeric_side_sliver=domain.intersection(box(-10,side_rear,1.03,side_front)).area;assert numeric_side_sliver<1e-4 and domain.bounds[0]>=1.02975,(name,numeric_side_sliver,domain.bounds[0]);domain=domain.difference(box(-10,side_rear,1.03,side_front)).union(side_band);side_z=set(np.r_[body_z,side_rear,side_front].tolist())
 for q in tris:
  uvq=np.c_[sg*q[:,0],q[:,2]]
  for a,b in zip(uvq,np.roll(uvq,-1,axis=0)):
   if abs(b[0]-a[0])>1e-12:
    t=(1.05-a[0])/(b[0]-a[0])
    if 0<=t<=1:
     z=a[1]+t*(b[1]-a[1])
     if side_rear<z<side_front:side_z.add(float(z))
 side_z=np.unique(np.round(sorted(side_z),7));groups=collections.defaultdict(list)
 for poly,(q,c) in zip(polys,old):groups[c].append(poly)
 paint=[(shapely.union_all(reg,grid_size=1e-7).intersection(domain),c) for c,reg in sorted(groups.items())];ptree=STRtree([q for q,c in paint])
 lines=[domain.boundary,band.boundary,side_band.boundary]+[q.boundary for q,c in paint]
 # The geometry outside the confirmed front band remains exactly on its old triangles.
 for poly in polys:
  q=poly.difference(band)
  if not q.is_empty:lines.append(q.boundary)
 for a,b in zip(xs,xs[1:]):lines.extend([LineString([(a,rear),(a,front)]),LineString([(a,rear),(b,front)])])
 for a,b in zip(side_z,side_z[1:]):lines.extend([LineString([(1.03,a),(1.05,a)]),LineString([(1.03,a),(1.05,b)])])
 uv,faces=graph_mesh(lines,domain);colors=[]
 for pt in uv[faces].mean(1):
  hits=ptree.query(Point(*pt),predicate='intersects');colors.append(paint[int(hits[0] if len(hits) else ptree.nearest(Point(*pt)))][1])
 class Field:
  def __init__(self):
   self.sg=sg;y=np.interp(side_z,body_z,body_y);oldA=self._base(np.c_[np.full(len(side_z),1.03),side_z])[:,1];end_error=oldA[[0,-1]]-y[[0,-1]];print(name,'inboard endpoint errors',end_error,flush=True);assert max(abs(end_error))<5e-5;self.D=y-oldA+np.interp(side_z,[side_rear,side_front],end_error)
  def _base(self,points,inside=False):
   hh=np.array([reference.lower(q,nearest=True) for q in points]);result=np.c_[sg*points[:,0],hh+(.008 if inside else 0),points[:,1]];mask=(points[:,0]>=1.03-1e-8)&(points[:,0]<=1.87+1e-8)&(points[:,1]>=rear-1e-9)&(points[:,1]<=front+1e-9);q=points[mask];ix=np.clip(np.searchsorted(xs,q[:,0],side='right')-1,0,len(xs)-2);a=(q[:,0]-xs[ix])/(xs[ix+1]-xs[ix]);b=(q[:,1]-rear)/(front-rear);A=np.c_[rxy,np.full(len(xs),rear)];B=np.c_[ixy if inside else fxy,np.full(len(xs),front)]
   if inside:A[:,1]+=.008
   mapped=np.where((a>=b)[:,None],A[ix]+(A[ix+1]-A[ix])*a[:,None]+(B[ix+1]-A[ix+1])*b[:,None],A[ix]+(B[ix+1]-B[ix])*a[:,None]+(B[ix]-A[ix])*b[:,None]);mapped[:,0]*=sg;result[mask]=mapped;return result
  def positions(self,points,inside=False):
   result=self._base(points,inside);mask=(points[:,0]>=1.03-1e-9)&(points[:,0]<=1.05+1e-9)&(points[:,1]>=side_rear-1e-9)&(points[:,1]<=side_front+1e-9);q=points[mask];iz=np.clip(np.searchsorted(side_z,q[:,1],side='right')-1,0,len(side_z)-2);a=(q[:,0]-1.03)/.02;b=(q[:,1]-side_z[iz])/(side_z[iz+1]-side_z[iz]);d=np.where(a>=b,self.D[iz]*(1-a),self.D[iz]-self.D[iz+1]*a+(self.D[iz+1]-self.D[iz])*b);result[mask,1]+=d;return result
  def height(self,points):return self.positions(points)[:,1]
 field=Field();height=field.height(uv);oldheight=np.array([reference.lower(q,nearest=True) for q in uv]);mask=((uv[:,0]>=1.03)&(uv[:,0]<=1.87)&(uv[:,1]>=rear)&(uv[:,1]<=front))|((uv[:,0]>=1.03)&(uv[:,0]<=1.05)&(uv[:,1]>=side_rear)&(uv[:,1]<=side_front));outside_error=float(max(abs(height[~mask]-oldheight[~mask]),default=0));frontpoints=field.positions(uv[abs(uv[:,1]-front)<1e-8]);frontpoints[:,0]*=sg;front_curve_error=float(max((LineString(front_curve).distance(Point(*q[:2])) for q in frontpoints),default=0));rearpoints=field.positions(uv[abs(uv[:,1]-rear)<1e-8]);rearpoints[:,0]*=sg;rear_curve_error=float(max((LineString(rear_curve).distance(Point(*q[:2])) for q in rearpoints),default=0));boundary_error=max(front_curve_error,rear_curve_error);assert outside_error<1e-8 and boundary_error<5e-5
 used=np.unique(faces);remap=np.full(len(uv),-1);remap[used]=np.arange(len(used));uv=uv[used];faces=remap[faces];part={'uv':uv,'faces':faces.tolist(),'colors':colors,'domain':domain,'paint_missing_m2':0,'discarded_disconnected_outline_areas_m2':[]};m,meta=make_panel(part,field,n,.008)
 # Map BOTH faces of the shell through the same spatial loft. The inside
 # follows the measured profile's valid offset, not a global Y extrusion.
 half=len(m.v)//2;vv=np.array(m.v);R,T=world(n);q=vv[:half]@R.T+T;params=np.c_[sg*q[:,0],q[:,2]];vv[:half]=(field.positions(params)-T)@R;vv[half:]=(field.positions(params,inside=True)-T)@R;m.v=list(map(tuple,vv))
 # The measured contour is concave. A fan of quadrilateral end faces cuts
 # across its overhang; triangulate the actual closed rim polygon instead.
 caps=[];kept=[]
 for ids,c,b in m.f:
  if c==(105,118,123) and all(abs(params[i%half,1]-front)<1e-8 for i in ids):caps.extend(i for i in ids if i<half)
  else:kept.append((ids,c,b))
 rim=sorted(set(caps),key=lambda i:params[i,0]);worldv=vv@R.T+T;ring=worldv[rim,:2].tolist()+worldv[np.array(rim[::-1])+half,:2].tolist();polygon=Polygon(ring);assert polygon.is_valid,(name,'invalid inward rim')
 ringids=rim+[i+half for i in rim[::-1]];ringxy=worldv[ringids,:2];segments=np.c_[np.arange(len(ringids)),np.roll(np.arange(len(ringids)),-1)];cap=triangle.triangulate({'vertices':ringxy,'segments':segments},'pQ');assert len(cap['vertices'])==len(ringids) and np.max(abs(cap['vertices']-ringxy))<1e-12
 for indices in cap['triangles']:
  ids=[ringids[int(i)] for i in indices];coords=worldv[ids,:2];cross=(coords[1,0]-coords[0,0])*(coords[2,1]-coords[0,1])-(coords[1,1]-coords[0,1])*(coords[2,0]-coords[0,0])
  if cross<0:ids=ids[::-1]
  kept.append((ids,(105,118,123),False))
 m.f=kept
 p[dnm.fil(n)]=m.srf()
 samples=np.unique(uvold.round(7),axis=0);sample_error=field.height(samples)-np.array([reference.lower(q,nearest=True) for q in samples])
 meta.update(front_band_abs_xz_m=[1.03,1.87,rear,front],outside_band_height_error_m=outside_error,mating_sections_curve_error_m=boundary_error,front_section_error_m=front_curve_error,rear_section_error_m=rear_curve_error,source_section_plane_z_m=profile['extraction_z'],source_section_snap_tolerance_m=profile['simplification_tolerance_m'],max_local_height_correction_m=float(max(abs(sample_error))),x_stations=xs.tolist(),z_stations=[rear,front],numeric_front_sliver_removed_m2=numeric_front_sliver,numeric_front_notches_filled_m2=front_notches,inboard_strip_abs_xz_m=[1.03,1.05,side_rear,side_front],numeric_inboard_sliver_removed_m2=numeric_side_sliver,max_inboard_edge_correction_m=float(max(abs(field.D))),internal_rim_retreat_z_m=0,method='spatial loft between unchanged rear profile and actual connected F4 front contour; retain overhang and offset inside profile')
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
 ends={}
 for side,sg in [('Left',-1),('Right',1)]:
  n=lu['MainBayFixedSkin_'+side];ref=Projected(np.array([q for q,c in exterior(p[dnm.fil(n)],n)]),sg);ends[side]=[(sg*x,ref.lower([x,-.41],nearest=True)) for x in [1.03,1.87]]
 profiles=extract_front(p,lu,dnm,world,ends)
 for name in NAMES:audit['panels'][name]=build_panel(p,lu,name,profiles['Left' if name.endswith('Left') else 'Right'])
 roofs={side:well_roofs(p,lu,side) for side in ['Left','Right']};audit['internal_body_cut']=cut(p,lu,roofs,dnm,world)
 out.parent.mkdir(parents=True,exist_ok=True);dnm.write(out,p,ns);out.write_bytes(out.read_bytes().replace(b'\r\n',b'\n'));audit.update(model_sha256=sha(out.read_bytes()),changed_packs=[k for k in p if p[k]!=old[k]],all_node_records_exact=True)
 assert set(audit['changed_packs'])=={n+'.srf' for n in NAMES}|{'Fuselage_0_4.srf'}
 out.with_suffix('.audit.json').write_text(json.dumps(audit,indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();run(a.baseline,a.output)
