import math,copy
from mesh import Mesh
import dnm

def normal(pts):
 n=[0.,0.,0.]
 for a,b in zip(pts,pts[1:]+pts[:1]):
  n[0]+=(a[1]-b[1])*(a[2]+b[2]);n[1]+=(a[2]-b[2])*(a[0]+b[0]);n[2]+=(a[0]-b[0])*(a[1]+b[1])
 l=math.sqrt(sum(v*v for v in n));return tuple(v/l if l>1e-12 else 0 for v in n)
def clip(poly,axis,threshold,positive):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  va=(a[axis]-threshold)*(1 if positive else -1);vb=(b[axis]-threshold)*(1 if positive else -1)
  if va>=-1e-9:out.append(a)
  if (va>1e-9 and vb<-1e-9) or (va<-1e-9 and vb>1e-9):
   t=va/(va-vb);out.append(tuple(a[k]+(b[k]-a[k])*t for k in range(3)))
 return out

def cut_bay(body,rect,side=False,limits=(.14,-.93)):
 x0,x1,z0,z1=rect;out=Mesh();removed=Mesh();cut=0
 for ids,c,b in body.f:
  poly=[body.v[k] for k in ids];nn=normal(poly)
  if not((not side and nn[1]<-.12) or (side and nn[0]*(1 if x0>0 else -1)>.8 and min(v[1] for v in poly)<-.2)) or max(p[0] for p in poly)<=x0 or min(p[0] for p in poly)>=x1 or max(p[2] for p in poly)<=z0 or min(p[2] for p in poly)>=z1:
   out.face(poly,c,b);continue
  inside=poly
  for axis,t,positive in ([(0,x0,True),(0,x1,False),(2,z0,True),(2,z1,False)]+([(1,limits[0],False),(1,limits[1],True)] if side else [])):
   outside=clip(inside,axis,t,not positive) if len(inside)>=3 else []
   if len(outside)>=3:out.face(outside,c,b)
   inside=clip(inside,axis,t,positive) if len(inside)>=3 else []
  if len(inside)>=3:cut+=1;removed.face(inside,c,b)
 body.v=out.v;body.f=out.f;return cut,removed

def add_gear(packs,nodes,body,kind):
 from rig import remove_original_gear,rig_node,sample_y,prism
 nodes=remove_original_gear(packs,nodes);su=kind=='su27';skin=copy.deepcopy(body);tire=(31,35,38);metal=(163,172,179);stats=[]
 # root pivot is inside a genuine bay; nose leg is vertical when down.
 nz=4.05 if su else 3.2;ny=sample_y(skin,0,nz)+(.36 if su else .31)
 cfg=[('Nose',140,(0,ny,nz),(0,-1.6 if su else -1.46,nz),.30 if su else .24,(-.36,.36,3.67,6.60) if su else (-.40,.40,2.88,5.14),(0,0,0,0,16384,0))]
 for sign,title,cla in [(-1,'Left',141),(1,'Right',142)]:
  px=sign*(1.40 if su else 1.08);pz=-3.4 if su else -.9;py=-.05 if su else -.32
  rect=(1.20,2.05,-4.15,-.65) if su else (.95,1.70,-1.68,.88)
  if sign<0:rect=(-rect[1],-rect[0],rect[2],rect[3])
  cfg.append((title,cla,(px,py,pz),(sign*(2.4 if su else 1.9),-1.52 if su else -1.36,-3.8 if su else -1.2),.38 if su else .34,rect,(0,.34 if su else .80,0,0,16384,sign*(-6007 if su else -8192))))
 for title,cla,pivot,world,radius,rect,up in cfg:
  cut,skinDoor=cut_bay(body,rect,title!='Nose',(.22,-.59) if su else (.14,-.93));axle=tuple(world[k]-pivot[k] for k in range(3));leg=Mesh()
  leg.tube((0,.06,0),(0,-.20,0),.095 if title=='Nose' else .12,(85,99,111),12)
  leg.tube((0,0,0),axle,.052 if title=='Nose' else .072,metal,12)
  leg.tube(tuple(a*.53 for a in axle),axle,.032,(211,216,218),12)
  leg.tube((0,-.12,-.13),(axle[0],axle[1]+.23,axle[2]-.10),.025,(106,120,130),8)
  leg.box(*axle,.23,.10,.13,metal)
  wheel=Mesh();centers=[-.13,.13] if not su and title=='Nose' else [0]
  for xx in centers:
   wheel.tube((xx-.085,0,0),(xx+.085,0,0),radius,tire,20)
   for sign in [-1,1]:
    wheel.tube((xx+sign*.086,0,0),(xx+sign*.101,0,0),radius*.59,(83,114,83),16)
    wheel.tube((xx+sign*.102,0,0),(xx+sign*.106,0,0),radius*.22,metal,12)
    for k in range(8):
     angle=k*math.pi/4;y=radius*.39*math.cos(angle);z=radius*.39*math.sin(angle);wheel.tube((xx+sign*.107,y,z),(xx+sign*.112,y,z),.012,(175,184,188),6)
   wheel.box(xx,0,radius-.01,.11,.06,.02,(75,79,81))
  fn='Gear_'+title+'.srf';wn='Wheel_'+title+'.srf';packs[fn]=leg.srf();packs[wn]=wheel.srf();child='Steer_Nose' if title=='Nose' else 'Wheel_'+title
  nodes.append(rig_node('Gear_'+title,fn,cla,pivot,up,children=[child]))
  if title=='Nose':
   packs['Empty.srf']=['SURF','E'];nodes.append(rig_node('Steer_Nose','Empty.srf',147,axle,children=['Wheel_Nose']));wheelpos=(0,0,0)
  else:wheelpos=axle
  nodes.append(rig_node('Wheel_'+title,wn,146,wheelpos))
  x0,x1,z0,z1=rect
  # Segmented doors follow the underside, with matching cavity walls and a roof.
  # They replace the cut surface rather than lying on an unbroken hull.
  door=Mesh();well=Mesh();nx=4 if title!='Nose' else 2;nzseg=8
  ys={}
  for i in range(nx+1):
   for j in range(nzseg+1):
    x=x0+(x1-x0)*i/nx;z=z0+(z1-z0)*j/nzseg;y=sample_y(skin,x,z)
    ys[i,j]=(x,y if y is not None else pivot[1]-.35,z)
  for ids,c,b in skinDoor.f:
   poly=[skinDoor.v[k] for k in ids]
   prism(door,[(x,y-.002,z) for x,y,z in poly],.012,(124,148,163))
  perimeter=[ys[0,j] for j in range(nzseg+1)]+[ys[i,nzseg] for i in range(1,nx+1)]+[ys[nx,j] for j in range(nzseg-1,-1,-1)]+[ys[i,0] for i in range(nx-1,0,-1)]
  def inside_top(pt):
   # A shallow liner follows the skin; it must never rise above the aircraft's top surface.
   x,y,z=pt;hits=[]
   for ids,c,b in skin.f:
    pts=[skin.v[k] for k in ids]
    for k in range(1,len(pts)-1):
     a,b,c=pts[0],pts[k],pts[k+1];den=(b[2]-c[2])*(a[0]-c[0])+(c[0]-b[0])*(a[2]-c[2])
     if abs(den)<1e-12:continue
     u=((b[2]-c[2])*(x-c[0])+(c[0]-b[0])*(z-c[2]))/den;v=((c[2]-a[2])*(x-c[0])+(a[0]-c[0])*(z-c[2]))/den
     if min(u,v,1-u-v)>=-1e-6:hits.append(u*a[1]+v*b[1]+(1-u-v)*c[1])
   high=max(hits) if hits else y+.2
   return (x,max(y+.035,min(y+.18,high-.025)),z)
  for a,b in zip(perimeter,perimeter[1:]+perimeter[:1]):
   aa,bb=inside_top(a),inside_top(b)
   well.face([aa,bb,b,a],(43,51,57))
  for i in range(nx):
   for j in range(nzseg):
    poly=[inside_top(ys[i,j]),inside_top(ys[i+1,j]),inside_top(ys[i+1,j+1]),inside_top(ys[i,j+1])]
    well.face(poly,(25,31,36))
  # Hinge along outside edge. Local door geometry keeps the skin profile at the closed position.
  hz=(z0+z1)/2
  leaves=[(door,cla+3,x0 if title!='Right' else x1,-14564 if title!='Right' else 14564,'')]
  if title=='Nose':
   mid=(x0+x1)/2;leaves=[]
   for right in [False,True]:
    leaf=Mesh()
    for ids,c,b in door.f:
     poly=clip([door.v[k] for k in ids],0,mid,right)
     if len(poly)>=3:leaf.face(poly,c,b)
    original=not right
    classid=143
    leaves.append((leaf,classid,x1 if right else x0,14564 if right else -14564,'' if original else '_Second'))
  for leaf,classid,hx,angle,suffix in leaves:
   angle=int(math.copysign(6372 if title!='Nose' else 12743,angle))
   hy=sample_y(skin,hx,hz);hinge=(hx,hy if hy is not None else pivot[1]-.4,hz);hdg=pch=0
   if title!='Nose':
    # Follow the actual straight upper edge of the engine sidewall, not a remote point under the wing.
    top=[v for v in leaf.v if v[1]>-.2]
    meanz=sum(v[2] for v in top)/len(top);den=sum((v[2]-meanz)**2 for v in top)
    def fit(k):
     mean=sum(v[k] for v in top)/len(top);slope=sum((v[2]-meanz)*(v[k]-mean) for v in top)/den
     return mean+slope*(hz-meanz),slope
    xx,dx=fit(0);yy,dy=fit(1);hinge=(xx,yy,hz)
    ez=(dx,dy,1);l=math.sqrt(sum(x*x for x in ez));ez=tuple(x/l for x in ez);ex=(ez[2],0,-ez[0]);l=math.sqrt(sum(x*x for x in ex));ex=tuple(x/l for x in ex);ey=(ez[1]*ex[2],ez[2]*ex[0]-ez[0]*ex[2],-ez[1]*ex[0])
    leaf.v=[tuple(sum((v[k]-hinge[k])*axis[k] for k in range(3)) for axis in [ex,ey,ez]) for v in leaf.v]
    hdg=round(math.atan2(-ez[0],ez[2])*32768/math.pi);pch=round(math.asin(ez[1])*32768/math.pi)
   else:leaf.shift(*[-x for x in hinge])
   dfn='Door_'+title+suffix+'.srf';packs[dfn]=leaf.srf()
   new=rig_node('Door_'+title+suffix,dfn,classid,hinge,down=(0,0,0,0,0,angle))
   new=dnm.edit(new,'POS ',' '.join(map(str,hinge))+f' {hdg} {pch} 0 1');nodes.append(new)
  wfn='Bay_'+title+'.srf';packs[wfn]=well.srf();nodes.append(rig_node('Bay_'+title,wfn,151))
  stats.append(dict(leg=title,contact_y=world[1]-radius,radius=radius,pivot=pivot,world=world,rect=rect,cut_polygons=cut,up=up))
 return nodes,stats
