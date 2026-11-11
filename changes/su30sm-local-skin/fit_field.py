"""A shared curved reference fitted under explicit, unchanged geometry constraints."""
from pathlib import Path
import sys,collections,json
import numpy as np
from scipy.interpolate import BSpline,LinearNDInterpolator
from scipy import sparse
from shapely.geometry import Polygon,Point,box
from shapely.strtree import STRtree
import shapely,osqp
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'model-source'))
from common import dnm,transform
PAINT={(142,169,181),(77,139,163),(118,166,185),(147,163,172)}
NAMES=['MainBayFixedSkin_Left','MainBayFixedSkin_Right','MainWheelBayShutter_Left','MainWheelBayShutter_Right']
def world(n):
 R,t=transform(n,0);return R,t+np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float)
def exterior(lines,n):
 m=dnm.mesh(lines);R,t=world(n);v=np.array(m.v)@R.T+t;out=[]
 for ids,c,b in m.f:
  if c not in PAINT:continue
  for j in range(1,len(ids)-1):
   q=v[[ids[0],ids[j],ids[j+1]]]
   if np.cross(q[1]-q[0],q[2]-q[0])[1]<-1e-10:out.append((q,c))
 return out
def smooth(v):
 v=np.clip(v,0,1);return v*v*(3-2*v)
def blend(uv):
 x,z=uv.T
 return np.minimum.reduce([smooth((x-1.03)/.03),smooth((1.85-x)/.06),smooth((z+3.38)/.04),smooth((-.41-z)/.04)])
class Projected:
 def __init__(self,tris,sg):
  self.polys=[];self.co=[]
  for q in tris:
   xy=np.c_[sg*q[:,0],q[:,2]];poly=Polygon(xy)
   if poly.area<1e-12:continue
   self.polys.append(poly);self.co.append(np.linalg.solve(np.c_[xy,np.ones(3)],q[:,1]))
  self.co=np.array(self.co);self.tree=STRtree(self.polys);self.cache={}
 def heights(self,uv):
  ids=self.tree.query(Point(*uv).buffer(1e-8),predicate='intersects')
  return self.co[ids]@np.r_[uv,1]
 def lower(self,uv,nearest=False):
  key=tuple(np.round(uv,8))
  if key not in self.cache:
   values=self.heights(uv)
   if not len(values):
    if not nearest:self.cache[key]=np.nan;return np.nan
    i=int(self.tree.nearest(Point(*uv)));assert self.polys[i].distance(Point(*uv))<.006;values=[self.co[i]@np.r_[uv,1]]
   self.cache[key]=float(min(values))
  return self.cache[key]
class Field:
 def __init__(self,p,ns,sg):
  self.sg=sg;self.lu={dnm.name(n):n for n in ns};self.p=p
  old=[q for name in NAMES if name.endswith('Left' if sg<0 else 'Right') for q,c in exterior(p[dnm.fil(self.lu[name])],self.lu[name])]
  self.old=Projected(old,sg)
  raw=dnm.mesh((ROOT/'source-data/original-hull.srf').read_text().splitlines());self.original=Projected([np.array([raw.v[i] for i in ids]) for ids,c,b in raw.f if np.mean([raw.v[i][0] for i in ids])*sg>0],sg)
  rp,rn=dnm.read(ROOT/'source-data/curved-shutters.dnm');ref=next(n for n in rn if dnm.name(n).endswith('Left' if sg<0 else 'Right'));rv=np.concatenate([q for q,c in exterior(rp[dnm.fil(ref)],ref)]);uv,inv=np.unique(np.round(np.c_[sg*rv[:,0],rv[:,2]],6),axis=0,return_inverse=True);yy=np.full(len(uv),np.inf);np.minimum.at(yy,inv,rv[:,1]);self.ref=LinearNDInterpolator(uv,yy)
  self.tx=np.r_[[1.03]*4,np.linspace(1.03,1.87,16)[1:-1],[1.87]*4];self.tz=np.r_[[-3.38]*4,np.linspace(-3.38,-.41,24)[1:-1],[-.41]*4];self.nx=len(self.tx)-4;self.nz=len(self.tz)-4;self.nc=self.nx*self.nz
  xx,zz=np.meshgrid(np.linspace(1.03,1.87,55),np.linspace(-3.38,-.41,120),indexing='ij');self.samples=np.c_[xx.ravel(),zz.ravel()];target=[]
  for u,z in self.samples:
   y=float(self.ref([[u,z]])[0]) if -1.858<=z<=-.662 else np.nan
   if not np.isfinite(y):y=self.original.lower([u,z],nearest=True)
   target.append(y)
  self.target=np.array(target);A=self.design(self.samples);dx=sparse.kron(sparse.diags([1.,-2.,1.],[0,1,2],shape=(self.nx-2,self.nx)),sparse.eye(self.nz),format='csc');dz=sparse.kron(sparse.eye(self.nx),sparse.diags([1.,-2.,1.],[0,1,2],shape=(self.nz-2,self.nz)),format='csc');self.P=(2*(A.T@A+.8*(dx.T@dx)+2*(dz.T@dz)+1e-7*sparse.eye(self.nc))).tocsc();self.q=-2*np.asarray(A.T@self.target).ravel()
  # Static root geometry is an obstacle, not an input height layer to stitch.
  body=[];self.body_domains=[];groups=collections.defaultdict(list);region=box(1.03,-3.38,1.87,-.41)
  for name,n in self.lu.items():
   if not name.startswith(('Fuselage_','GearWell_','IntakeDuct_','BayCornerSkin_','DoorSeat_','GearBay')):continue
   m=dnm.mesh(p[dnm.fil(n)]);R,t=world(n);v=np.array(m.v)@R.T+t if m.v else np.empty((0,3))
   for ids,c,b in m.f:
    for j in range(1,len(ids)-1):
     q=v[[ids[0],ids[j],ids[j+1]]]
     if (sg*q[:,0]).max()<1.03 or (sg*q[:,0]).min()>1.87 or q[:,2].max()<-3.38 or q[:,2].min()>-.41:continue
     xy=np.c_[sg*q[:,0],q[:,2]];poly=Polygon(xy)
     if poly.area<1e-9:continue
     cut=poly.intersection(region)
     if cut.area<1e-10:continue
     coef=np.linalg.solve(np.c_[xy,np.ones(3)],q[:,1]);body.append(q);groups[tuple(np.round(coef,4))].append(cut)
  self.body=Projected(body,sg)
  for polys in groups.values():
   for poly in shapely.get_parts(shapely.union_all(polys,grid_size=1e-6)):
    if poly.geom_type=='Polygon' and poly.area>1e-10:self.body_domains.append(poly)
  self.constraint_points=np.array([uv for poly in self.body_domains for uv in list(poly.exterior.coords)[:-1]+list(poly.representative_point().coords)])
  self.coeff=None;self.audit={};print('reference',sg,'constraints surface pieces',len(body),'merged plane regions',len(self.body_domains),flush=True)
 def design(self,uv):
  uv=np.asarray(uv);x=np.clip(uv[:,0],1.03,1.87);z=np.clip(uv[:,1],-3.38,-.41);bx=BSpline.design_matrix(x,self.tx,3).tocsr();bz=BSpline.design_matrix(z,self.tz,3).tocsr();rows=[];cols=[];values=[]
  for r in range(len(x)):
   ix=bx.indices[bx.indptr[r]:bx.indptr[r+1]];iz=bz.indices[bz.indptr[r]:bz.indptr[r+1]];a=bx.data[bx.indptr[r]:bx.indptr[r+1]];b=bz.data[bz.indptr[r]:bz.indptr[r+1]];cols.extend((ix[:,None]*self.nz+iz[None,:]).ravel());values.extend((a[:,None]*b[None,:]).ravel());rows.extend([r]*(len(ix)*len(iz)))
  return sparse.csc_matrix((values,(rows,cols)),shape=(len(x),self.nc))
 def fit(self,vertices):
  uv=np.unique(np.round(np.vstack([self.samples,vertices,self.constraint_points]),7),axis=0);uv=uv[(uv[:,0]>=1.03)&(uv[:,0]<=1.87)&(uv[:,1]>=-3.38)&(uv[:,1]<=-.41)];uv=uv[blend(uv)>.005];lower=[];upper=[];points=[];legacy_conflicts=0;relaxed_clearances=0
  for point in uv:
   h0=self.old.lower(point,nearest=True);body=self.body.heights(point)
   if not len(body):continue
   u,z=point;thick=.001 if 1.052<=u<=1.87 and -1.858<=z<=-.662 else .008
   above=body[body>=h0-.002];below=body[body<h0-.002];lo=float(max(below)+.002) if len(below) else -np.inf;hi=float(min(above)-thick-.002) if len(above) else np.inf
   if hi<lo and hi-lo>-.002:lo=hi=(hi+lo)/2;relaxed_clearances+=1
   if hi<lo:legacy_conflicts+=1;continue # Existing interpenetrating protected layers: inspected by motion checks.
   lower.append(lo);upper.append(hi);points.append(point)
  G=self.design(np.array(points));C=sparse.vstack([G,sparse.eye(self.nc)],format='csc');l=np.r_[lower,[-1.30]*self.nc];u=np.r_[upper,[.15]*self.nc];solver=osqp.OSQP();solver.setup(P=self.P,q=self.q,A=C,l=l,u=u,eps_abs=1e-8,eps_rel=1e-8,max_iter=100000,polishing=True,verbose=False,adaptive_rho_interval=100);res=solver.solve();assert res.info.status_val in [1,2],res.info.status
  self.coeff=res.x;value=C@self.coeff;violation=float(max(np.maximum(l-value,0).max(),np.maximum(value-u,0).max()));assert violation<2e-6,violation
  residual=self.design(self.samples)@self.coeff-self.target;self.audit={'status':res.info.status,'obstacle_rows':len(points),'legacy_conflicting_obstacle_samples_skipped':legacy_conflicts,'relaxed_existing_clearance_samples':relaxed_clearances,'max_constraint_violation_m':violation,'reference_rms_error_m':float(np.sqrt(np.mean(residual**2))),'reference_max_error_m':float(max(abs(residual))),'spline_coefficients':self.coeff.tolist(),'x_knots':self.tx.tolist(),'z_knots':self.tz.tolist()};print('fitted',self.sg,'RMS',self.audit['reference_rms_error_m'],'max',self.audit['reference_max_error_m'],'constraint',violation,flush=True)
 def height(self,uv):
  uv=np.asarray(uv);b=blend(uv);h=self.design(uv)@self.coeff;ids=np.where(b<1-1e-10)[0]
  for i in ids:h[i]=b[i]*h[i]+(1-b[i])*self.old.lower(uv[i],nearest=True)
  return np.asarray(h)
