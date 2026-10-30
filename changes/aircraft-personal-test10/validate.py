"""Check compiled runtime coefficients against actual moving exit geometry."""
from pathlib import Path
import sys,subprocess,json,math,tempfile
import numpy as np
from shapely.geometry import Polygon,Point
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
def pose(n,u):
 ss=[s for s in n if s.startswith('STA ')];step=u*(len(ss)-1);i=min(len(ss)-2,int(step));f=step-i;A,t=transform(n,i);B,v=transform(n,i+1);forward=A[:,2]*(1-f)+B[:,2]*f;forward/=np.linalg.norm(forward);up=A[:,1]*(1-f)+B[:,1]*f;side=np.cross(up,forward);side/=np.linalg.norm(side);up=np.cross(forward,side);pos=np.array(next(s.split()[1:4] for s in n if s.startswith('POS ')),float);return np.c_[side,up,forward],t*(1-f)+v*f+pos
program='''#include <cstdio>\n#include "fsexhaustprofile.h"\nint main(){for(int a=0;a<5;++a)for(int e=0;e<2;++e)for(int n=0;n<=200;++n){double u=n/200.;auto p=FsExhaustProfile::Get(a,e,u);printf("%d %d %.17g %.17g %.17g %.17g %.17g %.17g\\n",a,e,u,p.sx,p.sy,p.dx,p.dy,p.dz);}}'''
with tempfile.TemporaryDirectory() as t:
 t=Path(t);(t/'test.cpp').write_text(program);subprocess.run(['g++','-std=c++11','-I',str(r),str(t/'test.cpp'),'-o',str(t/'test')],check=True);rows=np.array([list(map(float,line.split())) for line in subprocess.check_output([str(t/'test')],text=True).splitlines()])
metadata=json.loads((r/'exhaust-profiles.json').read_text());result={};worst=0.;minimum_margin=100.
for ai,kind in enumerate(['su27','mig29','su34','su47','su57']):
 old,old_nodes=dnm.read(r/'baseline'/f'{kind}.dnm');p,ns=dnm.read(r/'runtime/aircraft'/f'{kind}.dnm');assert ns==old_nodes,'Node/animation regression '+kind;lu={dnm.name(n):n for n in ns};plume_files={dnm.fil(lu[m['node']]) for m in metadata[kind]}
 assert all(old[name]==data for name,data in p.items() if name not in plume_files),'Unrelated surface changed '+kind
 per=[]
 for engine in [0,1]:
  meta=metadata[kind][engine];candidate=[];allpoints=[]
  for name in meta['petal_nodes']:
   n=lu[name];v=np.unique(np.array(dnm.mesh(p[dnm.fil(n)]).v),axis=0);v=v[v[:,2]<v[:,2].min()+.00001];R,t=pose(n,1);q=v@R.T+t;candidate.append((n,v,q));allpoints.extend(q)
  q=np.array(allpoints);center=(q[:,:2].min(0)+q[:,:2].max(0))/2;rad=(q[:,:2].max(0)-q[:,:2].min(0))/2;selected=[]
  for n,v,q in candidate:selected.append((n,v[np.argsort(np.linalg.norm((q[:,:2]-center)/rad,axis=1))[:2]]))
  mesh=dnm.mesh(p[dnm.fil(lu[meta['node']])]);v=np.array(mesh.v);lo,hi=v.min(0),v.max(0);center=(lo[:2]+hi[:2])/2;radius=(hi[:2]-lo[:2])/2;mouth=np.unique(v[v[:,2]>hi[2]-.000001],axis=0);maxerr=0.;margin=100.;xscales=[]
  for row in rows[(rows[:,0]==ai)&(rows[:,1]==engine)]:
   u,sx,sy,dx,dy,dz=row[2:];lip=[]
   for n,points in selected:R,t=pose(n,u);lip.extend(points@R.T+t)
   lip=np.array(lip);c=(lip[:,:2].min(0)+lip[:,:2].max(0))/2;order=np.argsort(np.arctan2(lip[:,1]-c[1],lip[:,0]-c[0]));boundary=Polygon(lip[order,:2]).buffer(0)
   jet=mouth.copy();jet[:,:2]=(jet[:,:2]-center)*[sx,sy]+center+[dx*radius[0],dy*radius[1]];jet[:,2]+=dz*radius[0]
   assert all(boundary.contains(Point(q)) for q in jet[:,:2]),(kind,engine,u,'jet outside aperture')
   err=abs(jet[:,2].max()-(lip[:,2].max()+.010));maxerr=max(maxerr,float(err));xscales.append(float(sx))
   margin=min(margin,min(boundary.boundary.distance(Point(q)) for q in jet[:,:2]))
  assert maxerr<.0005,(kind,engine,'lip detachment',maxerr)
  assert max(xscales)-min(xscales)>.20,(kind,engine,'constant plume')
  worst=max(worst,maxerr);minimum_margin=min(minimum_margin,margin);per.append({'engine':engine,'positions_checked':201,'max_mouth_alignment_error_m':maxerr,'minimum_lip_clearance_m':margin,'scale_min':min(xscales),'scale_max':max(xscales)})
 result[kind]={'all_non_plume_surfaces_and_all_animation_nodes_unchanged':True,'engines':per}
output={'passed':True,'actual_compiled_cpp_coefficients_used':True,'aircraft':result,'maximum_alignment_error_m':worst,'minimum_clearance_m':minimum_margin,'physical_scope':'visual shape coupling, not CFD'};(r/'geometry-checks.json').write_text(json.dumps(output,indent=2));print('PASS five aircraft / ten nozzles / 201 positions each; max mouth error',worst,'minimum clearance',minimum_margin)
