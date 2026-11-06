from pathlib import Path
import sys,json,hashlib,collections,numpy as np
from shapely.geometry import Polygon,Point
from shapely.strtree import STRtree
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import *
from topology import panel
import shapely
from source_surface import parts, envelope
def prepare(surface,name):
 max_correction=0
 if name.startswith("MainWheelBayShutter"):
  heights={}
  for q,c in surface:
   for a in q:
    k=tuple(np.round(a[[0,2]],5));heights[k]=min(heights.get(k,float("inf")),float(a[1]))
  fixed=[]
  for q,c in surface:
   t=q.copy()
   for j,a in enumerate(q):
    k=tuple(np.round(a[[0,2]],5));t[j,1]=heights[k];max_correction=max(max_correction,float(abs(t[j,1]-a[1])))
   fixed.append((t,c))
  surface=fixed
 domains=envelope(surface);domain=shapely.union_all([q for q,a,c in domains]);outline=domain.buffer(-.002,join_style=2) if name.startswith("MainWheelBayShutter") else domain
 out=[]
 for poly,a,c in domains:
  for cut in parts(poly.intersection(outline)):
   for t in shapely.get_parts(shapely.constrained_delaunay_triangles(cut)):
    xy=np.array(t.exterior.coords)[:3];q=np.c_[xy[:,0],np.c_[xy,np.ones(3)]@a,xy[:,1]]
    if np.cross(q[1]-q[0],q[2]-q[0])[1]>0:q=q[::-1]
    if abs(np.cross(q[1]-q[0],q[2]-q[0])[1])>1e-10:out.append((np.round(q,6),c))
 return out,{"shared_xz_max_correction_m":max_correction,"seam_inset_m":.002 if name.startswith("MainWheelBayShutter") else 0,"no_new_projected_surface":True}
p,ns=dnm.read(r/'baseline/su30sm.dnm');old={k:list(v) for k,v in p.items()};lu={dnm.name(n):n for n in ns};audit={}
PAINT={(142,169,181),(77,139,163),(118,166,185),(147,163,172)}
def triangles(name,paint=False):
 n=lu[name];m=dnm.mesh(p[dnm.fil(n)]);R,t=transform(n,0);P=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);v=np.array(m.v)@R.T+t+P;out=[]
 for fi,(ids,c,b) in enumerate(m.f):
  if paint and c not in PAINT:continue
  for j in range(1,len(ids)-1):
   q=v[[ids[0],ids[j],ids[j+1]]]
   if np.cross(q[1]-q[0],q[2]-q[0])[1]<-1e-10:out.append((q,c))
 return out
names=[s for s in lu if s.startswith(('MainBayFixedSkin_','MainWheelBayShutter_','GearDoor_'))]
for name in names:
 n=lu[name];R,t=transform(n,0);P=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);surface=triangles(name,True);assert surface
 surface,detail=prepare(surface,name);m,meta=panel(surface,R,t+P);meta.update(detail);p[dnm.fil(n)]=m.srf();audit[name]=meta
# Measured closed lower envelope. Internal cream lining must not protrude beyond it.
supportnames=[s for s in lu if s.startswith(('MainBayFixedSkin','MainWheelBayShutter','GearDoor','BayCornerSkin')) or s in ['Fuselage_0_4','Fuselage_0_5']]
support=np.array([q for s in supportnames for q,c in triangles(s,True)]);polys=[Polygon(q[:,[0,2]]) for q in support];tree=STRtree(polys);coeff=np.array([np.linalg.solve(np.c_[q[:,[0,2]],np.ones(3)],q[:,1]) for q in support]);cache={}
def floor(x,z):
 key=(round(float(x),7),round(float(z),7))
 if key not in cache:
  ids=tree.query(Point(x,z),predicate='intersects');cache[key]=None if not len(ids) else float((coeff[ids]@np.array([x,z,1])).min())
 return cache[key]
def signed(q):
 h=floor(q[0],q[2]);return 1. if h is None else float(q[1]-h-.010)
def clip(q,ds):
 out=[]
 for i,j in [(0,1),(1,2),(2,0)]:
  a,b=q[i],q[j];da,db=ds[i],ds[j]
  if da>=0:out.append(a)
  if (da>=0)!=(db>=0):out.append(a+(b-a)*da/(da-db))
 return out
for name in ['GearWell_Left','GearWell_Right','GearWell_Nose']:
 n=lu[name];m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v);out=Mesh();affected=0;removed=0;minimum=0
 for ids,c,b in m.f:
  for k in range(1,len(ids)-1):
   q=v[[ids[0],ids[k],ids[k+1]]];ds=np.array([signed(a) for a in q]);minimum=min(minimum,float(ds.min()))
   if ds.min()>=-1e-7:out.face(q,c,b);continue
   # Subdivide only a confirmed boundary crossing; keep unchanged interior faces verbatim.
   affected+=1;todo=[q]
   while todo:
    t=todo.pop();d=np.array([signed(a) for a in t]);probes=np.array([signed((t[j]+t[(j+1)%3])/2) for j in range(3)]+[signed(t.mean(0))])
    if d.min()>=0 and probes.min()>=0:out.face(t,c,b);continue
    if d.max()<0 and probes.max()<0:removed+=1;continue
    lens=np.linalg.norm(np.roll(t,-1,axis=0)-t,axis=1);j=int(lens.argmax())
    if lens[j]>.025:
     a,jj,kk=j,(j+1)%3,(j+2)%3;mid=(t[a]+t[jj])/2;todo.extend([np.array([t[a],mid,t[kk]]),np.array([mid,t[jj],t[kk]])]);continue
    poly=clip(t,d)
    if len(poly)<3:removed+=1;continue
    for j in range(1,len(poly)-1):
     tri=np.round(np.array([poly[0],poly[j],poly[j+1]]),6)
     if np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))>1e-11:out.face(tri,c,b)
 rounded=np.round(np.array(out.v),6);out.f=[(ids,c,b) for ids,c,b in out.f if np.linalg.norm(np.cross(rounded[ids[1]]-rounded[ids[0]],rounded[ids[2]]-rounded[ids[0]]))>1e-12]
 p[dnm.fil(n)]=out.srf() if affected else old[dnm.fil(n)];audit[name]={'boundary_faces_clipped':affected,'outside_subtriangles_removed':removed,'worst_old_below_clearance_m':minimum,'new_clearance_m':.010,'interior_colors_preserved':True}
changed=[k for k in p if p[k]!=old[k]];assert all(k.removesuffix('.srf') in names+['GearWell_Left','GearWell_Right','GearWell_Nose'] for k in changed)
assert p['IntakeDuct_-1.srf']==old['IntakeDuct_-1.srf'] and p['IntakeDuct_1.srf']==old['IntakeDuct_1.srf']
output=r/'runtime/aircraft/su30sm.dnm';dnm.write(output,p,ns);audit['changed_packs']=changed;audit['all_nodes_states_parents_exact']=True;audit['model_sha256']=hashlib.sha256(output.read_bytes()).hexdigest();(r/'repair-audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps({k:({j:v for j,v in a.items() if j!='boundary_segments'} if isinstance(a,dict) else a) for k,a in audit.items()},indent=2))
