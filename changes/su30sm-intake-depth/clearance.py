from pathlib import Path
import numpy as np,json,fcl
from model import Model
r=Path(__file__).parent;out=[]
for source in ['baseline/su30sm.dnm','runtime/aircraft/su30sm.dnm']:
 m=Model(r/source);m.sample(1)
 for name in ['IntakeDuct_-1','IntakeDuct_1']:
  result=fcl.DistanceResult();distance=fcl.distance(m.objects[name],m.objects['Fuselage_0_4'],fcl.DistanceRequest(enable_nearest_points=True),result);out.append({'source':source,'node':name,'minimum_body_distance_m':float(distance),'nearest_points':[list(p) for p in result.nearest_points]});print(source,name,distance,flush=True)
(r/'clearance.json').write_text(json.dumps(out,indent=2))
