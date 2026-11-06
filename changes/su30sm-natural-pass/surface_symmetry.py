from pathlib import Path
import numpy as np,json,trimesh
from model import Model
r=Path(__file__).parent;m=Model();v,f=m.meshes['Fuselage_0_4'];R,t=m.poses['Fuselage_0_4'];v=v@R.T+t;points=np.unique(v,axis=0);points[:,0]*=-1;mesh=trimesh.Trimesh(vertices=v,faces=f,process=False);near,d,ids=trimesh.proximity.closest_point(mesh,points);report={'points':len(points),'max_m':float(d.max()),'p99_m':float(np.percentile(d,99)),'over_1mm_count':int(sum(d>.001)),'worst_mirrored_point':points[d.argmax()].tolist(),'nearest_surface':near[d.argmax()].tolist(),'note':'Distance from reflected Fuselage_0_4 vertices to actual mesh surface, not to vertices; same unchanged baseline source.'};(r/'surface-symmetry.json').write_text(json.dumps(report,indent=2));print(report)
