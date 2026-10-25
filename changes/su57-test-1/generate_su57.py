from pathlib import Path
import math,json,copy
import numpy as np
from scipy.interpolate import PchipInterpolator
from mesh import Mesh,node
from rig import rig_node
from gear_v3 import clip,cut_bay,normal
import dnm
lab=Path(__file__).resolve().parent;dest=lab/'runtime/aircraft';dest.mkdir(parents=True,exist_ok=True);packs={};nodes=[];stats={}
BLUE=(91,132,158);WHITE=(206,216,220);BELLY=(105,133,150);DARK=(28,38,46)
def face(m,pts,c,bright=False,up=None):
 if len(pts)<3:return
 nn=normal(pts)
 if sum(x*x for x in nn)<.5:return
 if up is not None and sum(a*b for a,b in zip(nn,up))<0:pts=pts[::-1]
 m.face(pts,c,bright)
def both(m,pts,c):face(m,pts,c);face(m,pts[::-1],c)
def camo(x,z):
 if z>8.12:return (196,210,219)
 ix,iz=math.floor(abs(x)/.30),math.floor(z/.34)
 threshold=2.35+.25*(((iz*iz*17+iz*31+19)%11)-5)/2
 if z<-4.5:threshold=2.05+.15*((iz*7)%4)
 if abs(x)>6.62:return (136,168,186)
 if 4.2<abs(x)<5.1 and -3.15<z<-2.70:return BLUE
 return WHITE if abs(x)>threshold else BLUE

def paint(m,poly,up=True):
 if not up:face(m,poly,BELLY,up=(0,-1,0));return
 xs=[v[0] for v in poly];zs=[v[2] for v in poly]
 for ix in range(math.floor(min(xs)/.30),math.ceil(max(xs)/.30)):
  p=clip(clip(poly,0,ix*.30,True),0,(ix+1)*.30,False)
  if len(p)<3:continue
  for iz in range(math.floor(min(zs)/.34),math.ceil(max(zs)/.34)):
   q=clip(clip(p,2,iz*.34,True),2,(iz+1)*.34,False)
   if len(q)>=3:face(m,q,camo((ix+.5)*.30,(iz+.5)*.34),up=(0,1,0))
def add(name,m,cla=99,pos=(0,0,0),states=None,parent=None):
 fn=name+'.srf';packs[fn]=m.srf();n=node(name,fn,cla)
 n=dnm.edit(n,'POS ',' '.join(map(str,pos))+' 0 0 0 1')
 if states:
  a=n.index('NST 1');b=next(i for i,x in enumerate(n) if x.startswith('POS '));n[a:b]=['NST '+str(len(states))]+['STA '+' '.join(map(str,s)) for s in states]
 nodes.append(n)
 if parent:
  pi=next(i for i,a in enumerate(nodes) if dnm.name(a)==parent);nodes[pi]=dnm.edit(nodes[pi],'NCH ',str(sum(x.startswith('CLD ') for x in nodes[pi])+1));nodes[pi].insert(-1,'CLD "'+name+'"')
 return n

def orient(mesh,pivot,axis):
 ax=np.array(axis,dtype=float);ax/=np.linalg.norm(ax);ez=np.array([-ax[2],0,ax[0]]);mesh.v=[(float(np.dot(np.array(v)-pivot,ax)),v[1]-pivot[1],float(np.dot(np.array(v)-pivot,ez))) for v in mesh.v];return round(math.atan2(ax[2],ax[0])*32768/math.pi)

def surface(poly,y=.12,thick=.07):
 m=Mesh();pts=[(x,y,z) for x,z in poly];paint(m,pts);paint(m,[(x,y-thick,z) for x,z in poly],False)
 for a,b in zip(pts,pts[1:]+pts[:1]):
  both(m,[a,b,(b[0],b[1]-thick,b[2]),(a[0],a[1]-thick,a[2])],(112,143,162))
  m.tube((a[0],a[1]+.004,a[2]),(b[0],b[1]+.004,b[2]),.006,(78,107,126),6)
 return m

def cut2(poly,a,b,c,positive=True):
 out=[]
 for p,q in zip(poly,poly[1:]+poly[:1]):
  v=(a*p[0]+b*p[1]+c)*(1 if positive else -1);w=(a*q[0]+b*q[1]+c)*(1 if positive else -1)
  if v>=-1e-9:out.append(p)
  if v*w<0:
   t=v/(v-w);out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
 return out
# z, half-width, top, underside. This is a new shallow Su-57 lifting body.
rows=[(-10.05,.015,.08,-.06),(-9.65,.27,.18,-.15),(-9.1,.57,.24,-.28),(-8.3,1.15,.28,-.42),(-7.4,1.9,.34,-.55),(-6,2.2,.37,-.64),(-4.5,2.47,.42,-.72),(-3,2.60,.48,-.75),(-1.4,2.68,.54,-.73),(0,2.70,.58,-.69),(1.5,2.68,.66,-.62),(2.6,2.5,.78,-.56),(3.6,2.05,.89,-.50),(4.5,1.48,1.00,-.45),(5.3,1.12,1.06,-.41),(6.1,.91,1.02,-.37),(6.9,.77,.91,-.31),(7.6,.65,.79,-.23),(8.3,.50,.65,-.14),(9,.32,.46,-.045),(9.6,.14,.28,.04),(10.05,.001,.14,.138)]
func=[PchipInterpolator([a[0] for a in rows],[a[k] for a in rows]) for k in [1,2,3]]
def bodyval(x,z,top=True):
 w,t,b=[float(f(z)) for f in func];u=min(1,abs(x)/w);chine=.25*t+.15*b
 return chine+(t-chine)*(1-u*u)**.62 if top else chine+(b-chine)*(1-u*u)**.65
body=Mesh();zs=sorted(set([r[0] for r in rows]+[3.85,4.35,4.75,5.05,5.65,6.35,6.75,7.15]))
for za,zb in zip(zs,zs[1:]):
 for i in range(12):
  ua=-1+2*i/12;ub=-1+2*(i+1)/12
  for top in [True,False]:
   pts=[(ua*float(func[0](za)),bodyval(ua*float(func[0](za)),za,top),za),(ub*float(func[0](za)),bodyval(ub*float(func[0](za)),za,top),za),(ub*float(func[0](zb)),bodyval(ub*float(func[0](zb)),zb,top),zb),(ua*float(func[0](zb)),bodyval(ua*float(func[0](zb)),zb,top),zb)]
   # Triangulation preserves real face normals across changing sections.
   for q in [[pts[0],pts[1],pts[2]],[pts[0],pts[2],pts[3]]]:paint(body,q,top)
# Close pointed ends; no missing nose cap.
for z in [zs[0],zs[-1]]:
 w=float(func[0](z));poly=[(-w,bodyval(-w,z),z),(0,bodyval(0,z),z),(w,bodyval(w,z),z),(0,bodyval(0,z,False),z)];both(body,poly,(178,195,206) if z>0 else BLUE)
# Cut actual canopy opening with a sealed tub, never put glass over an uncut solid deck.
canopyrect=(-.43,.43,4.55,7.1);_,removed=__import__('gear_v3').cut_bay(body,canopyrect) if False else (0,None)
# Clip top skin only in the cockpit rectangle.
new=Mesh()
for ids,c,b in body.f:
 poly=[body.v[k] for k in ids]
 if normal(poly)[1]<=.2 or max(v[2] for v in poly)<4.55 or min(v[2] for v in poly)>7.1 or min(v[0] for v in poly)>.43 or max(v[0] for v in poly)<-.43:face(new,poly,c,b);continue
 inside=poly
 for axis,t,positive in [(0,-.43,True),(0,.43,False),(2,4.55,True),(2,7.1,False)]:
  outside=clip(inside,axis,t,not positive) if inside else []
  face(new,outside,c,b);inside=clip(inside,axis,t,positive) if inside else []
body=new
# Engine nacelles: rectangular forward inlet transitioning to a separated rounded aft housing.
engines=Mesh();intakes=Mesh()
for sg in [-1,1]:
 cx=sg*1.44
 profiles=[(3.00,.66,.39,-.68),(2.35,.72,.52,-.36),(1.5,.76,.65,-.23),(0,.77,.65,-.23),(-2,.77,.70,-.17),(-4,.75,.75,-.10),(-6,.71,.69,-.10),(-7.4,.68,.65,-.10),(-8.30,.66,.62,-.10)]
 def ep(row,k):
  z,rx,ry,cy=row;t=k*math.pi/12
  if z==3.0:
   # rounded rectangular inlet, rather than an open circular tube at the nose.
   co,si=math.cos(t),math.sin(t);return cx+rx*math.copysign(abs(co)**.45,co),cy+ry*math.copysign(abs(si)**.45,si),z
  return cx+rx*math.cos(t),cy+ry*math.sin(t),z
 for a,b in zip(profiles,profiles[1:]):
  for k in range(24):
   poly=[ep(a,k),ep(a,k+1),ep(b,k+1),ep(b,k)]
   radial=(sum(v[0] for v in poly)/len(poly)-cx,sum(v[1] for v in poly)/len(poly)-a[3],0)
   if sum(v*w for v,w in zip(normal(poly),radial))<0:poly.reverse()
   if normal(poly)[1]>.15:paint(engines,poly)
   else:face(engines,poly,BELLY)
 front=profiles[0]
 for k in range(24):
  a,b=ep(front,k),ep(front,k+1);aa=(cx+(a[0]-cx)*.93,front[3]+(a[1]-front[3])*.92,3.035);bb=(cx+(b[0]-cx)*.93,front[3]+(b[1]-front[3])*.92,3.035)
  both(intakes,[a,b,bb,aa],(75,106,127));aa2=(cx+(aa[0]-cx)*.75,aa[1],1.75);bb2=(cx+(bb[0]-cx)*.75,bb[1],1.75);both(intakes,[aa,bb,bb2,aa2],(24,34,41))
 cap=[(cx+.47*math.cos(k*math.pi/12),-.68+.30*math.sin(k*math.pi/12),1.74) for k in range(24)];both(intakes,cap,(13,20,27))
fixed=Mesh();fixed.merge(body);fixed.merge(engines);collision=copy.deepcopy(fixed)
# Complete wings are split into non-overlapping movable leading/trailing panels.
for sg,label in [(-1,'L'),(1,'R')]:
 wing=[(2.08,3.30),(7.05,-2.15),(6.88,-3.45),(3.2,-4.48),(2.08,-4.35)]
 collision.merge(surface([(sg*x,z) for x,z in wing],.14,.065))
 le=lambda x:3.30+(x-2.08)*(-5.45)/(7.05-2.08)
 th=lambda x:-4.35+(x-2.08)*(.90)/(6.88-2.08)+.66
 # regions z>=leading-.42 are slats; z<=trailing+.66 are trailing control surfaces.
 m_le=(le(7.05)-le(2.08))/(7.05-2.08);b_le=le(2.08)-m_le*2.08-.42
 m_te=(th(6.88)-th(2.08))/(6.88-2.08);b_te=th(2.08)-m_te*2.08
 slat=cut2(wing,-m_le,1,-b_le);rest=cut2(wing,-m_le,1,-b_le,False);trailing=cut2(rest,-m_te,1,-b_te,False);stationary=cut2(rest,-m_te,1,-b_te)
 pieces=[('WingFixed',stationary,99,None),('Slat',slat,184 if sg<0 else 185,(m_le,b_le)),('Aileron',cut2(trailing,1,0,-4.30),180 if sg<0 else 181,(m_te,b_te)),('Flap',cut2(trailing,1,0,-4.30,False),182 if sg<0 else 183,(m_te,b_te))]
 for title,poly,cla,line in pieces:
  poly=[(sg*x,z) for x,z in poly];m=surface(poly,.14,.065)
  if line:
   xx=sum(x for x,z in poly)/len(poly);zz=line[0]*abs(xx)+line[1];pivot=np.array([xx,.14,zz]);axis=[1,0,line[0]*sg];heading=orient(m,pivot,axis);states=[(0,0,0,0,0,0,1),(0,0,0,0,5461,0,1),(0,0,0,0,-5461,0,1)];a=add(title+'_'+label,m,cla,pivot,states);nodes[-1]=dnm.edit(a,'POS ',' '.join(map(str,pivot))+f' {heading} 0 0 1')
  else:fixed.merge(m)
 # Root leading-edge vortex-control surface (LEVCON), separate from wing slats.
 poly=[(sg*1.17,4.55),(sg*2.08,3.3),(sg*2.9,2.4),(sg*1.45,2.4)];m=surface(poly,.14,.075);pivot=np.array([sg*1.48,.14,2.53]);heading=orient(m,pivot,[1,0,0]);add('LEVCON_'+label,m,186 if sg<0 else 187,pivot,[(0,0,0,0,0,0,1),(0,0,0,0,3641,0,1),(0,0,0,0,-3641,0,1)])
 # All-moving horizontal stabilator: own surface, with no extra duplicated fixed skin.
 poly=[(sg*1.75,-6.45),(sg*4.24,-7.87),(sg*4.12,-9.20),(sg*2.0,-9.02)];m=surface(poly,.22,.085);collision.merge(m);pivot=np.array([sg*2.12,.22,-7.55]);orient(m,pivot,[1,0,0]);add('Stabilator_'+label,m,190 if sg<0 else 191,pivot,[(0,0,0,0,0,0,1),(0,0,0,0,4551,0,1),(0,0,0,0,-4551,0,1)])
 # Canted all-moving vertical tail, not a fixed Su27 fin with a little rudder.
 empty=Mesh();parent='FinAxis_'+label;add(parent,empty,99,(sg*1.97,.48,-7.55));nodes[-1]=dnm.edit(nodes[-1],'POS ',f'{sg*1.97} .48 -7.55 0 0 {-sg*3277} 1')
 fin=Mesh();contour=[(0,.95),(2.23,-.03),(2.06,-1.12),(0,-1.48)]
 for side in [-1,1]:
  poly=[(side*.035,y,z) for y,z in contour]
  for iy in range(9):
   for iz in range(-6,5):
    q=clip(clip(clip(clip(poly,1,iy*.25,True),1,(iy+1)*.25,False),2,iz*.30,True),2,(iz+1)*.30,False)
    col=WHITE if iy>1 and iz<(-2+(iy*3)%4) else BLUE
    face(fin,q,col,up=(side,0,0))
 for a,b in zip(contour,contour[1:]+contour[:1]):face(fin,[(-.035,*a),(.035,*a),(.035,*b),(-.035,*b)],BLUE)
 add('Fin_'+label,fin,188 if sg<0 else 189,states=[(0,0,0,0,0,0,1),(0,0,0,3641,0,0,1),(0,0,0,-3641,0,0,1)],parent=parent)
 # Vectorable nozzle with an overlapping root hidden inside fixed nacelle.
 noz=Mesh();prof=[(.22,.60),(-.18,.60),(-.65,.55),(-1.14,.46)]
 for j,((za,ra),(zb,rb)) in enumerate(zip(prof,prof[1:])):
  for k in range(24):
   t=k*math.pi/12;u=(k+1)*math.pi/12;poly=[(ra*math.cos(t),ra*math.sin(t),za),(ra*math.cos(u),ra*math.sin(u),za),(rb*math.cos(u),rb*math.sin(u),zb),(rb*math.cos(t),rb*math.sin(t),zb)];face(noz,poly,(95+(k%2)*10,100+(k%2)*10,105+(k%2)*10),up=(math.cos((t+u)/2),math.sin((t+u)/2),0))
 for k in range(24):
  t=k*math.pi/12;u=(k+1)*math.pi/12
  both(noz,[(.46*math.cos(t),.46*math.sin(t),-1.14),(.46*math.cos(u),.46*math.sin(u),-1.14),(.41*math.cos(u),.41*math.sin(u),-1.14),(.41*math.cos(t),.41*math.sin(t),-1.14)],(133,144,151));both(noz,[(.41*math.cos(t),.41*math.sin(t),-1.14),(.41*math.cos(u),.41*math.sin(u),-1.14),(.28*math.cos(u),.28*math.sin(u),-.30),(.28*math.cos(t),.28*math.sin(t),-.30)],(27,32,39))
 both(noz,[(.30*math.cos(k*math.pi/12),.30*math.sin(k*math.pi/12),-.30) for k in range(24)],(12,17,23));add('Nozzle_'+label,noz,192 if sg<0 else 193,(sg*1.44,-.10,-8.21))
 # Flame child follows vectoring nozzle, active only with actual afterburner.
 flame=Mesh()
 for (za,ra),(zb,rb),col in [((-1.10,.37),(-1.50,.39),(92,137,229)),((-1.50,.39),(-2.15,.20),(236,161,80)),((-2.15,.20),(-2.9,.004),(228,103,46))]:
  for k in range(16):
   t=k*math.pi/8;u=(k+1)*math.pi/8;face(flame,[(ra*math.cos(t),ra*math.sin(t),za),(ra*math.cos(u),ra*math.sin(u),za),(rb*math.cos(u),rb*math.sin(u),zb),(rb*math.cos(t),rb*math.sin(t),zb)],col,True)
 add('Flame_'+label,flame,110 if sg<0 else 111,states=[(0,0,0,0,0,0,0),(0,0,0,0,0,0,1)],parent='Nozzle_'+label)
# Canopy sill conforms to real forebody; floor and all ends sealed.
inside=Mesh();glass=Mesh();wind=Mesh();canrows=[(4.55,.43,1.04,1.12),(4.95,.43,1.05,1.58),(5.55,.43,1.06,1.83),(6.15,.43,1.02,1.79),(6.72,.43,.94,1.48),(7.10,.43,.86,.91)]
for i,(a,b) in enumerate(zip(canrows,canrows[1:])):
 za,w,_,ta=a;zb,_,_,tb=b
 def cp(st,k):
  z,w,y,top=st;t=k*math.pi/16;base=bodyval(w,z);x=w*math.cos(t)
  return (x,bodyval(x,z),z) if z in [4.55,7.10] else (x,base+(top-base)*math.sin(t),z)
 target=wind if i==4 else glass
 for k in range(16):face(target,[cp(a,k),cp(b,k),cp(b,k+1),cp(a,k+1)],(72,109,135,85),up=(0,1,0))
 for k in [0,16]:target.tube(cp(a,k),cp(b,k),.014,(65,88,105),8)
 for sg in [-1,1]:
  aa=(sg*w,bodyval(w,za),za);bb=(sg*w,bodyval(w,zb),zb);both(inside,[aa,bb,(sg*w,.57,zb),(sg*w,.57,za)],DARK)
 both(inside,[(-w,.57,za),(w,.57,za),(w,.57,zb),(-w,.57,zb)],(24,33,41))
for st in [canrows[0],canrows[-1]]:
 z,w,y,t=st;poly=[(-w,.57,z),(w,.57,z)]+[(x,bodyval(x,z),z) for x in np.linspace(w,-w,17)];both(inside,poly,DARK)
for st,out in [(canrows[0],glass),(canrows[-2],wind)]:
 for k in range(16):out.tube(cp(st,k),cp(st,k+1),.013,(83,110,129),8)
inside.box(0,.91,5.18,.36,.52,.17,(32,41,48));inside.box(0,1.22,5.14,.27,.16,.16,(43,53,58));inside.box(0,.83,5.57,.34,.16,.43,(65,75,67));inside.box(0,1.00,5.57,.29,.34,.24,(67,80,69));inside.tube((0,1.16,5.62),(0,1.31,5.62),.10,(152,165,169),12);inside.box(0,1.27,5.71,.14,.055,.025,(27,38,45));inside.box(0,.98,6.70,.69,.18,.20,DARK)
# IRST ball ahead of windscreen, with dark coated lens.
sensor_y=bodyval(-.29,7.02)
inside.tube((-.29,sensor_y-.015,7.02),(-.29,sensor_y+.10,7.02),.09,(99,126,143),12)
inside.box(-.29,sensor_y+.10,7.08,.11,.065,.04,(53,60,85))
fixed.merge(wind);add('CockpitLiner',inside)
canhinge=(0,bodyval(.43,4.55),4.55);glass.shift(*[-v for v in canhinge]);add('Canopy',glass,100,canhinge,[(0,0,0,0,0,0,1),(0,0,0,0,6372,0,1)])
# Three true gear cavities. Only exterior bottom cut polygons become doors.
gearstats=[]
for title,cla,pivot,wheelcenter,radius,rect in [('Nose',140,(0,-.10,4.95),(0,-1.72,4.95),.28,(-.43,.43,4.65,7.05)),('Left',141,(-1.76,-.36,-2.55),(-2.00,-1.55,-2.30),.45,(-2.52,-1.13,-2.85,-.15)),('Right',142,(1.76,-.36,-2.55),(2.00,-1.55,-2.30),.45,(1.13,2.52,-2.85,-.15))]:
 before=copy.deepcopy(fixed);_,cut=cut_bay(fixed,rect);outer=Mesh()
 from rig import sample_y
 for ids,c,b in cut.f:
  poly=[cut.v[k] for k in ids];cx=sum(v[0] for v in poly)/len(poly);cz=sum(v[2] for v in poly)/len(poly);cy=sum(v[1] for v in poly)/len(poly);lowest=sample_y(before,cx,cz)
  if lowest is not None and cy<=lowest+.075:face(outer,poly,c)
 well=Mesh();door=Mesh();offset=.80 if title!='Nose' else .65
 for ids,c,b in outer.f:
  poly=[outer.v[k] for k in ids];roof=[]
  for x,y,z in poly:
   high=bodyval(x,z) if abs(x)<=float(func[0](z)) else -10
   if title!='Nose':
    u=(abs(x)-1.44)/.77
    if abs(u)<1:high=max(high,-.10+.75*math.sqrt(1-u*u))
   roof.append((x,min(y+(1.30 if title!='Nose' else offset),high-.04),z));both(well,roof,(36,44,50))
  for a,b,aa,bb in zip(poly,poly[1:]+poly[:1],roof,roof[1:]+roof[:1]):both(well,[a,b,bb,aa],(61,72,80))
  face(door,[(x,y-.001,z) for x,y,z in poly],c);face(door,[(x,y+.022,z) for x,y,z in poly[::-1]],(66,81,92))
  for a,b in zip(poly,poly[1:]+poly[:1]):face(door,[a,b,(b[0],b[1]+.022,b[2]),(a[0],a[1]+.022,a[2])],(107,136,155))
 px,py,pz=pivot;well.box(px,py+.025,pz,.29,.15,.25,(90,105,115));well.tube((px-.19,py,pz),(px+.19,py,pz),.09,(127,141,151),12);add('Bay_'+title,well,151)
 axle=tuple(wheelcenter[k]-pivot[k] for k in range(3));leg=Mesh();leg.tube((0,.04,0),axle,.061 if title=='Nose' else .085,(172,185,192),12);leg.tube((0,.04,0),tuple(v*.58 for v in axle),.095 if title=='Nose' else .12,(115,133,146),12)
 for sg in [-1,1]:
  off=.10 if title=='Nose' else .12;pts=[(axle[0]*.5+sg*off,axle[1]*.5,axle[2]*.5),(axle[0]*.75+sg*(off+.04),axle[1]*.75,axle[2]*.75-.12),(axle[0],axle[1],axle[2])]
  for a,b in zip(pts,pts[1:]):leg.tube(a,b,.025,(121,138,149),8)
 leg.box(*axle,.38 if title=='Nose' else .28,.10,.14,(136,151,162));packs['Gear_'+title+'.srf']=leg.srf();gn=rig_node('Gear_'+title,'Gear_'+title+'.srf',cla,pivot,up=(0,0,0,0,16384,0),children=['Steer_Nose' if title=='Nose' else 'Wheel_'+title]);nodes.append(gn)
 wheel=Mesh()
 for xx in [-.15,.15] if title=='Nose' else [0]:
  wheel.tube((xx-.10,0,0),(xx+.10,0,0),radius,(27,33,39),24)
  for sg in [-1,1]:
   wheel.tube((xx+sg*.101,0,0),(xx+sg*.114,0,0),radius*.60,(100,128,111),20);wheel.tube((xx+sg*.115,0,0),(xx+sg*.118,0,0),radius*.24,(160,174,183),12)
 if title=='Nose':add('Steer_Nose',Mesh(),147,axle,parent=None);nodes[-1]=dnm.edit(nodes[-1],'NCH ','1');nodes[-1].insert(-1,'CLD "Wheel_Nose"');wp=(0,0,0)
 else:wp=axle
 add('Wheel_'+title,wheel,146,wp,[(0,0,0,0,0,0,0),(0,0,0,0,0,0,1)])
 x0,x1,z0,z1=rect
 for side in ([False,True] if title=='Nose' else [title=='Right']):
  leaf=Mesh()
  for ids,c,b in door.f:
   poly=[door.v[k] for k in ids]
   if title=='Nose':poly=clip(poly,0,0,side)
   face(leaf,poly,c,b)
  hx=x1 if side else x0;hz=(z0+z1)/2;hy=sample_y(before,hx,hz);hy=hy if hy is not None else -.5;hinge=(hx,hy,hz);leaf.shift(*[-v for v in hinge]);name='Door_'+title+('_R' if title=='Nose' and side else '');add(name,leaf,143 if title=='Nose' else cla+3,hinge,[(0,0,0,0,0,0,1),(0,0,0,0,0,(1 if side else -1)*12743,1)])
 gearstats.append({'title':title,'pivot':pivot,'wheel_center':wheelcenter,'radius':radius,'rect':rect,'cut_faces':len(cut.f),'exterior_door_faces':len(outer.f),'contact_y':wheelcenter[1]-radius})
# Fixed hull root is a closed loft; all animations are separate named nodes.
add('Su57Hull',fixed,0);nodes.insert(0,nodes.pop())
add('IntakeLiners',intakes)
# Markings on wing top. Rays are unnecessary: wing upper skin is exactly y=.14.
mark=Mesh()
for sg in [-1,1]:
 for rr,c in [(.43,(224,232,234)),(.35,(173,42,48))]:
  pts=[]
  for k in range(10):
   a=k*math.pi/5;r=rr*(1 if k%2==0 else .42);pts.append((sg*5.55+r*math.sin(a),.144+(.003 if rr<.4 else 0),-2.35+r*math.cos(a)))
  for k in range(10):face(mark,[(sg*5.55,pts[0][1],-2.35),pts[k],pts[(k+1)%10]],c,up=(0,1,0))
add('Stars',mark)
nav=Mesh()
for sg,col in [(-1,(223,40,35)),(1,(45,210,95))]:face(nav,[(sg*7.052,.15,-2.25),(sg*7.052,.18,-2.40),(sg*7.052,.13,-2.48)],col,True)
add('Nav',nav,30)
# Reorder roots consistently and prune orphan packed surfaces before writing.
for coarse in ['su57.dnm','su57_coarse.dnm']:dnm.write(dest/coarse,packs,nodes)
from collision_su57 import build_collision
collision=build_collision(packs,nodes,rows)
(dest/'su57coll.srf').write_text('\n'.join(collision.srf())+'\n');(dest/'su57cockpit.srf').write_text('SURF\nE\n')
# Game flight parameters are an explicit approximation, not a certified Su57 dynamics model.
base_dat=lab/'baseline_su27.dat'
if not base_dat.exists():base_dat=lab.parent/'aircraft-lab6/runtime/aircraft/su27.dat'
s=base_dat.read_text();lines=[]
replacements={'IDENTIFY':'IDENTIFY "SU-57_FELON"','WEIGHCLN':'WEIGHCLN 18.5t','WEIGFUEL':'WEIGFUEL 10.3t','WINGAREA':'WINGAREA 78.8m^2','MAXSPEED':'MAXSPEED 2.0MACH','COCKPITP':'COCKPITP 0m 1.46m 5.90m','LEFTGEAR':'LEFTGEAR -2.0m -2.0m -2.3m','RIGHGEAR':'RIGHGEAR 2.0m -2.0m -2.3m','WHELGEAR':'WHELGEAR 0m -2.0m 4.95m','MACHNGUN':'MACHNGUN 1.15m .5m 4.3m','SMOKEGEN':'SMOKEGEN 0m 0m -10.1m','VAPORPO0':'VAPORPO0 7.0m .12m -3.0m','VAPORPO1':'VAPORPO1 7.0m .12m -3.0m','THRAFTBN':'THRAFTBN 29.0t','THRMILIT':'THRMILIT 18.0t','REFVLAND':'REFVLAND 140kt','ISPNLPOS':'ISPNLPOS 0m .65m 7m'}
for line in s.splitlines():
 a=line.split()
 if not a:lines.append(line);continue
 key=a[0]
 if key in ['HRDPOINT','LOADWEPN','ARRESTER']:continue
 lines.append(replacements.get(key,line))
(dest/'su57.dat').write_text('\n'.join(lines)+'\n');lst=dest/'aircraft.lst';old=lst.read_text() if lst.exists() else '';entry='aircraft/su57.dat aircraft/su57.dnm aircraft/su57coll.srf aircraft/su57cockpit.srf aircraft/su57_coarse.dnm'
if entry not in old:lst.write_text(old.rstrip()+'\n\n'+entry+'\n')
stats={'target_length_m':20.10,'target_span_m':14.10,'target_height_gear_down_m':4.60,'gear':gearstats,'nodes':len(nodes),'faces':sum(len(dnm.mesh(packs[dnm.fil(a)]).f) for a in nodes),'animation_classes':sorted({dnm.cla(a) for a in nodes}),'identifier':'SU-57_FELON'};(lab/'model-stats.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2))
