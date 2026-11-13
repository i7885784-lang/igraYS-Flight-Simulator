import sys,json,collections,numpy as np
sys.path.insert(0,'changes/su30sm-local-skin');from repair import dnm
from fit_field import world,PAINT
p,ns=dnm.read('work/large-panels/su30sm.dnm');audit=json.load(open('work/large-panels/su30sm.audit.json'))
for name in ['MainWheelBayShutter_Left','MainWheelBayShutter_Right']:
 n=next(n for n in ns if dnm.name(n)==name);m=dnm.mesh(p[name+'.srf']);R,t=world(n);v=np.array(m.v)@R.T+t;sg=-1 if name.endswith('Left') else 1;uv=np.c_[sg*v[:,0],v[:,2]];xs=np.array(audit['panels'][name]['ordered_x_stations']);zs=np.array(audit['panels'][name]['ordered_z_stations']);groups=collections.defaultdict(list)
 for ids,c,b in m.f:
  if c not in PAINT or len(ids)!=3:continue
  q=v[ids];u=uv[ids];d=np.minimum.reduce([u[:,0]-1.052,1.87-u[:,0],u[:,1]+1.858,-.662-u[:,1]])
  if min(d)<.06:continue
  center=u.mean(0);ix=np.clip(np.searchsorted(xs,center[0])-1,0,len(xs)-2);iz=np.clip(np.searchsorted(zs,center[1])-1,0,len(zs)-2);a=(u[:,0]-xs[ix])/(xs[ix+1]-xs[ix]);bb=(u[:,1]-zs[iz])/(zs[iz+1]-zs[iz]);diag=np.mean(a-bb)>0
  if min(a)<-1e-6 or max(a)>1+1e-6 or min(bb)<-1e-6 or max(bb)>1+1e-6:continue
  if diag and min(a-bb)<-1e-6 or not diag and max(a-bb)>1e-6:continue
  cross=np.cross(q[1]-q[0],q[2]-q[0]);area=np.linalg.norm(cross)/2
  if area<1e-14:continue
  groups[(int(ix),int(iz),bool(diag))].append((area,cross/np.linalg.norm(cross)))
 errors=[]
 for g in groups.values():
  ref=max(g,key=lambda r:r[0])[1]
  errors.extend((a,float(np.degrees(np.arccos(np.clip(ref@n,-1,1))))) for a,n in g)
 print(name,'triangles',len(errors),'max angle',max(d for a,d in errors),'over 1deg',sum(d>1 for a,d in errors),'over .1deg',sum(d>.1 for a,d in errors),'bad area',sum(a for a,d in errors if d>.1))
