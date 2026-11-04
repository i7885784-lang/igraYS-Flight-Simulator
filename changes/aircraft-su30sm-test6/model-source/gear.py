from pathlib import Path
import numpy as np,math,json,collections
from scipy.spatial.transform import Rotation
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
from scipy.spatial import Delaunay
from common import Mesh,state,add,dnm,transform
from envelope import Envelope
r=Path(__file__).resolve().parent.parent
METAL=(163,175,184);DARK=(53,63,70);TYRE=(30,33,36)
def clip(poly,axis,t,positive):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  a=np.array(a);b=np.array(b);va=(a[axis]-t)*(1 if positive else -1);vb=(b[axis]-t)*(1 if positive else -1)
  if va>=-1e-10:out.append(a)
  if (va>=0)!=(vb>=0):out.append(a+(b-a)*(-va/(vb-va)))
 return out
def area(poly):
 q=np.array(poly);return float(np.linalg.norm(np.sum(np.cross(q,np.roll(q,-1,axis=0)),axis=0))*.5) if len(q)>=3 else 0

def face_normals(m,poly,color,bright,tri,normals):
 q=np.array(poly);tri=np.array(tri);normals=np.array(normals);a,b,c=tri[:3];e=b-a;f=c-a;d00=e@e;d01=e@f;d11=f@f;den=d00*d11-d01*d01
 if abs(den)>1e-18:
  delta=q-a;u=(d11*(delta@e)-d01*(delta@f))/den;v=(d00*(delta@f)-d01*(delta@e))/den;ns=(1-u-v)[:,None]*normals[0]+u[:,None]*normals[1]+v[:,None]*normals[2]
 else:ns=np.repeat(normals[:1],len(q),axis=0)
 ns/=np.maximum(np.linalg.norm(ns,axis=1,keepdims=True),1e-15)
 if not hasattr(m,'normals'):m.normals=[]
 m.face(q,color,bright);m.normals.extend(map(tuple,ns))

def pose_axis_y(a,b):
 a=np.array(a);b=np.array(b);y=b-a;y/=np.linalg.norm(y);helper=np.array([1.,0,0]) if abs(y[0])<.9 else np.array([0,0,1.]);z=np.cross(helper,y);z/=np.linalg.norm(z);x=np.cross(y,z);return np.c_[x,y,z]
def torus(r,width):
 m=Mesh();N=40;profile=[(-width*.43,r*.64),(-width*.52,r*.82),(-width*.38,r*.97),(-width*.18,r),(width*.18,r),(width*.38,r*.97),(width*.52,r*.82),(width*.43,r*.64)]
 for (xa,ra),(xb,rb) in zip(profile,profile[1:]+profile[:1]):
  for i in range(N):
   a,b=2*math.pi*i/N,2*math.pi*(i+1)/N;m.face([(xa,ra*math.cos(a),ra*math.sin(a)),(xb,rb*math.cos(a),rb*math.sin(a)),(xb,rb*math.cos(b),rb*math.sin(b)),(xa,ra*math.cos(b),ra*math.sin(b))],TYRE)
 # fine tread grooves represented by alternating narrow dark strips, no floating bands.
 for i in range(N):
  a,b=2*math.pi*(i+.05)/N,2*math.pi*(i+.18)/N;m.face([(-width*.18,r*math.cos(a),r*math.sin(a)),(width*.18,r*math.cos(a),r*math.sin(a)),(width*.18,r*math.cos(b),r*math.sin(b)),(-width*.18,r*math.cos(b),r*math.sin(b))],(21,24,27))
 return m
def disk_hub(radius,width):
 m=Mesh();m.tube((-width*.44,0,0),(width*.44,0,0),radius*.63,(69,95,76),32)
 for sg in [-1,1]:
  m.tube((sg*width*.445,0,0),(sg*(width*.445+.018),0,0),radius*.25,METAL,24)
  for k in range(8):
   a=k*math.pi/4;y,z=radius*.43*math.cos(a),radius*.43*math.sin(a);m.tube((sg*width*.447,y,z),(sg*(width*.447+.009),y,z),.013,(179,184,180),8)
 return m

def build():
 p,ns=dnm.read(r/'source-stage.dnm');meta=json.loads((r/'conversion.json').read_text());lu={dnm.name(n):n for n in ns};body=[];skinparts=[]
 # Correct the source demo axes for native control conventions. Keep paired ailerons differential.
 for node in ns:
  name=dnm.name(node);cla=dnm.cla(node);pos=np.array(next(s[4:] for s in node if s.startswith('POS ')).split()[:3],float)
  invert=cla in [211,5] or (cla==6 and name.startswith('Front_Stabilizers')) or (cla==7 and pos[0]<0)
  if invert:
   indices=[i for i,line in enumerate(node) if line.startswith('STA ')]
   replacements=[state(R.T,t) for R,t in [transform(node,k) for k in range(len(indices))]]
   for i,new in zip(indices,replacements):node[i]=new

 for i in [4,5,6,30,31]:
  info=next(v for v in meta['components'] if v['node']==i);n=lu[info['name']];m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v)+np.array(info['pivot']);body.append({'v':v,'f':[ids for ids,c,b in m.f[:info['triangles']]]})
  if i in [4,5]:
   vn=[list(map(float,line.split()[5:8])) for line in p[dnm.fil(n)] if line.startswith('V ') and len(line.split())>=8 and line.split()[4]=='R'];assert len(vn)==len(m.v),'Imported vertex normals missing';skinparts.append((n,m,v,info,np.array(vn)))
 env=Envelope(body,step=.018);configs=[{'name':'Nose','rect':[-.38,.38,1.99,4.16],'P':[0,.05,2.17],'C':[0,-2.22,2.77],'radius':.30,'width':.17}]
 for sg,side in [(-1,'Left'),(1,'Right')]:configs.append({'name':side,'sg':sg,'rect':[1.03 if sg>0 else -2.40,2.40 if sg>0 else -1.03,-3.38,-.41],'P':[sg*2.05,-.02,-3.18],'C':[sg*2.05,-2.06,-2.80],'radius':.46,'width':.22})
 cutmeshes={q['name']:Mesh() for q in configs};conservation=[]
 for n,m,v,info,vn in skinparts:
  result=Mesh();before=after=0.
  for ids,c,b in m.f[:info['triangles']]:
   poly=[v[i] for i in ids];original_tri=np.array(poly);original_normals=vn[ids];before+=area(poly);todo=[poly]
   for cfg in configs:
    nxt=[];x0,x1,z0,z1=cfg['rect']
    for q in todo:
     q=np.array(q);norm=np.cross(q[1]-q[0],q[2]-q[0]);nn=np.linalg.norm(norm)
     if nn<1e-14 or abs(norm[1])<nn*.08 or q[:,0].max()<=x0 or q[:,0].min()>=x1 or q[:,2].max()<=z0 or q[:,2].min()>=z1:nxt.append(list(q));continue
     candidate=list(q)
     for axis,t,positive in [(0,x0,True),(0,x1,False),(2,z0,True),(2,z1,False)]:
      candidate=clip(candidate,axis,t,positive) if len(candidate)>=3 else []
     if len(candidate)<3:nxt.append(list(q));continue
     cen=np.mean(candidate,axis=0);low=env.bounds([cen])[0][0]
     if cen[1]>low+.045:nxt.append(list(q));continue
     inside=list(q)
     for axis,t,positive in [(0,x0,True),(0,x1,False),(2,z0,True),(2,z1,False)]:
      outside=clip(inside,axis,t,not positive) if len(inside)>=3 else []
      if len(outside)>=3:nxt.append(outside)
      inside=clip(inside,axis,t,positive) if len(inside)>=3 else []
     if len(inside)>=3:face_normals(cutmeshes[cfg['name']],inside,c,b,original_tri,original_normals);after+=area(inside)
    todo=nxt
   for q in todo:face_normals(result,q,c,b,original_tri,original_normals);after+=area(q)
  conservation.append({'component':info['name'],'source_area':before,'retained_skin_plus_doors_area':after,'relative_error':abs(after-before)/before})
  # double-sided render, re-use indices for reversed faces.
  result.v=[tuple(np.array(v)-np.array(info['pivot'])) for v in result.v];result.f += [(ids[::-1],c,b) for ids,c,b in list(result.f)];p[dnm.fil(n)]=result.srf()
 gear_info=[]
 def dynamic(name,m,poses,parent=None,cla=210):
  n=add(p,ns,name,m,cla,[state(R,t) for R,t in poses])
  if parent:
   pn=next(n for n in ns if dnm.name(n)==parent);pn[:]=dnm.edit(pn,'NCH ','1');pn.insert(-1,'CLD "'+name+'"')
  return n
 for cfg in configs:
  title=cfg['name'];sg=cfg.get('sg',1);P=np.array(cfg['P'],float);Cdown=np.array(cfg['C'],float);main=title!='Nose';posesC=[];posesR=[];As=[];struts=[];radii=cfg['radius'];width=cfg['width']
  A_down=Cdown+np.array([sg*.23,0,0]) if main else Cdown;length=np.linalg.norm(A_down-P)
  for g in np.linspace(0,1,101):
   leg=np.clip((g-.20)/.72,0,1)
   if main:
    s=np.clip(leg/.35,0,1);s=s*s*(3-2*s);angle=math.radians(145.4964857469*(1-s))*sg;R=Rotation.from_rotvec([0,0,angle]).as_matrix();x=sg*(1.4035673637+(2.05-1.4035673637)*s);y=-0.2614500118+(-.85-(-0.2614500118))*s
    if leg>.35:t=(leg-.35)/.65;y=-.85+(Cdown[1]+.85)*t
    axleOffset=R@np.array([sg*.23,0,0]);ax=x+axleOffset[0];ay=y+axleOffset[1];zz=length*length-(ax-P[0])**2-(ay-P[1])**2;assert zz>0;C=np.array([x,y,P[2]+math.sqrt(zz)]);A=C+axleOffset
   else:R=Rotation.from_rotvec([-math.pi/2*(1-leg),0,0]).as_matrix();C=P+R@(Cdown-P);A=C
   posesC.append((R,C));posesR.append(R);As.append(A);struts.append((pose_axis_y(P,A),P.copy()))
  # fixed bearing stays under the existing skin.
  mount=Mesh();mount.tube((P[0]-.13,P[1],P[2]),(P[0]+.13,P[1],P[2]),.085,METAL,16);add(p,ns,'GearBearing_'+title,mount)
  upper=Mesh();upper.tube((0,0,0),(0,1.40 if main else 1.50,0),.055 if main else .062,METAL,20)
  upper.tube((0,.10,0),(0,.22,0),.10 if main else .083,(93,108,116),20)
  dynamic('GearUpper_'+title,upper,struts)
  piston=Mesh();piston.tube((0,0,0),(0,1.40,0),.038 if main else .040,(211,218,218),20)
  pistonPoses=[(R,A-R[:,1]*1.40) for (R,P0),A in zip(struts,As)];dynamic('GearPiston_'+title,piston,pistonPoses)
  axle=Mesh()
  if main:axle.tube((-sg*.12,0,0),(sg*.25,0,0),.052,METAL,20)
  else:
   axle.tube((-.355,0,0),(.355,0,0),.055,METAL,20)
   for sign in [-1,1]:axle.tube((sign*.325,0,0),(sign*.325,.36,-.081),.032,METAL,12)
   axle.tube((-.325,.36,-.081),(.325,.36,-.081),.032,METAL,12)
  dynamic('GearAxle_'+title,axle,posesC)
  # Articulated drag brace and oleo torque links; endpoints share the leg motion.
  for label,pa,pb,rad in [('TorqueUpper',.52,.66,.024),('TorqueLower',.66,.80,.024)]:
   poses=[]
   for A in As:
    v=A-P;Q=P+v*pa;T=P+v*pb;side=pose_axis_y(P,A)[:,2]*(.13 if main else -.10)
    if label=='TorqueUpper':T=T+side
    else:Q=Q+side
    poses.append((Q,T))
   length0=np.linalg.norm(poses[-1][1]-poses[-1][0]);bar=Mesh();bar.tube((0,0,0),(0,length0,0),rad,METAL,12)
   dynamic('GearLink_'+label+'_'+title,bar,[(pose_axis_y(Q,T),Q) for Q,T in poses])
  # Independently posed wheel, with native rolling under a sampled carrier.
  carrier=dynamic('WheelCarrier_'+title,Mesh(),posesC)
  tire=Mesh();hub=Mesh()
  for xx in ([0] if main else [-.18,.18]):
   t=torus(radii,width);t.shift(xx,0,0);tire.merge(t);h=disk_hub(radii,width);h.shift(xx,0,0);hub.merge(h)
  spin=add(p,ns,'Wheel_'+title,tire,146);hubn=add(p,ns,'WheelHub_'+title,hub,146);carrier[:]=dnm.edit(carrier,'NCH ','2');carrier.insert(-1,'CLD "Wheel_'+title+'"');carrier.insert(-1,'CLD "WheelHub_'+title+'"')
  # Match the exact removed lower skin; each bay has two independently hinged leaves.
  cut=cutmeshes[title];assert len(cut.f)>0,title;mid=(cfg['rect'][0]+cfg['rect'][1])/2;fairing_drop=0.
  for right in ([sg>0] if main else [False,True]):
   leaf=Mesh()
   for ids,c,b in cut.f:
    q=[cut.v[i] for i in ids] if main else clip([cut.v[i] for i in ids],0,mid,right)
    if len(q)>=3:face_normals(leaf,q,c,b,[cut.v[i] for i in ids[:3]],[cut.normals[i] for i in ids[:3]])
   if not leaf.f:continue
   vv=np.array(leaf.v);hx=cfg['rect'][1] if right else cfg['rect'][0];edge=vv[abs(vv[:,0]-hx)<1e-5]
   if len(edge)<2:edge=vv[np.argsort(abs(vv[:,0]-hx))[:max(2,len(vv)//10)]]
   pivot=edge.mean(0);_,_,V=np.linalg.svd(edge-pivot,full_matrices=False);axis=V[0];axis*=1 if axis[2]>0 else -1;side=np.cross(axis,vv.mean(0)-pivot)[1];sign=-1 if side>0 else 1;original=list(leaf.f);N=len(leaf.v);edge_counts=collections.Counter();edge_ids={}
   for ids,c,b in original:
    for ia,ib in zip(ids,ids[1:]+ids[:1]):
     key=tuple(sorted([tuple(np.round(vv[ia],6)),tuple(np.round(vv[ib],6))]));edge_counts[key]+=1;edge_ids[key]=(ia,ib)
   leaf.v=[tuple(q-pivot) for q in vv]+[tuple(q-pivot+np.array([0,.008,0])) for q in vv];leaf.normals+= [tuple(-np.array(n)) for n in list(leaf.normals)];leaf.f += [([i+N for i in ids[::-1]],(77,92,101),False) for ids,c,b in original]
   for key,count in edge_counts.items():
    if count==1:
     ia,ib=edge_ids[key];q=np.array([leaf.v[i] for i in [ia,ib,ib+N,ia+N]]);normal=np.cross(q[1]-q[0],q[2]-q[0]);normal/=max(np.linalg.norm(normal),1e-15);leaf.face(q,(91,108,120));leaf.normals.extend([tuple(normal)]*4);ids=leaf.f[-1][0];leaf.f.append((ids[::-1],(91,108,120),False))
   doorPoses=[]
   for g in np.linspace(0,1,101):
    u=np.clip((g-.02)/.15,0,1);u=u*u*(3-2*u);R=Rotation.from_rotvec(axis*math.radians(82 if main else 100)*sign*u).as_matrix();drop=.070*min(1,g/.015);doorPoses.append((R,pivot+np.array([0,-drop-fairing_drop,0])))
   dynamic('GearDoor_'+title+('_Outer' if right else '_Inner'),leaf,doorPoses)
  # Build real enclosure from the aperture's actual boundary, not a rectangular exterior box.
  polys=[Polygon(np.array([cut.v[i] for i in ids])[:,[0,2]]) for ids,c,b in cut.f if area([cut.v[i] for i in ids])>1e-9];shape=unary_union([p for p in polys if p.is_valid and p.area>1e-9]).buffer(.00001).buffer(-.00001);well=Mesh();regions=list(shape.geoms) if hasattr(shape,'geoms') else [shape]
  print('APERTURE',title,'regions',len(regions),'holes',sum(len(q.interiors) for q in regions),flush=True)
  cut_tri=np.array([[cut.v[ids[0]],cut.v[ids[k]],cut.v[ids[k+1]]] for ids,c,b in cut.f for k in range(1,len(ids)-1)])
  ca=cut_tri[:,0];ce=cut_tri[:,1]-ca;cf=cut_tri[:,2]-ca;cdet=ce[:,0]*cf[:,2]-cf[:,0]*ce[:,2]
  def lower_skin_height(x,z):
   u=np.divide((x-ca[:,0])*cf[:,2]-(z-ca[:,2])*cf[:,0],cdet,out=np.zeros(len(cdet)),where=abs(cdet)>1e-12)
   v=np.divide(ce[:,0]*(z-ca[:,2])-ce[:,2]*(x-ca[:,0]),cdet,out=np.zeros(len(cdet)),where=abs(cdet)>1e-12)
   valid=(abs(cdet)>1e-12)&(u>=-.001)&(v>=-.001)&(u+v<=1.001)
   if valid.any():return float(np.min(ca[valid,1]+u[valid]*ce[valid,1]+v[valid]*cf[valid,1]))
   raise ValueError('Aperture boundary has no source skin height: '+str((title,x,z)))
  for poly in regions:
   poly=Polygon(poly.exterior);rings=[poly.exterior]
   for ring in rings:
    rawcoords=np.array(ring.coords);outline=[];cut_xz=np.array(cut.v)[:,[0,2]]
    # Projected unions remove collinear vertices; restore every original height break along edges.
    for ea,eb in zip(rawcoords[:-1],rawcoords[1:]):
     delta=eb-ea;length2=delta@delta
     if length2<1e-16:continue
     tt=(cut_xz-ea)@delta/length2;near=np.linalg.norm(cut_xz-ea-tt[:,None]*delta,axis=1)<.00003
     ts=np.unique(np.r_[np.linspace(0,1,max(2,int(math.sqrt(length2)/.035)+2)),np.clip(tt[near&(tt>=0)&(tt<=1)],0,1)])
     outline.extend(ea+t*delta for t in ts[:-1])
    coords=np.array(outline+[outline[0]])
    for a,b in zip(coords[:-1],coords[1:]):
     qa=np.array([a[0],0,a[1]]);qb=np.array([b[0],0,b[1]]);low,high,_=env.bounds([qa,qb]);qa[1]=lower_skin_height(a[0],a[1])+.001;qb[1]=lower_skin_height(b[0],b[1])+.001
     oa=qa.copy();ob=qb.copy();qa[1]-=fairing_drop;qb[1]-=fairing_drop;fa=qa.copy();fb=qb.copy()
     # Keep the fixed enclosure behind a 20 mm seating lip, away from moving panel edges.
     center_xz=np.array(poly.centroid.coords[0])
     for point in [qa,qb]:
      away=point[[0,2]]-center_xz;away/=max(np.linalg.norm(away),1e-12);point[[0,2]]+=away*.020
     if fairing_drop:
      well.face([oa,ob,qb,qa],(30,49,72));well.face([qa,qb,ob,oa],(30,49,72))
     lip=[q.copy() for q in [fa,fb,qb,qa]]
     if main:
      for q in lip:q[1]+=.004
     well.face(lip,DARK);well.face(lip[::-1],DARK)
     ta=qa.copy();tb=qb.copy()
     # The wheel well widens above the inboard lip to contain the horizontal wheel.
     if main:
      inner=cfg['rect'][0] if sg>0 else cfg['rect'][1]
      if abs(a[0]-inner)<.01:ta[0]-=sg*.43
      if abs(b[0]-inner)<.01:tb[0]-=sg*.43
     top=env.bounds([ta,tb])[1];ta[1]=top[0]-.012;tb[1]=top[1]-.012
     well.face([qa,qb,tb,ta],DARK);well.face([ta,tb,qb,qa],DARK)
   # Sampled roof; preserve the original upper skin above it.
   pts=np.array([[x,z] for x in np.arange(poly.bounds[0],poly.bounds[2]+.04,.10) for z in np.arange(poly.bounds[1],poly.bounds[3]+.04,.10) if poly.covers(Point(x,z))]+list(poly.exterior.coords)[:-1])
   if len(pts)>=3:
    yy=env.bounds(np.c_[pts[:,0],np.zeros(len(pts)),pts[:,1]])[1]-.012
    for ids in Delaunay(pts).simplices:
     if poly.buffer(.0001).covers(Polygon(pts[ids])):
      q=np.c_[pts[ids,0],yy[ids],pts[ids,1]];well.face(q,DARK);well.face(q[::-1],DARK)
  add(p,ns,'GearWell_'+title,well)
  gear_info.append({**cfg,'length':length,'closed_center':posesC[0][1].tolist(),'closed_R':posesC[0][0].tolist(),'cut_faces':len(cut.f)})
 for name in ['su30sm.dnm','su30sm_coarse.dnm']:dnm.write(r/'runtime/aircraft'/name,p,ns)
 (r/'gear.json').write_text(json.dumps({'gear':gear_info,'skin_area_conservation':conservation},indent=2));print('BUILT GEARS',[(q['name'],q['closed_center']) for q in gear_info],flush=True)
if __name__=='__main__':build()
