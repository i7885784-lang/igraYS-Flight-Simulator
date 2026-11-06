from pathlib import Path
import numpy as np,json,trimesh
from model import Model
r=Path(__file__).parent;m=Model();vs=[];fs=[];offset=0
for name,(v,f) in m.meshes.items():
 if name.startswith(('Su30Plume','Su30Dry')):continue
 R,t=m.poses[name];v=v@R.T+t;vs.append(v);fs.append(f+offset);offset+=len(v)
v=np.concatenate(vs);f=np.concatenate(fs);mesh=trimesh.Trimesh(vertices=v,faces=f,process=False);points=np.unique(np.round(v,5),axis=0)[::10];points[:,0]*=-1
near,d,ids=trimesh.proximity.closest_point(mesh,points);result={'closed_pose':0,'sampled_reflected_vertices':len(points),'max_distance_to_other_geometry_m':float(d.max()),'p99_m':float(np.percentile(d,99)),'over_1mm':int(sum(d>.001)),'worst_reflected_point':points[d.argmax()].tolist(),'nearest':near[d.argmax()].tolist(),'note':'Whole visual mesh sampled symmetry incl internal mechanisms; component Fuselage0_4 alone has deliberate openings filled by other nodes. Not certified factory geometry.'};(r/'whole-symmetry.json').write_text(json.dumps(result,indent=2));print(result)
