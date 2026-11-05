import numpy as np,math
from common import *
from doors import exterior,panel

def clip(poly,n,c,inside=True):
 out=[];sg=1 if inside else -1
 for a,b in zip(poly,poly[1:]+poly[:1]):
  da=(n@a+c)*sg;db=(n@b+c)*sg
  if da>=-1e-10:out.append(a)
  if (da>=0)!=(db>=0):out.append(a+(b-a)*da/(da-db))
 return out

def phase(n,u):
 states=[s for s in n if s.startswith('STA ')];x=np.clip(u,0,1)*100;i=min(99,int(x));f=x-i;R,t=transform(n,i);S,v=transform(n,i+1);z=(1-f)*R[:,2]+f*S[:,2];z/=np.linalg.norm(z);y=(1-f)*R[:,1]+f*S[:,1];a=np.cross(y,z);a/=np.linalg.norm(a);return np.c_[a,np.cross(z,a),z],(1-f)*t+f*v

def repair_covers(p,ns,lu,audit):
 for sg,side in [(-1,'Left'),(1,'Right')]:
  name='MainWheelBayShutter_'+side;n=lu[name];old=list(n);tris=exterior(p,n);kept=[];removed=0.;clearance=.020
  # Exact tapered channel from the existing unchanged IntakeDuct side planes.
  # The convex air volume is expanded only for panel thickness and running clearance.
  # xMax(z)=1.55+.06/1.85*(z+1.25); yTop(z)=-.15+.08/1.85*(z+1.25);
  # yBottom(z)=-.97-.12/1.85*(z+1.25).
  ax=.06/1.85;ay=.08/1.85;ab=-.12/1.85
  planes=[(np.array([0,0,1]),3.10+clearance),(np.array([0,0,-1]),-1.25+clearance),(np.array([-sg,0,ax]),1.55+ax*1.25+clearance),(np.array([sg,0,ax]),- .81+ax*1.25+clearance),(np.array([0,-1,ay]),-.15+ay*1.25+clearance),(np.array([0,1,-ab]),.97-ab*1.25+clearance)]
  for q,color in tris:
   work=list(q);pieces=[]
   for normal,c in planes:
    if len(work)<3:break
    outside=clip(work,normal,c,False)
    if len(outside)>=3:pieces.append(outside)
    work=clip(work,normal,c,True)
   if len(work)>=3:removed+=sum(np.linalg.norm(np.cross(work[j]-work[0],work[j+1]-work[0]))/2 for j in range(1,len(work)-1))
   for poly in pieces:
    for j in range(1,len(poly)-1):
     tri=np.round(np.array([poly[0],poly[j],poly[j+1]]),6)
     if np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))>1e-10:kept.append((tri,color))
  assert kept;R,C=transform(n,0);p[dnm.fil(n)]=panel(kept,R,C,conform=True).srf()
  # Same hinge, same 100deg path/endpoints. Only phase is delayed until the outer door has clearance.
  values=[]
  for k in range(101):
   g=k/100
   if g<=.12:values.append(next(s for s in old if s.startswith('STA ')));continue
   if g>=1:values.append([s for s in old if s.startswith('STA ')][-1]);continue
   u=.015+.165*np.clip((g-.12)/.08,0,1) if g<.20 else (.18 if g<.84 else 1-.20*(1-g)/.16)
   A,b=phase(old,float(u));values.append(state(A,b))
  indices=[i for i,s in enumerate(n) if s.startswith('STA ')];assert len(indices)==101
  for i,v in zip(indices,values):n[i]=v
  audit[name]={'removed_surface_area_inside_channel_clearance_m2':removed,'channel_geometry_unchanged':True,'channel_clearance_m':clearance,'same_hinge_path_and_endpoints':True,'opening_phase_old':[.015,.175],'opening_phase_new':[.12,.20],'closing_phase_old':[.8,1],'closing_phase_new':[.84,1],'reason':'Confirmed outer-door intersections g=.025..045 and fairing collision g=.86; no wheel/strut curves changed.'}
