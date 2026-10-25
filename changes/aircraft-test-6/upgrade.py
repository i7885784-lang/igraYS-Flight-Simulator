from pathlib import Path
import math,copy,json
import dnm
from mesh import Mesh,node
from rig import rig_node
lab=Path(__file__).resolve().parent;rt=lab/'runtime/aircraft';stats={}
def double(m,poly,c):m.face(poly,c);m.face(poly[::-1],c)
def tube(m,a,b,r,c,n=12):m.tube(a,b,r,c,n)
def close_liner(m,rows):
 # Each transverse station closes against a sealed floor and sidewall.
 for (za,wa,ya),(zb,wb,yb) in zip(rows,rows[1:]):
  fa,fb=ya-.29,yb-.29
  for sg in [-1,1]:double(m,[(sg*wa,ya,za),(sg*wb,yb,zb),(sg*wb*.7,fb,zb),(sg*wa*.7,fa,za)],(29,36,41))
  double(m,[(-wa*.7,fa,za),(wa*.7,fa,za),(wb*.7,fb,zb),(-wb*.7,fb,zb)],(25,32,37))
 for z,w,y in [rows[0],rows[-1]]:double(m,[(-w,y,z),(w,y,z),(w*.7,y-.29,z),(-w*.7,y-.29,z)],(37,44,49))
for kind in ['su27','mig29']:
 packs,nodes=dnm.read(lab.parent/'aircraft-lab5/runtime/aircraft'/(kind+'.dnm'));su=kind=='su27'
 # Rebuild cavities from EXACT removed shell polygons, extruded inward.
 # Unlike the old XZ-grid, this also seals the vertical sidewalls.
 basep,basen=dnm.read(lab.parent/'aircraft-lab2/runtime/aircraft'/f'{kind}.dnm');skin=dnm.mesh(basep[dnm.fil(basen[0])])
 if su:
  def front(v):
   x,y,z=v;f=max(0,min(1,(z-5.6)/1.1));f=f*f*(3-2*f);return x*(1-.20*f),.575+(y-.575)*(1-.17*f),z
  skin.v=[front(v) for v in skin.v]
 from gear_v3 import cut_bay
 gstats=json.loads((lab.parent/'aircraft-lab5/model-stats.json').read_text())[kind+'_gear'];seals=[]
 for cfg in gstats:
  title=cfg['leg'];dummy=copy.deepcopy(skin);_,cut=cut_bay(dummy,cfg['rect'],title!='Nose',(.22,-.59) if su else (.14,-.93));well=Mesh();sg=-1 if title=='Left' else 1
  offset=(0,.31,0) if title=='Nose' else (-sg*.30,0,0)
  for ids,c,b in cut.f:
   poly=[cut.v[i] for i in ids];inner=[tuple(v[k]+offset[k] for k in range(3)) for v in poly]
   double(well,inner,(37,43,47))
   for a,b,aa,bb in zip(poly,poly[1:]+poly[:1],inner,inner[1:]+inner[:1]):double(well,[a,b,bb,aa],(54,62,66))
  # A closed pivot block and bearing join the visible leg to the recessed structure.
  px,py,pz=cfg['pivot'];well.box(px,py+.025,pz,.26,.15,.28,(72,81,86));well.tube((px-.18,py,pz),(px+.18,py,pz),.087,(117,127,133),12)
  packs['Bay_'+title+'.srf']=well.srf();seals.append({'leg':title,'cut_faces':len(cut.f),'liner_faces':len(well.f),'inward_offset':offset})
  leg=dnm.mesh(packs['Gear_'+title+'.srf']);axle=[cfg['world'][i]-cfg['pivot'][i] for i in range(3)]
  # Upper oleo sleeve, torque link and a flexible-looking segmented brake line.
  a=tuple(v*.10 for v in axle);b=tuple(v*.58 for v in axle);leg.tube(a,b,.072 if title=='Nose' else .092,(116,130,139),12)
  for frac in [.17,.46,.57]:
   aa=tuple(v*(frac-.014) for v in axle);bb=tuple(v*(frac+.014) for v in axle);leg.tube(aa,bb,.08 if title=='Nose' else .10,(66,76,84),12)
  for sg2 in [-1,1]:
   off=.065 if title=='Nose' else .09
   points=[(axle[0]*.60+sg2*off,axle[1]*.60,axle[2]*.60),(axle[0]*.77+sg2*(off+.055),axle[1]*.77,axle[2]*.77-.06),(axle[0]*.92+sg2*off,axle[1]*.92,axle[2]*.92)]
   for aa,bb in zip(points,points[1:]):leg.tube(aa,bb,.018,(133,144,151),8)
  packs['Gear_'+title+'.srf']=leg.srf()
 stats[kind+'_sealed_bays']=seals
 if not su:
  # Seal the rear cockpit bulkhead and deep floor, preserving MiG silhouette.
  m=dnm.mesh(packs['MigDetails.srf']);sx=11.36/12.403338;sy=3.03/3.149863;sz=17.32/18.058239
  rows=[(z*sz,w*sx,y*sy) for z,w,y in [(5.89,.24,.88),(4.88,.42,.95),(4.4,.41,1.01),(3.24,.37,1.16)]];close_liner(m,rows)
  z,w,y=rows[-1];m.box(0,y-.14,z+.03,w*1.95,.30,.09,(47,58,64));packs['MigDetails.srf']=m.srf()
 else:
  # Replace canopy glass/rails and inner tub together, retaining decals and fin detail.
  m=dnm.mesh(packs['SU27_Detail.srf']);keep=[]
  for ids,c,b in m.f:
   vs=[m.v[i] for i in ids];cock=all(abs(x)<.76 and z>3 and y>.65 for x,y,z in vs) and (len(c)==4 or max(c[:3])<165)
   exhaust=all(z<-7.69 and abs(x)<2.15 for x,y,z in vs)
   if not(cock or exhaust):keep.append((ids,c,b))
  m.f=keep;can=Mesh();fixed=Mesh()
  # Rim stations follow the actual hull. Rounded bubble, sloping windscreen, single seat.
  stations=[]
  for z,w,y,top in [(6.70,.015,1.20,1.22),(6.52,.22,1.15,1.36),(5.70,.50,1.25,1.70),(5.20,.50,1.30,1.85),(4.50,.40,1.38,1.89),(4.05,.30,1.45,1.79),(3.02,.015,1.59,1.61)]:
   xx,yy,_=front((w,y,z));_,tt,_=front((0,top,z));stations.append((z,xx,yy,tt))
  def pt(st,k):
   z,w,y,top=st;t=k*math.pi/16;return w*math.cos(t),y+(top-y)*math.sin(t),z
  for i,(a,b) in enumerate(zip(stations,stations[1:])):
   out=fixed if i<2 else can
   for k in range(16):out.face([pt(b,k),pt(b,k+1),pt(a,k+1),pt(a,k)],(77,116,140,92))
   for k in [0,16]:out.tube(pt(a,k),pt(b,k),.013,(72,91,103),8)
  for idx in [2,6]:
   out=fixed if idx==2 else can
   for k in range(16):out.tube(pt(stations[idx],k),pt(stations[idx],k+1),.014,(85,104,115),8)
  # Moving leading hoop and locking feet remain part of the moving shell.
  for k in range(16):
   a=list(pt(stations[2],k));b=list(pt(stations[2],k+1));a[2]-=.017;b[2]-=.017;can.tube(a,b,.009,(51,66,77),6)
  for sg in [-1,1]:
   for z,w,y in [(4.15,.32,1.44),(5.35,.49,1.28)]:can.box(sg*w,y-.018,z,.035,.045,.08,(94,107,117))
  hinge=(0,1.59,3.02);can.shift(*[-v for v in hinge]);packs['SU27_Canopy.srf']=can.srf();m.merge(fixed)
  rows=[(z,w,y) for z,w,y,_ in stations[1:]];close_liner(m,rows)
  m.box(0,1.26,4.20,.34,.36,.13,(31,38,43));m.box(0,1.48,4.20,.24,.15,.15,(42,49,52));m.box(0,1.16,4.56,.33,.16,.42,(66,73,64));m.box(0,1.19,5.57,.64,.15,.22,(32,41,48))
  # Retain a compact helmet so the exterior still looks piloted.
  m.tube((0,1.40,4.60),(0,1.53,4.60),.09,(146,155,159),12);m.box(0,1.50,4.68,.12,.05,.025,(30,40,48))
  # Contiguous Su-specific nozzle housings, petal overlaps and hollow hot interior.
  ring=[(.70,0),(.50,.49),(0,.70),(-.49,.49),(-.70,0),(-.49,-.50),(0,-.70),(.50,-.50)]
  for cx in [-1.3,1.3]:
   def ep(z,t,r,cy):
    if z==-7.7:
     f=(t%(2*math.pi))*4/math.pi;i=int(f)%8;f-=int(f);a,b=ring[i],ring[(i+1)%8];return cx+a[0]*(1-f)+b[0]*f,a[1]*(1-f)+b[1]*f,z
    return cx+r*math.cos(t),cy+r*math.sin(t),z
   prof=[(-7.7,.70,0),(-7.96,.65,.01),(-8.26,.585,.025),(-8.82,.46,.045),(-9.15,.38,.05)]
   for j,(a,b) in enumerate(zip(prof,prof[1:])):
    for k in range(32):
     t=k*math.pi/16;u=(k+1)*math.pi/16;c=(97+k%2*6,103+k%2*6,109+k%2*6) if j<2 else (67+k%2*9,72+k%2*9,81+k%2*9)
     m.face([ep(b[0],t,b[1],b[2]),ep(b[0],u,b[1],b[2]),ep(a[0],u,a[1],a[2]),ep(a[0],t,a[1],a[2])],c)
   for k in range(32):
    t=k*math.pi/16;u=(k+1)*math.pi/16
    m.face([ep(-9.15,t,.38,.05),ep(-9.15,u,.38,.05),ep(-9.15,u,.335,.05),ep(-9.15,t,.335,.05)][::-1],(124,133,140))
    m.face([ep(-9.15,t,.335,.05),ep(-9.15,u,.335,.05),ep(-8.40,u,.26,.05),ep(-8.40,t,.26,.05)][::-1],(32,36,44))
    # Narrow longitudinal overlaps give the petals real edge depth.
    aa=ep(-8.27,t,.588,.025);bb=ep(-9.13,t,.385,.05);m.tube(aa,bb,.008,(96,103,111),6)
   double(m,[ep(-8.401,k*math.pi/16,.275,.05) for k in range(32)],(14,17,23))
  packs['SU27_Detail.srf']=m.srf()
  # Replace radome section transitions by smoothly interpolated meridians.
  from scipy.interpolate import PchipInterpolator
  old=dnm.mesh(packs['SU27_Radome.srf']);root=[old.v[k] for k in range(96)] # preserve explicit root from face positions below
  # Reuse exact original seam; only the forward meridian is changed.
  seam=[(0,1.20),(.51,.95),(.65,.40),(.43,.02),(0,-.05),(-.43,.02),(-.65,.40),(-.51,.95)]
  zs=[6.70,7.25,7.9,8.6,9.25,9.72,9.86];rx=[.52,.475,.385,.255,.125,.027,.001];ry=[.519,.45,.36,.25,.125,.035,.003];cy=[.575,.525,.43,.30,.205,.158,.15]
  fs=[PchipInterpolator(zs,v) for v in [rx,ry,cy]]
  def nose(z,k):
   k%=32;t=k*math.pi/16
   if z==6.7:
    i=k//4;f=(k%4)/4;a,b=seam[i],seam[(i+1)%8];zz=6.7+.03*((1-f)*(i in [1,7])+f*((i+1)%8 in [1,7]));return front((a[0]*(1-f)+b[0]*f,a[1]*(1-f)+b[1]*f,zz))
   rr,yy,cc=[float(f(z)) for f in fs];return rr*math.sin(t),cc+yy*math.cos(t),z
  rad=Mesh();sections=[6.7]+[6.7+(9.86-6.7)*i/14 for i in range(1,15)]
  for za,zb in zip(sections,sections[1:]):
   for k in range(32):
    # Triangles avoid twisted nonplanar quads at the octagonal joint.
    a,b,c,d=nose(za,k),nose(za,k+1),nose(zb,k+1),nose(zb,k)
    rad.face([a,c,b],(105,121,134));rad.face([a,d,c],(105,121,134))
  rad.tube((0,.15,9.86),(0,.15,10.55),.006,(82,98,110),8);packs['SU27_Radome.srf']=rad.srf()
  stats['su27_nose']={'root_width':1.04,'tip_z':9.86,'smooth_sections':15,'radial_segments':32}
  # Articulated telescopic brake actuator: exact anchors for sampled spoiler values.
  brake=next(a for a in nodes if dnm.cla(a)==4);hinge=list(map(float,next(x[4:] for x in brake if x.startswith('POS ')).split()[:3]));panel=dnm.mesh(packs[dnm.fil(brake)]);attach=(0,-.25,-1.75);anchor=(0,hinge[1]-.32,hinge[2]-.50)
  panel.box(*attach,.18,.11,.17,(86,99,108));packs[dnm.fil(brake)]=panel.srf()
  # Choose attachment from actual underside near that longitudinal location.
  for cla,name,length,radius,from_end in [(160,'BrakeCylinder',.82,.052,False),(161,'BrakePiston',1.32,.027,True)]:
   act=Mesh();act.tube((0,0,0),(0,0,length),radius,(111,126,137) if not from_end else (190,202,210),12);act.tube((0,0,-.04),(0,0,.04),radius*1.35,(80,94,106),12)
   packs[name+'.srf']=act.srf();states=[];samples=[]
   for i in range(21):
    q=i/20;theta=-10012*math.pi/32768*q;xx,yy,zz=attach;B=(hinge[0]+xx,hinge[1]+yy*math.cos(theta)+zz*math.sin(theta),hinge[2]-yy*math.sin(theta)+zz*math.cos(theta));d=tuple(B[k]-anchor[k] for k in range(3));dist=math.sqrt(sum(v*v for v in d));unit=tuple(v/dist for v in d);start=tuple(B[k]-unit[k]*length for k in range(3)) if from_end else anchor
    hdg=round(math.atan2(-unit[0],unit[2])*32768/math.pi);pch=round(math.asin(unit[1])*32768/math.pi);states.append('STA '+' '.join(map(str,start))+f' {hdg} {pch} 0 1');samples.append({'q':q,'A':anchor,'B':B,'length':dist})
   nodes.append([f'SRF "{name}"',f'FIL {name}.srf',f'CLA {cla}','NST 21']+states+['POS 0 0 0 0 0 0 1','CNT 0 0 0','PAX 1 0 0','REL DEP','NCH 0','END']);stats['brake_actuator_samples']=samples
 # Engine exhaust remains tied to the real afterburner state, never a permanent plume.
 for a in nodes:
  if dnm.cla(a) not in [110,111]:continue
  flame=Mesh();scale=1.0 if su else .88
  for j,((za,ra),(zb,rb)) in enumerate(zip([(0,.30),(-.34,.32),(-.86,.20)], [(-.34,.32),(-.86,.20),(-1.65,.005)])):
   for k in range(16):
    t=k*math.pi/8;u=(k+1)*math.pi/8
    pts=[(ra*math.cos(t)*scale,ra*math.sin(t)*scale,za*scale),(ra*math.cos(u)*scale,ra*math.sin(u)*scale,za*scale),(rb*math.cos(u)*scale,rb*math.sin(u)*scale,zb*scale),(rb*math.cos(t)*scale,rb*math.sin(t)*scale,zb*scale)]
    flame.face(pts,(100,145,239) if j==0 else ((238,146,65) if j==1 else (236,91,37)),True)
  packs[dnm.fil(a)]=flame.srf()
 for a in nodes:
  if dnm.cla(a) not in [2,30,31,32,33,34,35,110,111]:packs[dnm.fil(a)]=[v for v in packs[dnm.fil(a)] if v!='B']
 dnm.write(rt/(kind+'.dnm'),packs,nodes);dnm.write(rt/('su27coarse.dnm' if su else 'mig29_coarse.dnm'),packs,nodes)
(lab/'upgrade-stats.json').write_text(json.dumps(stats,indent=2));print('Lab6 upgraded models')
