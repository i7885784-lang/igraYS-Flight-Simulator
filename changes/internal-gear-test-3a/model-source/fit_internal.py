"""Fit stowed gear to the ORIGINAL skin envelope; never enlarge the aircraft."""
import numpy as np,math,json
from scipy.spatial.transform import Rotation
from scipy.optimize import differential_evolution,minimize_scalar
from envelope import Envelope

def align(a,b):
 a=np.asarray(a,float);b=np.asarray(b,float);a/=np.linalg.norm(a);b/=np.linalg.norm(b);cross=np.cross(a,b);c=np.clip(a@b,-1,1)
 if np.linalg.norm(cross)<1e-10:return np.eye(3)
 return Rotation.from_rotvec(cross/np.linalg.norm(cross)*math.acos(c)).as_matrix()
def reference(ac,su):
 objects=[o for o in ac.objects if (o['name'].startswith('HULL_Hull_Upper') if su else o['name'] in ['fuselage','WingL','WingR'] or any(s in o['name'] for s in ['geardoor','gearwell']))]
 if su:
  objects+= [o for o in ac.objects if o['name'] in ['GLS_Canopy_Rear.001','GLS_Canopy_Rear','object.001']]
  objects.append({'name':'nose_bay_flush_reference','v':[(-.30,-.12,1.30),(.30,-.12,1.30),(.30,-.10,4.65),(-.30,-.10,4.65)],'f':[[0,1,2,3]]})
 return Envelope(objects)
def fit(kind,title,pivot,axle,names,objects,env):
 su=kind=='su27';nose=title=='N';sg=1 if title=='L' else -1;leg=[];wheel=[];lower=[]
 for n in names:
  o=objects[n];v=np.array(o['v'])
  for f in o['f']:
   iswheel='Tyre' in n or n.startswith('wheel.')
   if n.startswith('UC_Main_') and n.endswith('Hub'):iswheel=v[f,1].mean()<axle[1]+.40
   (lower if su and nose and n not in ['UC_Nose_Upper_Strut','UC_Nose_LLights'] else wheel if iswheel and not nose else leg).extend(v[f])
 lower=np.unique(np.round(lower,5),axis=0) if lower else np.empty((0,3));leg=np.unique(np.round(leg,5),axis=0);wheel=np.unique(np.round(wheel,5),axis=0) if wheel else np.empty((0,3));d=axle-pivot;ln=np.linalg.norm(d);direction=1 if su or not nose else -1;cap=(.78 if su else .63) if nose else .48
 def evaluate(params,ret=False):
  x,y,phi=(0,params[0],0) if nose else (sg*params[0],params[1],params[2])
  compression=params[1] if nose and su else 0.;C=-d/ln*compression;short=axle+C-pivot;shortln=np.linalg.norm(short)
  dz2=shortln*shortln-(x-pivot[0])**2-(y-pivot[1])**2
  if dz2<=0:return 1e8
  target=np.array([x,y,pivot[2]+direction*math.sqrt(dz2)]);axis=(target-pivot)/shortln;R=Rotation.from_rotvec(axis*phi).as_matrix()@align(short,target-pivot);t=pivot-R@pivot
  W=align(R@np.array([1.,0,0]),[0,sg,0]) if not nose else np.eye(3);Q=W@R;u=target+W@(t+R@C-target)
  points=np.concatenate([leg@R.T+t,(lower+C)@R.T+t,wheel@Q.T+u]);low,high,dist=env.bounds(points);high=np.minimum(high,cap)
  r=np.stack([np.maximum(low+.025-points[:,1],0),np.maximum(points[:,1]+.025-high,0),np.maximum(dist-.01,0)*4],1)
  if not nose:
   mirror=points.copy();mirror[:,0]*=-1;ml,mh,md=env.bounds(mirror);mh=np.minimum(mh,cap);mr=np.stack([np.maximum(ml+.035-mirror[:,1],0),np.maximum(mirror[:,1]+.035-mh,0),np.maximum(md-.01,0)*4],1);r=np.concatenate([r,mr])
  value=float((r*r).sum()+.0000001*phi*phi+1e-6*((x-sg*1.05)**2+(y-.22)**2))
  if ret:return R,W,target,{'cost':value,'max_violation':float(r.max()),'violating_vertices':int((r.max(1)>.035).sum()),'target':target.tolist(),'roll':float(phi),'source_skin_only':True,'roof_cap':cap,'compression':float(compression)}
  return value
 if nose:
  result=differential_evolution(evaluate,[(.12,.55),(.20,.65)] if su else [(.12,.62)],seed=42,popsize=15,maxiter=100,tol=1e-7,polish=True);params=result.x
 else:
  result=differential_evolution(evaluate,[(.75,1.6),(-.08,.35),(-math.pi,math.pi)],seed=42,popsize=15,maxiter=200,tol=1e-7,polish=True);params=result.x
 R,W,target,info=evaluate(params,True);info['evaluations']=int(result.nfev);print(kind,title,'INTERNAL FIT',info,flush=True)
 return R,W,target,info
