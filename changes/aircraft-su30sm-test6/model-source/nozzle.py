import numpy as np,json,math
from scipy.spatial.transform import Rotation,Slerp
class Nozzles:
 def __init__(self,g,scale,center):
  self.g=g;self.items={};self.groups={0:[],1:[]};self.bounds={};self.profiles={};self.original={}
  for i,n in enumerate(g.d['nodes']):
   if 'mesh' not in n:continue
   par=g.parents[i]
   if not g.d['nodes'][par].get('name','').startswith('Cylinder'):continue
   W=g.world(par);narrow=g.world(par,10.);wide=g.world(par,.03333333507180214);inv=np.linalg.inv(W[:3,:3]);rots=Rotation.from_matrix(np.array([narrow[:3,:3]@inv,wide[:3,:3]@inv]));interp=Slerp([0,1],rots);pivot=(W[:3,3]-center)*scale;v=np.concatenate([v for v,f,m,p in g.mesh(i)]);v=(v-center)*scale-pivot;side=0 if pivot[0]<0 else 1;item=(v,pivot,interp,par);self.items[par]=item;self.groups[side].append(item)
  self.axes={k:np.mean([v[1] for v in its],axis=0) for k,its in self.groups.items()}
  self.original={k:{'closed':self.measure(k,0),'wide':self.measure(k,1)} for k in [0,1]}
  maxrad=min(self.measure(k,.85)['radius'] for k in [0,1]);minrad=maxrad/1.35
  def solve(k,target):
   lo,hi=0.,1.
   for _ in range(28):
    mid=(lo+hi)/2
    if self.measure(k,mid)['radius']<target:lo=mid
    else:hi=mid
   return (lo+hi)/2
  for k in [0,1]:
   lo,hi=solve(k,minrad),solve(k,maxrad);self.bounds[k]=(lo,hi);self.profiles[str(k)]=[self.measure(k,lo+(hi-lo)*u) for u in np.linspace(0,1,21)]
  # Both installed engines use the same reference nozzle, mirrored across X.
  self.profiles['1']=[{**q,'cx':-q['cx']} for q in self.profiles['0']]
 def measure(self,k,a):
  axis=self.axes[k];rr=[];zz=[]
  for v,p,interp,par in self.groups[k]:
   q=v@interp([a]).as_matrix()[0].T+p;z=q[:,2].min();band=q[q[:,2]<z+.018];rr.append(np.linalg.norm(band[:,:2]-axis[:2],axis=1).min());zz.append(z)
  return {'radius':float(np.median(rr)),'z':float(np.mean(zz)),'cx':float(axis[0]),'cy':float(axis[1])}
 def rotation(self,parent,u):
  v,p,interp,par=self.items[parent];k=0 if p[0]<0 else 1;lo,hi=self.bounds[k];return interp([lo+(hi-lo)*u]).as_matrix()[0]
 def save(self,r):
  (r/'nozzle-profile.json').write_text(json.dumps(self.profiles,indent=2));(r/'nozzle-limits.json').write_text(json.dumps({'source_original':self.original,'source_interpolation_bounds':self.bounds,'maximum_radius_ratio':1.35,'not_a_factory_engine_control_model':True},indent=2));lines=['#pragma once','#include <array>','inline std::array<double,5> Su30ExhaustProfile(int engine,double opening){',' static const double p[2][21][5]={']
  for side in ['0','1']:
   samples=self.profiles[side];base=samples[-1];param=base['radius']/.67*.94;lines+=['{'+','.join('{'+','.join(f'{x:.10g}' for x in [v['radius']/base['radius'],v['radius']/base['radius'],0,0,(v['z']-base['z'])/param])+'}' for v in samples)+'},']
  lines+=['};',' const double u=(opening<0?0:opening>1?1:opening)*20;const int i=(int(u)<20?int(u):19);const double f=u-i;std::array<double,5> r;for(int j=0;j<5;++j)r[j]=p[engine][i][j]+f*(p[engine][i+1][j]-p[engine][i][j]);return r;','}'];(r/'engine/YSFLIGHT/src/vehicle/su30_exhaust_profile.h').write_text('\n'.join(lines)+'\n');print('NOZZLE LIMITS',self.bounds,'radius',self.profiles['0'][0]['radius'],self.profiles['0'][-1]['radius'],flush=True)
