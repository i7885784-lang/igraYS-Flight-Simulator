from pathlib import Path
import sys,json,math,xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'model-source'))
from common import *
from ac_reference import AC
from gear_v3 import clip
p,ns=dnm.read(root/'baseline/mig29.dnm');lookup={dnm.name(n):n for n in ns}
ac=AC(root/'upstream/mig29/mesh_airframe.ac');xml=ET.parse(root/'upstream/mig29/Mig-29.xml').getroot()
for o in ac.objects:o['v']=(np.array(o['v'])+[0,0,8.05]).tolist()
# Restore precisely the donor skin outside the real main-gear apertures.
# Previous rectangular cut removed curved nacelle sides and made the door huge.
source=Mesh()
for o in ac.objects:
 if o['name'] not in ['fuselage','WingL','WingR']:continue
 for ids in o['f']:
  if len(ids)<3:continue
  q=np.array(o['v'])[ids];c=q.mean(0);col=(95,113,115) if c[1]<-.30 else (122,147,145)
  if c[1]>.15 and math.sin(c[2]*1.3)+.6*math.cos(c[0]*1.4)>.5:col=(79,106,104)
  source.face(q,col)
regions=[[(0,.25,True),(0,2.0,False),(2,-2.55,True),(2,.17,False),(1,.47,False)],[(0,-2.,True),(0,-.25,False),(2,-2.55,True),(2,.17,False),(1,.47,False)]]
def partition(poly,planes):
 inside=list(poly);outside=[]
 for ax,t,pos in planes:
  q=clip(inside,ax,t,not pos) if len(inside)>=3 else []
  if len(q)>=3:outside.append(q)
  inside=clip(inside,ax,t,pos) if len(inside)>=3 else []
 return inside,outside
hull=dnm.mesh(p['Hull.srf']);restored=Mesh()
for ids,c,b in hull.f:
 polys=[[hull.v[i] for i in ids]]
 for region in regions:
  polys=[q for poly in polys for q in partition(poly,region)[1]]
 for q in polys:restored.face(q,c,b)
for ids,c,b in source.f:
 for region in regions:
  q,_=partition([source.v[i] for i in ids],region)
  if len(q)>=3:restored.face(q,c,b);restored.face(q[::-1],c,b)
p['Hull.srf']=restored.srf()
remove=['FlushGearDoorL0','FlushGearDoorL1','FlushGearDoorR0','FlushGearDoorR1','InternalGearBayL','InternalGearBayR']
ns=[n for n in ns if dnm.name(n) not in remove]
C=np.array([[0.,-1,0],[0,0,1],[-1,0,0]])
def cv(q):return C@np.array(q)+[0,0,8.05]
clearance={}
for o in ac.objects:
 name=o['name']
 if not name.startswith(('fwdgeardoor.','reargeardoor.','GearWell')):continue
 m=Mesh()
 for ids in o['f']:
  if len(ids)>2:m.face([o['v'][i] for i in ids],(111,133,132) if 'door' in name else (55,68,73))
 if 'door' not in name:
  add(p,ns,'Source_'+name,double(m));continue
 a=next(a for a in xml.findall('animation') if a.findtext('type')=='rotate' and name in [e.text for e in a.findall('object-name')]);ax=a.find('axis');center=a.find('center')
 vals=lambda e,s:[float(e.findtext(k+s,'0')) for k in ['x','y','z']]
 pivot=cv(vals(center,'-m'));axis=cv(vals(ax,'2-m'))-cv(vals(ax,'1-m'));axis/=np.linalg.norm(axis);angle=float(a.findall('interpolation/entry')[-1].findtext('dep'))
 states=[]
 for g in np.linspace(0,1,101):
  phase=np.clip(g/(.22 if name.startswith('fwd') else .18),0,1);R=Rotation.from_rotvec(axis*math.radians(angle)*phase).as_matrix();states.append(state(R,pivot-R@pivot))
 n=add(p,ns,'Source_'+name.replace('.','_'),double(m),210,states);R,t=transform(n,100);q=np.array(m.v)@R.T+t;clearance[name]=float(q[:,1].min()+1.74)
# The FOD ramp pivots into its duct rather than disappearing on a speed threshold.
for n in ns:
 if dnm.name(n).startswith('GroundFODScreen'):
  m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v);top=v[v[:,1]>v[:,1].max()-.02];pivot=top.mean(0);R=Rotation.from_rotvec([math.radians(49),0,0]).as_matrix()
  i=next(i for i,s in enumerate(n) if s.startswith('NST '));j=next(i for i,s in enumerate(n) if s.startswith('POS '));n[i:j]=['NST 2',state(R,pivot-R@pivot),state()]
dnm.write(root/'runtime/aircraft/mig29.dnm',p,ns)
(root/'mig-repair.json').write_text(json.dumps({'source_door_ground_clearance_m':clearance,'removed_old_engine_side_leaves':remove,'source_gear_motion_retained':True},indent=2));print(clearance)
