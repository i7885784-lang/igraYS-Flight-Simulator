from pathlib import Path
import sys,numpy as np,json
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
from collision import arrays
from visibility import occluded
for kind in sys.argv[1:] or ['mig29']:
 p,ns=dnm.read(Path(__import__('os').environ.get('WHEEL_RUNTIME',str(r/'runtime')))/'aircraft'/f'{kind}.dnm');outer=Mesh();samples=[]
 for n in ns:
  name=dnm.name(n)
  if dnm.cla(n)==99 or name.startswith(('Source_fwdgeardoor','Source_reargeardoor','FlushGearDoor','MainBayInnerCover','MainBayForwardReturn','MainBaySlidingFloor','MainBaySlidingReturn','MainBayReturnStrip')):
   m=dnm.mesh(p[dnm.fil(n)]);R,t=transform(n,0);m.v=[tuple(q) for q in np.array(m.v)@R.T+t];outer.merge(m)
  if name in ['Gear_wheel_L_wheel','Gear_wheel_R_wheel','Gear_nosewheels_leg','NoseTireRight']:
   m=dnm.mesh(p[dnm.fil(n)]);R,t=transform(n,0);v=np.array(m.v)@R.T+t;samples.extend(np.unique(v,axis=0));samples.extend(np.array([v[ids].mean(0) for ids,c,b in m.f]))
 v,f=arrays(outer);tri=v[f];samples=np.array(samples);visible={}
 for direct in [[0,-1,0]]+[[np.cos(h)*np.cos(p),-np.sin(p),np.sin(h)*np.cos(p)] for h in np.linspace(0,2*np.pi,8,endpoint=False) for p in [0,.3,.8]]:
  bad=~occluded(tri,samples,direct)
  visible[str(direct)]={'visible_samples':int(bad.sum()),'total':len(samples),'points':samples[bad].round(5).tolist()}
 (r/(kind+'-'+__import__('os').environ.get('WHEEL_LABEL','final')+'-closed-wheel-check.json')).write_text(json.dumps(visible,indent=2));print(kind,[(k,v['visible_samples']) for k,v in visible.items()])
