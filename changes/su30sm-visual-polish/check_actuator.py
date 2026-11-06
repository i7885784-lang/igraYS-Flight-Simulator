from pathlib import Path
import sys,json,numpy as np
r=Path(__file__).parent;sys.path.insert(0,str(r));from collision import interpolate
sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm');lu={dnm.name(n):n for n in ns};cn,pn=lu['AirbrakeActuator_Cylinder'],lu['AirbrakeActuator_Piston'];br=lu['Air_Brake_1_20'];L=max(v[1] for v in dnm.mesh(p[dnm.fil(pn)]).v);bp=np.array(next(s[4:] for s in br if s.startswith('POS ')).split()[:3],float)
R,t=transform(pn,0);B=t+R@np.array([0,L,0]);_,A=transform(cn,0);errors=[];overlap=[]
for g in np.linspace(0,1,201):
 q=interpolate(br,g);expected=q.getRotation()@(B-bp)+bp+q.getTranslation();c=interpolate(cn,g);piston=interpolate(pn,g);tip=piston.getRotation()@np.array([0,L,0])+piston.getTranslation();errors.append(np.linalg.norm(tip-expected));assert np.linalg.norm(c.getTranslation()-A)<1e-6;overlap.append(2*L-np.linalg.norm(tip-A))
out={'samples':201,'maximum_rod_attachment_error_m':float(max(errors)),'minimum_telescopic_overlap_m':float(min(overlap)),'fixed_base_m':A.tolist(),'no_detached_attachment_at_sampled_poses':bool(max(errors)<.002),'no_separated_cylinder_rod':bool(min(overlap)>0)};assert out['no_detached_attachment_at_sampled_poses'] and out['no_separated_cylinder_rod'];(r/'actuator-validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
