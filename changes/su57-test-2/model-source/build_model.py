from pathlib import Path
import math,json,copy
import numpy as np
from scipy.spatial import ConvexHull
import helpers as H
from helpers import *
from ac_reference import AC
from collision_su57 import rotation
source=AC(lab/'reference/Su-57.ac');raw={o['name']:o for o in source.objects};SX=14.10/14.02;SZ=20.10/19.67978
# Recenter and normalize lengths; retain source vertical proportions.
def cv(v):x,y,z=v;return (x*SX,y,(z-.16011)*SZ)
rawmeshes={}
for name,o in raw.items():
 m=Mesh();m.v=[cv(v) for v in o['v']];m.f=[(f,(115,145,165),False) for f in o['f'] if len(f)>=3];rawmeshes[name]=m
base=rawmeshes['Fuselage'];basepts=[]
for ids,c,b in base.f:
 p=np.array([base.v[i] for i in ids])
 for i in range(1,len(p)-1):basepts.append([p[0],p[i],p[i+1]])
tri=np.array(basepts);aa,bb,cc=tri[:,0],tri[:,1],tri[:,2];den=(bb[:,2]-cc[:,2])*(aa[:,0]-cc[:,0])+(cc[:,0]-bb[:,0])*(aa[:,2]-cc[:,2]);safe=np.where(abs(den)>1e-12,den,1.0)
def upper(x,z,_a=aa,_b=bb,_c=cc,_d=den,_s=safe):
 aa,bb,cc,den,safe=_a,_b,_c,_d,_s
 u=((bb[:,2]-cc[:,2])*(x-cc[:,0])+(cc[:,0]-bb[:,0])*(z-cc[:,2]))/safe;v=((cc[:,2]-aa[:,2])*(x-cc[:,0])+(aa[:,0]-cc[:,0])*(z-cc[:,2]))/safe;mask=(abs(den)>1e-12)&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)
 vals=u*aa[:,1]+v*bb[:,1]+(1-u-v)*cc[:,1];return float(np.max(vals[mask])) if mask.any() else .30

def painted(m):
 out=Mesh()
 for ids,c,b in m.f:
  p=[m.v[k] for k in ids];ny=normal(p)[1]
  if ny>.12:
   for i in range(1,len(p)-1):paint(out,[p[0],p[i],p[i+1]])
  else:face(out,p,(208,221,231) if sum(v[2] for v in p)/len(p)>7.95 else (104,139,163))
 return out
fixed=painted(base);coll=copy.deepcopy(base)
# Geometry parts are retained, rather than invented lofts; hinge frames are adapted to YSFlight.
controlmap={'Canard':(186,187),'Eleron':(180,181),'Flap':(182,183),'Slat':(184,185),'HStab':(190,191),'VStab':(188,189)}
controlstats=[]
for name,m0 in rawmeshes.items():
 prefix=name.split('_')[0]
 if prefix not in controlmap:continue
 m=painted(m0);vv=np.array(m0.v);sg=-1 if vv[:,0].mean()<0 else 1;label='L' if sg<0 else 'R';cla=controlmap[prefix][0 if sg<0 else 1]
 if prefix=='VStab':
  yy=vv[:,1];xx=vv[:,0];slope=float(np.linalg.lstsq(np.c_[yy,np.ones(len(yy))],xx,rcond=None)[0][0]);low=vv[yy<yy.min()+.06];pivot=np.array([low[:,0].mean(),low[:,1].mean(),(low[:,2].min()+low[:,2].max())/2]);bank=round(-math.atan(slope)*32768/math.pi);R=rotation([0,0,bank]);m.v=[tuple(R.T@(np.array(v)-pivot)) for v in m.v];a=add(prefix+'_'+label,m,cla,pivot,[(0,0,0,0,0,0,1),(0,0,0,3641,0,0,1),(0,0,0,-3641,0,0,1)]);nodes[-1]=dnm.edit(a,'POS ',' '.join(map(str,pivot))+f' 0 0 {bank} 1')
 else:
  # Fit the real hinge edge across the span instead of using unrelated body axes.
  bins=np.linspace(vv[:,0].min(),vv[:,0].max(),9);edge=[]
  for x0,x1 in zip(bins,bins[1:]):
   part=vv[(vv[:,0]>=x0-1e-5)&(vv[:,0]<=x1+1e-5)]
   if len(part):
    zz=part[:,2].min() if prefix=='Slat' else part[:,2].max();chosen=part[np.abs(part[:,2]-zz)<.025];edge.append(chosen.mean(0))
  e=np.array(edge);slope=float(np.linalg.lstsq(np.c_[e[:,0],np.ones(len(e))],e[:,2],rcond=None)[0][0]) if len(e)>1 else 0
  if prefix=='HStab':pivot=np.array([sg*2.25,.28,cv((0,0,-6.45))[2]]);slope=0
  elif prefix=='Canard':pivot=np.array([vv[:,0].mean(),.18,cv((0,0,1.9))[2]]);slope=0
  else:pivot=e.mean(0)
  heading=orient(m,pivot,[1,0,slope]);a=add(prefix+'_'+label,m,cla,pivot,[(0,0,0,0,0,0,1),(0,0,0,0,4551 if prefix=='HStab' else 5461,0,1),(0,0,0,0,-4551 if prefix=='HStab' else -5461,0,1)]);nodes[-1]=dnm.edit(a,'POS ',' '.join(map(str,pivot))+f' {heading} 0 0 1')
 coll.merge(m0);controlstats.append({'name':name,'class':cla,'pivot':pivot.tolist()})
# Exact source windscreen/canopy shapes and frames. Rear canopy rotates as one unit.
rear=Mesh()
for name in ['Canopy_Frame_F','Canopy_Glass_F','Canopy_Frame_R','Canopy_Glass_R']:
 m=rawmeshes[name];out=Mesh()
 for ids,c,b in m.f:
  p=[m.v[i] for i in ids]
  if 'Glass' in name:face(out,p,(69,108,139,145))
  else:face(out,p,(82,126,158))
 if name.endswith('_F'):fixed.merge(out)
 else:rear.merge(out)
 coll.merge(m)
hinge=np.array([0,.72,cv((0,0,4.31))[2]]);rear.shift(*(-hinge));add('Canopy',rear,100,hinge,[(0,0,0,0,0,0,1),(0,0,0,0,6372,0,1)])
# Sealed compact cockpit under the actual glass, with no floating interior blocks.
tub=Mesh();rows_tub=[(4.85,.35,.74),(5.25,.47,.72),(5.9,.50,.70),(6.5,.47,.67),(7.1,.34,.63),(7.4,.12,.58)]
for a,b in zip(rows_tub,rows_tub[1:]):
 za,wa,ya=a;zb,wb,yb=b;za=cv((0,0,za))[2];zb=cv((0,0,zb))[2]
 for sg in [-1,1]:both(tub,[(sg*wa,ya,za),(sg*wb,yb,zb),(sg*wb,.20,zb),(sg*wa,.20,za)],DARK)
 both(tub,[(-wa,.20,za),(wa,.20,za),(wb,.20,zb),(-wb,.20,zb)],DARK)
for z,w,y in [rows_tub[0],rows_tub[-1]]:z=cv((0,0,z))[2];both(tub,[(-w,.20,z),(w,.20,z),(w,y,z),(-w,y,z)],DARK)
zp=cv((0,0,5.62))[2];tub.box(0,.58,zp,.35,.18,.44,(54,68,61));tub.box(0,.84,zp-.24,.36,.48,.14,DARK);tub.box(0,1.07,zp-.23,.25,.15,.13,(42,54,59));tub.box(0,.80,zp,.29,.29,.22,(70,87,75));tub.tube((0,.96,zp),(0,1.10,zp),.09,(144,161,174),12);tub.box(0,.70,cv((0,0,6.95))[2],.55,.15,.18,DARK);add('CockpitLiner',tub)
# Close actual intake boundary loops with dark recessed ducts, not exterior cards.
from collections import Counter
edgecount=Counter()
for ids,c,b in base.f:
 points=[tuple(round(v,5) for v in base.v[k]) for k in ids]
 for a,b in zip(points,points[1:]+points[:1]):edgecount[tuple(sorted([a,b]))]+=1
graph={}
for (a,b),count in edgecount.items():
 if count==1:graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
seen=set();ducts=Mesh()
for first in graph:
 if first in seen:continue
 stack=[first];component=[]
 while stack:
  point=stack.pop()
  if point in seen:continue
  seen.add(point);component.append(point);stack.extend(graph[point]-seen)
 vv=np.array(component)
 if len(component)==3 and vv[:,2].mean()<-6 and abs(vv[:,1].mean())<.15:
  both(ducts,component,(99,140,169));continue
 if not(len(component)==10 and vv[:,1].max()<.15 and .3<vv[:,2].mean()<2.5):continue
 ordered=[first];previous=None;cur=first
 for k in range(len(component)-1):
  nxt=next(q for q in graph[cur] if q!=previous and q not in ordered);ordered.append(nxt);previous,cur=cur,nxt
 center=vv.mean(0);back=[];lip=[]
 for x,y,z in ordered:
  lip.append((center[0]+.985*(x-center[0]),center[1]+.985*(y-center[1]),z-.012));back.append((center[0]+.94*(x-center[0]),center[1]+.94*(y-center[1]),.035))
 for a,b,c,d in zip(lip,lip[1:]+lip[:1],back,back[1:]+back[:1]):both(ducts,[a,b,d,c],(26,35,44))
 bc=tuple(np.array(back).mean(0))
 for a,b in zip(back,back[1:]+back[:1]):both(ducts,[bc,a,b],(12,19,27))
add('IntakeLiners',ducts);coll.merge(ducts)

# Native vectorable nozzles match the source installation, not v1 long cylinders.
for name in ['Nozzle_Sample_L','Nozzle_Sample_R']:
 m0=rawmeshes[name];v=np.array(m0.v);sg=-1 if v[:,0].mean()<0 else 1;label='L' if sg<0 else 'R';near=v[v[:,2]>v[:,2].max()-.03];P=np.array([(v[:,0].min()+v[:,0].max())/2,(v[:,1].min()+v[:,1].max())/2,v[:,2].max()-.02]);noz=Mesh()
 for ids,c,b in m0.f:face(noz,[tuple(np.array(m0.v[k])-P) for k in ids],(109,115,120))
 zz=v[:,2].min()-P[2];tip=v[v[:,2]<v[:,2].min()+.03]-P;rad=float(np.max(np.linalg.norm(tip[:,:2],axis=1)));inner=rad*.85
 for k in range(24):
  a,b=k*math.pi/12,(k+1)*math.pi/12
  both(noz,[(rad*math.cos(a),rad*math.sin(a),zz),(rad*math.cos(b),rad*math.sin(b),zz),(inner*math.cos(b),inner*math.sin(b),zz),(inner*math.cos(a),inner*math.sin(a),zz)],(127,139,146));both(noz,[(inner*math.cos(a),inner*math.sin(a),zz),(inner*math.cos(b),inner*math.sin(b),zz),(.22*math.cos(b),.22*math.sin(b),zz+.7),(.22*math.cos(a),.22*math.sin(a),zz+.7)],(27,34,41))
 both(noz,[(.24*math.cos(k*math.pi/12),.24*math.sin(k*math.pi/12),zz+.69) for k in range(24)],(13,19,25))
 # Buried moving skirt and fixed root collar prevent daylight at vectoring extremes.
 rz=float(v[:,2].max()-P[2]);rootrad=.64;seal=Mesh()
 for k in range(24):
  a,b=k*math.pi/12,(k+1)*math.pi/12
  face(noz,[(.61*math.cos(a),.61*math.sin(a),rz+.26),(.61*math.cos(b),.61*math.sin(b),rz+.26),(rootrad*math.cos(b),rootrad*math.sin(b),rz),(rootrad*math.cos(a),rootrad*math.sin(a),rz)],(95,107,117),up=(math.cos((a+b)/2),math.sin((a+b)/2),0))
  pts=[(.675*math.cos(a),.675*math.sin(a),rz+.08),(.675*math.cos(b),.675*math.sin(b),rz+.08),(.675*math.cos(b),.675*math.sin(b),rz-.15),(.675*math.cos(a),.675*math.sin(a),rz-.15)]
  both(seal,[tuple(np.array(t)+P) for t in pts],(99,113,125))
  ring=[(.675*math.cos(a),.675*math.sin(a),rz-.15),(.675*math.cos(b),.675*math.sin(b),rz-.15),(.60*math.cos(b),.60*math.sin(b),rz-.15),(.60*math.cos(a),.60*math.sin(a),rz-.15)]
  both(seal,[tuple(np.array(t)+P) for t in ring],(87,99,109))
 both(seal,[tuple(P+np.array([.66*math.cos(k*math.pi/12),.66*math.sin(k*math.pi/12),rz+.18])) for k in range(24)],(24,32,40));add('NozzleRootSeal_'+label,seal)
 add('Nozzle_'+label,noz,192 if sg<0 else 193,P);coll.merge(m0)
 flame=Mesh()
 for (za,ra),(zb,rb),col in [((zz,.34),(zz-.4,.36),(89,135,230)),((zz-.4,.36),(zz-1.0,.2),(236,163,78)),((zz-1.0,.2),(zz-1.8,.003),(228,103,45))]:
  for k in range(16):
   a,b=k*math.pi/8,(k+1)*math.pi/8;face(flame,[(ra*math.cos(a),ra*math.sin(a),za),(ra*math.cos(b),ra*math.sin(b),za),(rb*math.cos(b),rb*math.sin(b),zb),(rb*math.cos(a),rb*math.sin(a),zb)],col,True,up=(math.cos((a+b)/2),math.sin((a+b)/2),0))
 add('Flame_'+label,flame,110 if sg<0 else 111,states=[(0,0,0,0,0,0,0),(0,0,0,0,0,0,1)],parent='Nozzle_'+label)

# Three true gear cavities. Only exterior bottom cut polygons become doors.
gearstats=[]
for title,cla,pivot,wheelcenter,radius,rect in [('Nose',140,(0,-.10,4.95),(0,-1.90,4.95),.28,(-.43,.43,4.65,7.05)),('Left',141,(-1.76,-.36,-2.55),(-2.00,-1.73,-2.30),.45,(-2.52,-1.13,-2.85,-.15)),('Right',142,(1.76,-.36,-2.55),(2.00,-1.73,-2.30),.45,(1.13,2.52,-2.85,-.15))]:
 before=copy.deepcopy(fixed);_,cut=cut_bay(fixed,rect);outer=Mesh()
 from rig import sample_y
 for ids,c,b in cut.f:
  poly=[cut.v[k] for k in ids];cx=sum(v[0] for v in poly)/len(poly);cz=sum(v[2] for v in poly)/len(poly);cy=sum(v[1] for v in poly)/len(poly);lowest=sample_y(before,cx,cz)
  if lowest is not None and cy<=lowest+.075:face(outer,poly,c)
 well=Mesh();door=Mesh();offset=.80 if title!='Nose' else .65
 for ids,c,b in outer.f:
  poly=[outer.v[k] for k in ids];roof=[]
  for x,y,z in poly:
   high=upper(x,z)
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

add('Su57Hull',fixed,0);nodes.insert(0,nodes.pop())
# Markings fitted to upper geometry, not suspended cards.
mark=Mesh()
for sg in [-1,1]:
 for rr,c,dy in [(.42,(235,241,242),.008),(.34,(183,43,50),.012)]:
  cx=sg*5.7;cz=cv((0,0,-4.20))[2];pts=[]
  for k in range(10):
   t=k*math.pi/5;r=rr*(1 if k%2==0 else .42);x=cx+r*math.sin(t);z=cz+r*math.cos(t);pts.append((x,upper(x,z)+dy,z))
  center=(cx,upper(cx,cz)+dy,cz)
  for k in range(10):face(mark,[center,pts[k],pts[(k+1)%10]],c,up=(0,1,0))
add('Stars',mark)
nav=Mesh()
for sg,col in [(-1,(223,40,35)),(1,(45,210,95))]:face(nav,[(sg*7.052,.17,-4.38),(sg*7.052,.20,-4.48),(sg*7.052,.15,-4.56)],col,True)
add('Nav',nav,30)
for f in ['su57.dnm','su57_coarse.dnm']:dnm.write(dest/f,packs,nodes)
(dest/'su57coll.srf').write_text('\n'.join(coll.srf())+'\n');(dest/'su57cockpit.srf').write_text('SURF\nE\n')
dat=(lab/'baseline_su57.dat').read_text().replace('COCKPITP 0m 1.46m 5.90m','COCKPITP 0m 1.10m 6.35m').replace('-2.0m -2.3m','-2.18m -2.3m').replace('-2.0m 4.95m','-2.18m 4.95m');(dest/'su57.dat').write_text(dat)
result={'geometry_source':'ShFsn/Su-57 Models/Su-57.ac','source_commit':'e7015f490233e78c59331f01cfbab7c5edf584b3','license':'GPL-3.0','target_length_m':20.1,'target_span_m':14.1,'gear_ground_y':-2.18,'gear':gearstats,'controls':controlstats,'nodes':len(nodes),'faces':sum(len(dnm.mesh(packs[dnm.fil(a)]).f) for a in nodes)};(lab/'model-stats.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
