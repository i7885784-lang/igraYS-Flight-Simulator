"""Variable-area, overlapping rigid petals. TVC stays on Su-57 parent nodes only."""
from pathlib import Path
import sys,json,math
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'model-source'))
from common import *
from gear_v3 import clip
from nozzle_geometry import *
report={}
def variable(p,ns,name,x,y,front,back,rx,ry,ex,ey,parent=None):
 N=24;L=front-back;extent=2*math.pi/N
 for k in range(N):
  a=extent*(k+.5);a0=a-extent*.57;a1=a+extent*.57
  def pt(t,aa,inside=False):
   rr=1-.022 if inside else 1.;return point(x,y,front-L*t,(rx+(ex-rx)*t)*rr,(ry+(ey-ry)*t)*rr,aa)
  m=Mesh()
  for j,(t0,t1) in enumerate([(0,.19),(.19,.80),(.80,1)]):
   col=[(123,128,132),(104,111,119),(83,92,103)][j];col=tuple(c+(k%2)*6 for c in col)
   m.face([pt(t0,a0),pt(t0,a1),pt(t1,a1),pt(t1,a0)],col)
   m.face([pt(t1,a0,True),pt(t1,a1,True),pt(t0,a1,True),pt(t0,a0,True)],(66,72,81))
   m.face([pt(t0,a1-.018),pt(t0,a1),pt(t1,a1),pt(t1,a1-.018)],(67,74,86))
  m.face([pt(1,a0),pt(1,a1),pt(1,a1,True),pt(1,a0,True)],(143,138,131))
  # Root tangent hinge; 21 rigid poses, finite overlaps throughout the range.
  pivot=np.array([x+rx*math.cos(a),y+ry*math.sin(a),front]);axis=np.array([-math.sin(a),math.cos(a),0.]);angle=math.atan2((1-.72)*math.sqrt((ex*math.cos(a))**2+(ey*math.sin(a))**2),L);states=[]
  for opening in np.linspace(0,1,21):
   R=Rotation.from_rotvec(axis*angle*(1-opening)).as_matrix();states.append(state(R,pivot-R@pivot))
  n=add(p,ns,name+'Petal'+str(k),double(m),270,states)
  if parent:
   i=next(i for i,s in enumerate(parent) if s.startswith('NCH '));parent[i]='NCH '+str(int(parent[i].split()[1])+1);parent.insert(i+1,'CLD "'+dnm.name(n)+'"')
for kind in ['su27','mig29','su34','su47','su57']:
 base=root/'runtime/aircraft'/f'{kind}.dnm' if kind=='mig29' else root/'baseline'/f'{kind}.dnm'
 p,ns=dnm.read(base);lu={dnm.name(n):n for n in ns};removed=[]
 def remove(names):
  global ns
  ns=[n for n in ns if dnm.name(n) not in names];removed.extend(names)
 if kind in ['su27','mig29','su34']:
  remove([n for n in lu if n.startswith(('OwnPetalNozzle','SourceNozzlePetals','OwnNozzleChamber','Exhaust','Afterburner'))])
  specs=({'su27':[(-1.2627,-.1908,-8.61,-9.1922,.601,.562,.548,.513),(1.2627,-.1908,-8.61,-9.1922,.601,.562,.548,.513)],'mig29':[(-.957,-.176,-5.797,-6.645,.537,.545,.43,.43),(.957,-.176,-5.797,-6.645,.537,.545,.43,.43)],'su34':[(1.19196,-.484,-8.37,-8.8773,.531,.531,.427,.427),(-1.15782,-.484,-8.37,-8.8773,.531,.531,.427,.427)]})[kind]
  for i,(x,y,front,back,rx,ry,ex,ey) in enumerate(specs):
   variable(p,ns,'VariableNozzle'+str(i),x,y,front,back,rx,ry,ex,ey)
   if kind=='su34':add(p,ns,'NozzleFixedCollar'+str(i),petal_shell(x,y,-8.16,front+.01,.396,.396,rx,ry))
   if kind=='su34':
    inner=petal_shell(x,y,-8.14,front+.015,.372,.372,rx*.94,ry*.94);inner.f=[(ids,(61,68,78),b) for ids,c,b in inner.f];add(p,ns,'NozzleInnerCollar'+str(i),inner)
    add(p,ns,'NozzleChamber'+str(i),chamber(x,y,-8.14,.372,.372,1.05))
   else:add(p,ns,'NozzleChamber'+str(i),chamber(x,y,front-.02,rx*.94,ry*.94,1.05))
   add(p,ns,'Afterburner'+str(i),flame(x,y,back-.02,ex,ey),110+i,[state(show=0),state()])
 elif kind=='su47':
  # Source petals already have an aperture pose; the engine previously never drove it.
  for side in ['L','R']:
   n=lu['NozzleInterior'+side];v=np.array(dnm.mesh(p[dnm.fil(n)]).v);x,y=(v[:,:2].min(0)+v[:,:2].max(0))/2;back=v[:,2].min();p[dnm.fil(n)]=chamber(x,y,back+.07,.375,.375,1.20).srf()
   n=lu['Afterburner'+side];p[dnm.fil(n)]=flame(x,y,back-.02,.43,.43).srf()
 elif kind=='su57':
  for side in ['L','R']:
   n=lu['Nozzle_'+side];old=dnm.mesh(p[dnm.fil(n)]);m=Mesh()
   for ids,c,b in old.f:
    q=clip([old.v[j] for j in ids],2,-.46,True)
    if len(q)>=3:m.face(q,c,b)
   p[dnm.fil(n)]=m.srf()
   variable(p,ns,'VariableNozzle'+side,0,0,-.45,-1.6405,.59,.59,.44,.44,n)
   chambernode=add(p,ns,'NozzleChamber'+side,chamber(0,0,-.47,.59*.94,.59*.94,.9));idx=next(i for i,s in enumerate(n) if s.startswith('NCH '));n[idx]='NCH '+str(int(n[idx].split()[1])+1);n.insert(idx+1,'CLD "'+dnm.name(chambernode)+'"')
   p[dnm.fil(lu['Flame_'+side])]=flame(0,0,-1.6605,.44,.44).srf()
 target=root/'runtime/aircraft'/f'{kind}.dnm';dnm.write(target,p,ns)
 # Every aircraft uses the same detailed mesh in near/far diagnostic views.
 import shutil
 coarse={'su27':'su27_coarse.dnm','mig29':'mig29_coarse.dnm','su34':'su34_coarse.dnm','su47':'su47_coarse.dnm','su57':'su57_coarse.dnm'}[kind];shutil.copy2(target,target.with_name(coarse))
 report[kind]={'variable_aperture':True,'thrust_vectoring':kind=='su57','removed_static_nozzles':removed,'petal_state_class':120 if kind=='su47' else 270}
(root/'nozzles.json').write_text(json.dumps(report,indent=2))
