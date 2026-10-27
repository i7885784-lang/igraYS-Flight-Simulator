"""Source Su-34 upper cylinder plus swivelling complete lower fork/bogie."""
import math,numpy as np
import json,os
from pathlib import Path
from types import SimpleNamespace
from scipy.spatial.transform import Rotation
from scipy.optimize import differential_evolution
from mesh import Mesh

def build_main(title,upper,lower,wheels,source,bone,env,add,double,sta,cv,align):
 sign=1 if title=='L' else -1;original=cv(source.skeleton[bone]['position']);pivot=original.copy()
 v=np.array(upper.v);center=v.mean(0);_,_,vt=np.linalg.svd(v-center,full_matrices=False);up=vt[0]
 if up[1]<0:up=-up
 q=np.array(lower.v);projection=q@up;F=q[projection>projection.max()-.045].mean(0)
 collar=Mesh();collar.tube(tuple(F-up*.08),tuple(F+up*.08),.067,(147,166,179),12);lower.merge(collar)
 def samples(mesh):
  rows=list(mesh.v)
  for ids,col,bright in mesh.f:
   poly=np.array([mesh.v[i] for i in ids]);c=poly.mean(0);rows.append(c)
   for a,b in zip(poly,np.roll(poly,-1,axis=0)):rows.extend(a+(b-a)*f for f in np.linspace(0,1,max(2,int(np.linalg.norm(b-a)/.045)+1)))
   for a in poly:
    for f in [.25,.5,.75]:rows.append(a*(1-f)+c*f)
  return np.unique(np.round(rows,5),axis=0)
 V=samples(upper);L=samples(lower);W=samples(wheels)
 def pose(params,fold):
  rx,ry,rz,swivel,compression,hy=params;p=original.copy();p[1]=hy;R=Rotation.from_euler('XYZ',np.array([rx,ry,rz])*fold,degrees=True).as_matrix();t=p-R@p
  S=Rotation.from_rotvec(up*math.radians(swivel)*np.clip((fold-.70)/.30,0,1)).as_matrix();C=up*compression*fold;A=R@S;u=R@(F-S@F+C)+t
  return R,t,A,u,p
 def cost(params,ret=False):
  R,t,A,u,p=pose(params,1);points=np.concatenate([V@R.T+t,L@A.T+u,W@A.T+u]);lo,hi,dist=env.bounds(points);hi=np.minimum(hi,.40)
  residual=np.concatenate([np.maximum(lo+.008-points[:,1],0),np.maximum(points[:,1]+.008-hi,0),np.maximum(dist-.012,0)*4,np.maximum(.25-sign*points[:,0],0)])
  bias=1e-7*((params[0]+90)**2+params[1]**2+params[2]**2+(abs(params[3])-90)**2)
  value=float(residual@residual+bias)
  return value,float(residual.max()) if ret else value
 # Use a separate wrapper so DE receives a scalar.
 def objective(p):return cost(p)[0]
 bounds=[(-115,-65),(-30,30),(-25,25),(-110,-70) if sign>0 else (70,110),(.10,.70),(0,.18)]
 initial=[-90,0,0,-90 if sign>0 else 90,.45,.08]
 cfg=Path(__file__).resolve().parent/'gear-fit.json'
 if cfg.exists() and not os.environ.get('REFIT_GEAR'):
  params=np.array(json.loads(cfg.read_text())[title]);result=SimpleNamespace(x=params,fun=objective(params))
 else:result=differential_evolution(objective,bounds,x0=initial,seed=73 if sign>0 else 74,popsize=12,maxiter=180,tol=1e-7,polish=True);params=result.x
 R,t,A,u,pivot=pose(params,1);_,maximum=cost(params,True)
 if maximum>.010:raise RuntimeError(('Stored gear fit no longer matches source',title,maximum))
 adjustments={}
 for name,mesh,M,tr in [('upper',upper,R,t),('lower',lower,A,u),('wheels',wheels,A,u)]:
  points=np.array(mesh.v);world=points@M.T+tr;lo,hi,dist=env.bounds(world);hi=np.minimum(hi,.40);change=np.maximum(lo+.008-world[:,1],0)-np.maximum(world[:,1]-(hi-.008),0);amount=float(abs(change).max());adjustments[name]=amount
  if amount>.045 or dist.max()>.03:raise RuntimeError(('Nested main gear needs redesign',title,name,amount,float(dist.max()),params.tolist()))
  mesh.v=[tuple(p) for p in points+change[:,None]*M[1,:]]
 states=[];lowerstates=[];matrices=[]
 for g in np.linspace(0,1,101):
  fold=1-np.clip((g-.24)/.76,0,1);R,t,A,u,p=pose(params,fold);states.append(sta(R,t));lowerstates.append(sta(A,u));matrices.append((R,t,A,u))
 double(upper);add('Gear'+title,upper,210,states);double(lower);add('GearLower'+title,lower,210,lowerstates);double(wheels);add('Wheels'+title,wheels,210,lowerstates)
 trunnion=Mesh();trunnion.tube(tuple(pivot),tuple(original),.060,(145,165,179),12);add('MainUpperTrunnion'+title,trunnion,210,states)
 # A connected two-link drag brace follows the ACTUAL lower fork, not the tyre axle.
 base=cv([(-1 if title=='L' else 1)*2.46,-3.75,.50]);base[1]=.18;attachment=F-up*.30;pairs=[(base,A@attachment+u) for R,t,A,u in matrices];length=max(np.linalg.norm(b-a) for a,b in pairs)*.55
 def knee(a,b,phi):
  d=b-a;side=np.cross(d,[0,1,0]);side/=np.linalg.norm(side)
  if side[0]*sign>0:side=-side
  vertical=np.cross(d/np.linalg.norm(d),side)
  if vertical[1]<0:vertical=-vertical
  return (a+b)/2+(side*math.cos(phi)+vertical*math.sin(phi))*math.sqrt(max(0,length*length-d@d/4))
 def knee_cost(phi):
  a,b=pairs[0];k=knee(a,b,phi);q=np.vstack([a+(k-a)*f for f in np.linspace(0,1,61)]+[k+(b-k)*f for f in np.linspace(0,1,61)]);lo,hi,_=env.bounds(q);r=np.concatenate([np.maximum(lo+.085-q[:,1],0),np.maximum(q[:,1]+.045-np.minimum(hi,.4),0)]);return float(r@r+1e-7*phi*phi)
 phi=min(np.linspace(0,math.pi/2,91),key=knee_cost);links=[[],[]]
 for i,(a,b) in enumerate(pairs):
  fold=1-np.clip((i/100-.24)/.76,0,1);k=knee(a,b,phi*fold)
  for j,(start,end) in enumerate([(a,k),(k,b)]):links[j].append(sta(align([0,0,1],end-start),start))
 for j in [0,1]:
  m=Mesh();m.tube((0,0,0),(0,0,length),.021,(150,169,181),10);add('MainDragBrace'+title+str(j),m,210,links[j])
 info={'nested_lower_fork_swivel':True,'fork_pivot':F.tolist(),'fork_axis':up.tolist(),'root':pivot.tolist(),'parameters_rx_ry_rz_swivel_compression_hingeY':params.tolist(),'fit_error_m':maximum,'corner_adjustments_m':adjustments,'cost':float(result.fun),'source_upper_cylinder_and_whole_lower_fork':True}
 print('NESTED MAIN',title,info,flush=True);return info
