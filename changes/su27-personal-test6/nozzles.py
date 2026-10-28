"""Own untextured nozzle internals; source-based dimensions, existing states kept."""
from pathlib import Path
import sys,math,json,shutil
import numpy as np
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root/'model-source'));import dnm
from mesh import Mesh,node
from gear_v3 import clip
rt=root/'runtime/aircraft';base=root/'baseline';report={}
def double(m):
 for ids,c,b in list(m.f):m.face([m.v[i] for i in ids[::-1]],c,b)
 return m
def point(x,y,z,rx,ry,a):return (x+rx*math.cos(a),y+ry*math.sin(a),z)
def chamber(x,y,z,rx,ry,length):
 m=Mesh();N=24
 # Recessed convergent inner liner and longitudinal ribs. No disk at the mouth.
 for i in range(N):
  a,b=2*math.pi*i/N,2*math.pi*(i+1)/N
  for j,(za,zb,ra,rb) in enumerate([(z,z+length*.45,.96,.88),(z+length*.45,z+length,.88,.80)]):
   m.face([point(x,y,za,rx*ra,ry*ra,a),point(x,y,za,rx*ra,ry*ra,b),point(x,y,zb,rx*rb,ry*rb,b),point(x,y,zb,rx*rb,ry*rb,a)],(47+i%2*9,51+i%2*8,57+i%2*8))
  for depth in [.32,.65,.94]:
   zz=z+length*depth;r=.96-.16*depth
   m.face([point(x,y,zz,rx*r,ry*r,a),point(x,y,zz,rx*r,ry*r,b),point(x,y,zz+.018,rx*(r-.025),ry*(r-.025),b),point(x,y,zz+.018,rx*(r-.025),ry*(r-.025),a)],(77,72,66))
  # A deep flameholder ring rather than a flat black end cap.
  a,b=2*math.pi*i/N,2*math.pi*(i+1)/N
  m.face([point(x,y,z+length,rx*.80,ry*.80,a),point(x,y,z+length,rx*.80,ry*.80,b),point(x,y,z+length+.012,rx*.60,ry*.60,b),point(x,y,z+length+.012,rx*.60,ry*.60,a)],(69+i%2*8,63+i%2*6,59+i%2*6))
  m.face([(x,y,z+length+.18),point(x,y,z+length+.18,rx*.80,ry*.80,b),point(x,y,z+length+.18,rx*.80,ry*.80,a)],(22,25,29))
 return double(m)
def petal_shell(x,y,zfront,zback,rx,ry,endrx,endry):
 m=Mesh();N=24
 for k in range(N):
  a,b=2*math.pi*k/N,2*math.pi*(k+1)/N
  # Three axial bands, with narrow overlapping edge strips.
  for j,(t0,t1) in enumerate([(0,.20),(.20,.78),(.78,1)]):
   def ring(t,aa):return point(x,y,zfront+(zback-zfront)*t,rx+(endrx-rx)*t,ry+(endry-ry)*t,aa)
   shade=[(116,119,122),(101,105,112),(83,88,96)][j];c=tuple(v+(k%2)*7 for v in shade)
   m.face([ring(t0,a),ring(t0,b),ring(t1,b),ring(t1,a)],c)
   m.face([ring(t0,b-.016),ring(t0,b),ring(t1,b),ring(t1,b-.016)],(69,75,84))
  # Finite exit lip joins the external petals to the inner liner.
  m.face([point(x,y,zback,endrx,endry,a),point(x,y,zback,endrx,endry,b),point(x,y,zback+.012,endrx*.96,endry*.96,b),point(x,y,zback+.012,endrx*.96,endry*.96,a)],(128,125,121))
 return double(m)
def flame(x,y,z,rx,ry,length=1.65):
 m=Mesh();N=20
 for j,(t0,t1,r0,r1,c) in enumerate([(0,.28,.67,.54,(116,139,230)),(.28,.68,.54,.32,(227,167,99)),(.68,1,.32,.025,(239,119,55))]):
  for i in range(N):
   a,b=2*math.pi*i/N,2*math.pi*(i+1)/N
   m.face([point(x,y,z-length*t0,rx*r0,ry*r0,a),point(x,y,z-length*t0,rx*r0,ry*r0,b),point(x,y,z-length*t1,rx*r1,ry*r1,b),point(x,y,z-length*t1,rx*r1,ry*r1,a)],c,True)
 return double(m)
for kind in ['su27']:
 f=rt/(kind+'.dnm')
 # Su-27 comes from the fresh gear repair, other originals are kept independently.
 if kind!='su27':
  if not (base/f.name).exists():shutil.copy2(f,base/f.name)
  fbase=base/f.name
 else:fbase=f
 if kind=='su34' and __import__('os').environ.get('SU34_CANDIDATE_PATH'):fbase=Path(__import__('os').environ['SU34_CANDIDATE_PATH'])
 packs,ns=dnm.read(fbase);lookup={dnm.name(n):n for n in ns};added=[];removed=[]
 def add(name,m,cla=99,states=None,parent=None):
  fn=name+'.srf';packs[fn]=m.srf();n=node(name,fn,cla)
  if states:
   i=n.index('NST 1');j=n.index('POS 0 0 0 0 0 0 1');n[i:j]=['NST '+str(len(states))]+states
  ns.append(n);added.append(name)
  if parent:
   p=lookup[parent];i=next(i for i,s in enumerate(p) if s.startswith('NCH '));p[i]='NCH '+str(int(p[i].split()[1])+1);p.insert(i+1,'CLD "'+name+'"')
 def remove(names):
  global ns
  removed.extend(names);ns=[n for n in ns if dnm.name(n) not in names]
 if kind=='su27':
  remove(['EngineBlocks','Exhaust0','Exhaust1','Afterburner0','Afterburner1'])
  hull=dnm.mesh(packs['Hull.srf']);out=Mesh()
  # The original source already had shells extending to -9.192m. The old own
  # exhaust was placed at -8.32, behind an opaque source engine cap.
  for ids,c,b in hull.f:
   polys=[[hull.v[i] for i in ids]]
   for sg in [-1,1]:
    x0,x1=(.64,1.89) if sg>0 else(-1.89,-.64);kept=[]
    for q in polys:
     rest=q
     for ax,t,pos in [(0,x0,True),(0,x1,False),(1,-.85,True),(1,.44,False),(2,-8.625,False)]:
      outer=clip(rest,ax,t,not pos) if len(rest)>=3 else []
      if len(outer)>=3:kept.append(outer)
      rest=clip(rest,ax,t,pos) if len(rest)>=3 else []
    polys=kept
   for q in polys:
    if len(q)>=3:out.face(q,c,b)
  packs['Hull.srf']=out.srf()
  for i,sg in enumerate([-1,1]):
   x,y,z=sg*1.2627,-.1908,-9.1922
   add('OwnPetalNozzle'+str(i),petal_shell(x,y,-8.61,z,.601,.562,.548,.513))
   add('OwnNozzleChamber'+str(i),chamber(x,y,z+.012,.548,.513,1.05))
   add('Afterburner'+str(i),flame(x,y,z-.02,.548,.513),110+i,['STA 0 0 0 0 0 0 0','STA 0 0 0 0 0 0 1'])
 elif kind=='mig29':
  # Keep the selected editable source petals and their exact outer contour.
  remove(['Exhaust0','Exhaust1','Afterburner0','Afterburner1'])
  for i,sg in enumerate([-1,1]):
   x,y,z=sg*.957,-.176,-6.645
   add('OwnNozzleChamber'+str(i),chamber(x,y,z+.012,.43,.43,1.05))
   add('Afterburner'+str(i),flame(x,y,z-.02,.43,.43),110+i,['STA 0 0 0 0 0 0 0','STA 0 0 0 0 0 0 1'])
 elif kind=='su47':
  # Preserve both the original outer petal poses and throttle binding.
  for s in ['L','R']:
   n=lookup['NozzleInterior'+s];m=dnm.mesh(packs[dnm.fil(n)]);vv=np.array(m.v);x,y=(vv[:,:2].min(0)+vv[:,:2].max(0))/2;z=vv[:,2].min();rx,ry=np.ptp(vv[:,:2],axis=0)/2
   packs[dnm.fil(n)]=chamber(x,y,z+.03,rx*.82,ry*.82,1.15).srf()
   # Petals keep their finite thickness; improve their untextured metal finish.
   for name,pn in lookup.items():
    if name.startswith('NozzlePetal'+s):
     pm=dnm.mesh(packs[dnm.fil(pn)]);pm.f=[(ids,(111,116,123) if j==0 else c,b) for j,(ids,c,b) in enumerate(pm.f)];packs[dnm.fil(pn)]=pm.srf()
   fn=lookup['Afterburner'+s];packs[dnm.fil(fn)]=flame(x,y,z-.02,rx,ry).srf()
 elif kind=='su57':
  # Retain the Su-57's different source shape and existing thrust-vectoring.
  # Replace only the flat internal cap and add a child liner which follows it.
  for s in ['L','R']:
   nn=lookup['Nozzle_'+s];m=dnm.mesh(packs[dnm.fil(nn)]);m.f=[(ids,c,b) for ids,c,b in m.f if not(len(ids)>5 and np.ptp(np.array([m.v[i] for i in ids])[:,2])<1e-5)];packs[dnm.fil(nn)]=m.srf()
   add('OwnNozzleChamber'+s,chamber(0,0,-1.615,.46,.46,1.23),parent='Nozzle_'+s)
   fl=lookup['Flame_'+s];packs[dnm.fil(fl)]=flame(0,0,-1.66,.48,.48,1.8).srf()
 elif kind=='su34':
  # The source contains the actual petal surfaces. The former own pipe was
  # about 64cm too far forward and 12cm below their real centreline.
  remove(['FixedNozzle0','FixedNozzle1'])
  body_node=lookup['SourceAirframe'];body=dnm.mesh(packs[dnm.fil(body_node)]);kept=Mesh();petals={0:Mesh(),1:Mesh()}
  for ids,c,b in body.f:
   q=np.array([body.v[i] for i in ids]);cent=q.mean(0)
   selected=q[:,2].max()<-8.16 and q[:,1].min()>-1.12 and q[:,1].max()<.09 and abs(q[:,0]).min()>.62 and abs(q[:,0]).max()<1.86
   if selected:
    i=0 if cent[0]>0 else 1;angle=math.atan2(cent[1]+.484,abs(cent[0])-1.192);band=int(((angle+math.pi)/(2*math.pi))*24)%2;shade=97+band*12
    petals[i].face(q,(shade,shade+5,shade+12),False)
   else:kept.face(q,c,b)
  packs[dnm.fil(body_node)]=kept.srf()
  for i,sg in enumerate([1,-1]):
   x,y,z=sg*1.192,-.484,-8.8773
   assert petals[i].f
   add('SourceNozzlePetals'+str(i),petals[i])
   add('OwnNozzleChamber'+str(i),chamber(x,y,z+.016,.426,.427,1.05))
   fn=lookup['Afterburner'+str(i)];packs[dnm.fil(fn)]=flame(x,y,z-.02,.426,.427).srf()
 active={dnm.fil(n) for n in ns};packs={k:v for k,v in packs.items() if k in active}
 for name in [kind+'.dnm',kind+'_coarse.dnm']:dnm.write(rt/name,packs,ns)
 report[kind]={'added':added,'removed':removed,'not_yet_visually_accepted':True,'existing_animation_binding_preserved':True}
(root/'nozzle-repairs.json').write_text(json.dumps(report,indent=2));print('NOZZLES UPDATED',list(report),flush=True)
