"""Fixed-pivot samples prevent affine-translation drift at partial opening."""
from pathlib import Path
import sys,numpy as np,math,xml.etree.ElementTree as ET,json
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'model-source'))
from common import *
p,ns=dnm.read(root/'runtime/aircraft/mig29.dnm');xml=ET.parse(root/'upstream/mig29/Mig-29.xml').getroot();C=np.array([[0.,-1,0],[0,0,1],[-1,0,0]]);cv=lambda q:C@np.array(q)+[0,0,8.05];count=0
for n in ns:
 name=dnm.name(n)
 if name.startswith('Louvers') or name in ['AirBrakeU','AirBrakeB']:
  a=next(a for a in xml.findall('animation') if a.findtext('type')=='rotate' and name in [e.text for e in a.findall('object-name')]);ax=a.find('axis');vals=lambda e,s:[float(e.findtext(k+s,'0')) for k in ['x','y','z']];pivot=cv(vals(ax,'1-m'));axis=cv(vals(ax,'2-m'))-pivot;axis/=np.linalg.norm(axis);angle=float(a.findtext('factor')) if a.findtext('factor') is not None else float(a.findall('interpolation/entry')[-1].findtext('dep'));poses=[]
  for u in np.linspace(0,1,41):
   A=Rotation.from_rotvec(axis*math.radians(angle)*u).as_matrix();poses.append(state(A,pivot-A@pivot))
  if name.startswith('Louvers'):count+=1
 elif name.startswith('GroundFODScreen'):
  m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v);top=v[v[:,1]>v[:,1].max()-.02];pivot=top.mean(0);poses=[]
  for u in np.linspace(0,1,41):
   A=Rotation.from_rotvec([math.radians(49)*(1-u),0,0]).as_matrix();poses.append(state(A,pivot-A@pivot))
 else:continue
 i=next(i for i,s in enumerate(n) if s.startswith('NST '));j=next(i for i,s in enumerate(n) if s.startswith('POS '));n[i:j]=['NST 41']+poses
assert count==10
dnm.write(root/'runtime/aircraft/mig29.dnm',p,ns);(root/'mig-louver-repair.json').write_text(json.dumps({'louvers':count,'sides':['left','right'],'samples_per_fixed_pivot':41,'protection_ramps':2,'tail_airbrakes':2,'mode':'inward opening with fixed lateral hinges'},indent=2))
