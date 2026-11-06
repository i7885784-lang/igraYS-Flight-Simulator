from pathlib import Path
import sys,json,numpy as np
from shapely.geometry import Polygon,Point
from shapely.strtree import STRtree
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm');lu={dnm.name(n):n for n in ns};paint={(142,169,181),(77,139,163),(118,166,185),(147,163,172)};support=[]
for name,n in lu.items():
 if not (name.startswith(('MainBayFixedSkin','MainWheelBayShutter','GearDoor','BayCornerSkin')) or name in ['Fuselage_0_4','Fuselage_0_5']):continue
 m=dnm.mesh(p[dnm.fil(n)]);R,t=transform(n,0);P=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);v=np.array(m.v)@R.T+t+P
 for ids,c,b in m.f:
  if c not in paint:continue
  for j in range(1,len(ids)-1):
   q=v[[ids[0],ids[j],ids[j+1]]]
   if np.cross(q[1]-q[0],q[2]-q[0])[1]<-1e-10:support.append(q)
polys=[Polygon(q[:,[0,2]]) for q in support];tree=STRtree(polys);coeff=np.array([np.linalg.solve(np.c_[q[:,[0,2]],np.ones(3)],q[:,1]) for q in support]);out={}
for name in ['GearWell_Left','GearWell_Right','GearWell_Nose']:
 m=dnm.mesh(p[name+'.srf']);v=np.array(m.v);bad=[];covered=uncovered=0
 for fi,(ids,c,b) in enumerate(m.f):
  a=v[ids].mean(0);hits=tree.query(Point(a[0],a[2]),predicate='intersects')
  if not len(hits):uncovered+=1;continue
  covered+=1;h=float((coeff[hits]@np.array([a[0],a[2],1])).min());d=h-a[1]
  if d>.001:bad.append({'face':fi,'centroid':a.tolist(),'below_m':d})
 out[name]={'tested_face_centroids_with_closed_support':covered,'no_projected_support':uncovered,'centroids_below_closed_skin_by_over_1mm':len(bad),'worst_below_m':max([a['below_m'] for a in bad],default=0),'examples':sorted(bad,key=lambda x:-x['below_m'])[:8]}
(r/'lining-final-check.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
