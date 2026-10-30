"""Bind each exhaust plume to its actual moving exit lip; keep all other geometry."""
from pathlib import Path
import sys,json,math,hashlib,shutil
import numpy as np
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
(r/'runtime/aircraft').mkdir(parents=True,exist_ok=True)
def pose(n,opening):
 count=len([s for s in n if s.startswith('STA ')]);u=opening*(count-1);i=min(count-2,int(u));f=u-i;R,t=transform(n,i);S,v=transform(n,i+1);z=R[:,2]*(1-f)+S[:,2]*f;z/=np.linalg.norm(z);y=R[:,1]*(1-f)+S[:,1]*f;x=np.cross(y,z);x/=np.linalg.norm(x);y=np.cross(z,x);pos=np.array(next(s.split()[1:4] for s in n if s.startswith('POS ')),float);return np.c_[x,y,z],t*(1-f)+v*f+pos
profiles={};report={}
for kind in ['su27','mig29','su34','su47','su57']:
 p,ns=dnm.read(r/'baseline'/f'{kind}.dnm');lu={dnm.name(n):n for n in ns};groups=[];profiles[kind]=[];report[kind]=[]
 for engine in [0,1]:
  side=['L','R'][engine]
  if kind=='su47':petals=[n for n in ns if dnm.name(n).startswith('NozzlePetal'+side)];plume=lu['Afterburner'+side]
  elif kind=='su57':petals=[n for n in ns if dnm.name(n).startswith('VariableNozzle'+side+'Petal')];plume=lu['Flame_'+side]
  else:petals=[n for n in ns if dnm.name(n).startswith('VariableNozzle'+str(engine)+'Petal')];plume=lu['Afterburner'+str(engine)]
  assert len(petals)>=20
  candidates=[];all_open=[]
  for n in petals:
   v=np.unique(np.array(dnm.mesh(p[dnm.fil(n)]).v),axis=0);v=v[v[:,2]<v[:,2].min()+.00001];R,t=pose(n,1.);q=v@R.T+t;candidates.append((n,v,q));all_open.extend(q)
  q=np.array(all_open);center=(q[:,:2].min(0)+q[:,:2].max(0))/2;rad=(q[:,:2].max(0)-q[:,:2].min(0))/2;lips=[]
  for n,v,q in candidates:
   order=np.argsort(np.linalg.norm((q[:,:2]-center)/rad,axis=1));lips.append((n,v[order[:2]]))
  samples=[]
  for opening in np.linspace(0,1,21):
   points=[]
   for n,v in lips:R,t=pose(n,float(opening));points.extend(v@R.T+t)
   q=np.array(points);c=(q[:,:2].min(0)+q[:,:2].max(0))/2;rr=(q[:,:2].max(0)-q[:,:2].min(0))/2;inset=min(np.linalg.norm((q[:,:2]-c)/rr,axis=1));rr*=inset*.94;samples.append([*c,*rr,float(q[:,2].max()+.010)])
  samples=np.array(samples);ref=samples[-1];m=dnm.mesh(p[dnm.fil(plume)]);v=np.array(m.v);old_center=(v[:,:2].min(0)+v[:,:2].max(0))/2;old_r=(v[:,:2].max(0)-v[:,:2].min(0))/2;old_z=v[:,2].max()
  # Anchor is just inside the physical lip; avoid an axial gap on closure.
  v[:,:2]=(v[:,:2]-old_center)*(ref[2:4]/old_r)+ref[:2];v[:,2]+=ref[4]-old_z;m.v=[tuple(q) for q in v];p[dnm.fil(plume)]=m.srf()
  table=[]
  for c in samples:
   row=np.round([c[2]/ref[2],c[3]/ref[3],(c[0]-ref[0])/ref[2],(c[1]-ref[1])/ref[3],(c[4]-ref[4])/ref[2]],10);row[abs(row)<1e-9]=0.;table.append(row.tolist())
  profiles[kind].append(table);report[kind].append({'engine':engine,'node':dnm.name(plume),'petal_nodes':[dnm.name(n) for n in petals],'physical_exit_profiles':samples.tolist(),'render_profiles':table,'reference_mouth':ref.tolist(),'inset_fraction':.94,'fixed_lip_overlap_m':.010})
 for name in [kind+'.dnm',kind+'_coarse.dnm']:dnm.write(r/'runtime/aircraft'/name,p,ns)
lines=['// Generated from the actual moving inner exit lips. Own exhaust adaptation.','#ifndef FSEXHAUSTPROFILE_IS_INCLUDED','#define FSEXHAUSTPROFILE_IS_INCLUDED','namespace FsExhaustProfile {','struct Sample { double sx,sy,dx,dy,dz; };','static const Sample profile[5][2][21]={']
for k in ['su27','mig29','su34','su47','su57']:
 lines.append('{ // '+k)
 for tab in profiles.get(k,[]):lines.append('{'+','.join('{'+','.join(format(float(v),'.12g') for v in row)+'}' for row in tab)+'},')
 lines.append('},')
lines+=['};','inline Sample Get(int aircraft,int engine,double opening) {',' const double u=(opening<0?0:opening>1?1:opening)*20.;',' const int i=(int(u)<20?int(u):19);const double f=u-i;',' const auto &a=profile[aircraft][engine][i];const auto &b=profile[aircraft][engine][i+1];',' return {a.sx+(b.sx-a.sx)*f,a.sy+(b.sy-a.sy)*f,a.dx+(b.dx-a.dx)*f,a.dy+(b.dy-a.dy)*f,a.dz+(b.dz-a.dz)*f};','}','}','#endif']
# Engine coefficients and mesh geometry are generated together.
(r/'fsexhaustprofile.h').write_text('\n'.join(lines)+'\n');(r/'exhaust-profiles.json').write_text(json.dumps(report,indent=2));(r/'generated-models.json').write_text(json.dumps({name:hashlib.sha256((r/'runtime/aircraft'/name).read_bytes()).hexdigest() for k in profiles for name in [k+'.dnm',k+'_coarse.dnm']},indent=2))
for k,v in report.items():print(k,[(np.round(a['physical_exit_profiles'][0][2:4],4).tolist(),np.round(a['physical_exit_profiles'][-1][2:4],4).tolist()) for a in v])
