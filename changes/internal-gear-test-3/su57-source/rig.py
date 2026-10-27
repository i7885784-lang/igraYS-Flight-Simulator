import math,re
from mesh import Mesh,node
import dnm

def prism(m,poly,thickness,color):
 a=[(x,y,z) for x,y,z in poly];b=[(x,y-thickness,z) for x,y,z in poly];m.face(a,color);m.face(b[::-1],color)
 for i in range(len(a)):j=(i+1)%len(a);m.face([a[i],b[i],b[j],a[j]],color)

def sample_y(m,x,z):
 hits=[]
 for ids,_,_ in m.f:
  pts=[m.v[i] for i in ids]
  for j in range(1,len(pts)-1):
   a,b,c=pts[0],pts[j],pts[j+1];den=(b[2]-c[2])*(a[0]-c[0])+(c[0]-b[0])*(a[2]-c[2])
   if abs(den)<1e-10:continue
   u=((b[2]-c[2])*(x-c[0])+(c[0]-b[0])*(z-c[2]))/den;v=((c[2]-a[2])*(x-c[0])+(a[0]-c[0])*(z-c[2]))/den
   if min(u,v,1-u-v)>=-1e-6:hits.append(u*a[1]+v*b[1]+(1-u-v)*c[1])
 return min(hits) if hits else None

def remove_original_gear(packs,nodes):
 root=dnm.name(nodes[0]);remove={dnm.name(n) for n in nodes if dnm.cla(n)==0 and dnm.name(n)!=root}
 while True:
  more={s[4:].strip('"') for n in nodes if dnm.name(n) in remove for s in n if s.startswith('CLD ')}
  if more.issubset(remove):break
  remove|=more
 nodes=[n for n in nodes if dnm.name(n) not in remove]
 for i,n in enumerate(nodes):
  n=[s for s in n if not (s.startswith('CLD ') and s[4:].strip('"') in remove)];n=dnm.edit(n,'NCH ',str(sum(s.startswith('CLD ') for s in n)));nodes[i]=n
 return nodes

def rig_node(name,file,cla,pos=(0,0,0),up=(0,0,0,0,0,0),down=(0,0,0,0,0,0),children=()):
 fmt=lambda a:' '.join(str(x) for x in a)
 return [f'SRF "{name}"',f'FIL {file}',f'CLA {cla}','NST 2','STA '+fmt(up)+(' 0' if cla in [140,141,142,146,151] else ' 1'),'STA '+fmt(down)+' 1','POS '+fmt(pos)+' 0 0 0 1','CNT 0 0 0','PAX 1 0 0','REL DEP','NCH '+str(len(children))]+[f'CLD "{c}"' for c in children]+['END']

def add_gear(packs,nodes,body,kind):
 nodes=remove_original_gear(packs,nodes);su=kind=='su27';tire=(31,35,38);metal=(153,164,171);hub=(83,114,83);dark=(37,43,49);stats=[]
 cfg=[('Nose',140,(0,-.25,3.6 if su else 2.9),(0,-1.60 if su else -1.46,4.05 if su else 3.2),.30 if su else .24),('Left',141,(-1.9 if su else -1.45,-.30,-3.4 if su else -.9),(-2.4 if su else -1.9,-1.52 if su else -1.36,-3.8 if su else -1.2),.38 if su else .34),('Right',142,(1.9 if su else 1.45,-.30,-3.4 if su else -.9),(2.4 if su else 1.9,-1.52 if su else -1.36,-3.8 if su else -1.2),.38 if su else .34)]
 for title,cla,pivot,world,radius in cfg:
  axle=tuple(world[k]-pivot[k] for k in range(3));leg=Mesh();leg.tube((0,0,0),axle,.055 if title=='Nose' else .073,metal,12)
  mid=tuple(a*.55 for a in axle);leg.tube(mid,axle,.033,(210,215,215),12)
  leg.tube((0,-.05,.10),(axle[0],axle[1]+.22,axle[2]-.10),.024,(98,110,119),8)
  leg.box(*axle,.23,.10,.13,metal)
  up=(0,.45 if title=='Nose' else .68,-.22 if title=='Nose' else 0,0,-16384 if title=='Nose' else 0,0 if title=='Nose' else (14564 if title=='Left' else -14564))
  wheel=Mesh();centers=[-.13,.13] if not su and title=='Nose' else [0]
  for xx in centers:
   wheel.tube((xx-.09,0,0),(xx+.09,0,0),radius,tire,20)
   for sign in [-1,1]:
    wheel.tube((xx+sign*.091,0,0),(xx+sign*.105,0,0),radius*.59,hub,16)
    wheel.tube((xx+sign*.106,0,0),(xx+sign*.108,0,0),radius*.22,metal,12)
    for k in range(8):
     t=k*math.pi/4;y=radius*.39*math.cos(t);z=radius*.39*math.sin(t)
     wheel.tube((xx+sign*.109,y,z),(xx+sign*.111,y,z),.014,(186,194,195),6)
   wheel.box(xx,0,radius-.01,.12,.07,.02,(75,79,81))
  fn='Gear_'+title+'.srf';wn='Wheel_'+title+'.srf';packs[fn]=leg.srf();packs[wn]=wheel.srf();child='Steer_Nose' if title=='Nose' else 'Wheel_'+title
  nodes.append(rig_node('Gear_'+title,fn,cla,pivot,up,children=[child]))
  if title=='Nose':
   packs['Empty.srf']=['SURF','E'];nodes.append(rig_node('Steer_Nose','Empty.srf',147,axle,children=['Wheel_Nose']));axle=(0,0,0)
  nodes.append(rig_node('Wheel_'+title,wn,146,axle))
  # Shallow dark bay fitted to the existing underside; doors open before the legs.
  bx=0 if title=='Nose' else (math.copysign(1.85 if su else 1.45,world[0]));bz=3.72 if su and title=='Nose' else (2.95 if title=='Nose' else (-3.55 if su else -1.0));width=.42 if title=='Nose' else .56;length=1.15 if title=='Nose' else .9
  poly=[]
  for dx,dz in [(-width/2,-length/2),(width/2,-length/2),(width/2,length/2),(-width/2,length/2)]:
   y=sample_y(body,bx+dx,bz+dz);y=y if y is not None else (-.55 if title=='Nose' else -.85);poly.append((bx+dx,y-.008,bz+dz))
  well=Mesh();prism(well,poly,.025,(20,25,29));wfn='Bay_'+title+'.srf';packs[wfn]=well.srf();nodes+= [rig_node('Bay_'+title,wfn,99)]
  hinge=(poly[0][0],poly[0][1]-.015,bz) if title!='Right' else (poly[1][0],poly[1][1]-.015,bz)
  door=Mesh();local=[tuple(pt[k]-hinge[k]-(.018 if k==1 else 0) for k in range(3)) for pt in poly];prism(door,local,.018,(126,151,166))
  dfn='Door_'+title+'.srf';packs[dfn]=door.srf();angle=-12743 if title!='Right' else 12743
  nodes.append(rig_node('Door_'+title,dfn,cla+3,hinge,down=(0,0,0,0,0,angle)))
  stats.append(dict(leg=title,contact_y=world[1]-radius,radius=radius,pivot=pivot))
 return nodes,stats

def add_pylons(packs,nodes,body,dat,kind):
 pylon=Mesh();new=[];stats=[]
 for line in dat.splitlines():
  a=line.split()
  if not a or a[0]!='HRDPOINT':new.append(line);continue
  x,y,z=[float(v.rstrip('m')) for v in a[1:4]]
  if kind=='su27' and abs(x)>7:
   pylon.box(x,y+.065,z,.10,.08,1.18,(95,109,119));pylon.box(x-math.copysign(.07,x),y+.03,z,.20,.06,.56,(112,134,149));ny=y;sy=y+.13
  else:
   sy=sample_y(body,x,z)
   if sy is None:
    near=[v for v in body.v if abs(v[0]-x)<.2 and abs(v[2]-z)<.8];sy=min((v[1] for v in near),default=y+.3)
   ny=sy-.23 if kind=='mig29' else min(y,sy-.20);base=ny+.065;top=sy+.015
   # Slender trapezoidal support and a launch rail, deliberately intersecting both attachments.
   poly=[(x-.055,base,z-.48),(x-.055,top,z-.32),(x-.055,top,z+.38),(x-.055,base,z+.53)]
   other=[(pt[0]+.11,pt[1],pt[2]) for pt in poly];pylon.face(poly[::-1],(102,120,133));pylon.face(other,(128,147,161))
   for i in range(4):j=(i+1)%4;pylon.face([poly[i],poly[j],other[j],other[i]],(119,137,151))
   pylon.box(x,ny+.065,z,.14,.07,1.16,(87,99,108))
  new.append('HRDPOINT '+' '.join(f'{v:.6f}m' for v in [x,ny,z])+' '+' '.join(a[4:]));stats.append(dict(x=x,y=ny,z=z,wing_y=sy))
 packs['Pylons.srf']=pylon.srf();nodes.append(rig_node('Pylons','Pylons.srf',99));return '\n'.join(new)+'\n',stats

def split_stabilators(packs,nodes):
 originals=[n for n in nodes if dnm.cla(n)==6]
 for old in originals:
  src=dnm.mesh(packs[dnm.fil(old)]);pos=list(map(float,next(s[4:] for s in old if s.startswith('POS ')).split()[:3]));states=[s for s in old if s.startswith('STA ')];remove=dnm.name(old);nodes=[n for n in nodes if dnm.name(n)!=remove]
  for j,n in enumerate(nodes):
   n=[s for s in n if not (s.startswith('CLD ') and s[4:].strip('"')==remove)];nodes[j]=dnm.edit(n,'NCH ',str(sum(s.startswith('CLD ') for s in n)))
  for sign,cla in [(-1,148),(1,149)]:
   m=Mesh();pivot=(sign*2.25,pos[1],pos[2])
   for ids,c,b in src.f:
    poly=[src.v[k] for k in ids];clipped=[]
    for a,bb in zip(poly,poly[1:]+poly[:1]):
     ia=sign*a[0]>=.015;ib=sign*bb[0]>=.015
     if ia:clipped.append(a)
     if ia!=ib:
      f=(sign*.015-a[0])/(bb[0]-a[0]);clipped.append(tuple(a[k]+f*(bb[k]-a[k]) for k in range(3)))
    if len(clipped)>=3:m.face([tuple(v[k]-pivot[k] for k in range(3)) for v in clipped],c,b)
   name='Stabilator_'+('L' if sign<0 else 'R');fn=name+'.srf';packs[fn]=m.srf();new=rig_node(name,fn,cla,pivot);start=new.index('NST 2');end=next(i for i,s in enumerate(new) if s.startswith('POS '));new[start:end]=['NST '+str(len(states))]+states;nodes.append(new)
 return nodes
