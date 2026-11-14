"""Repair only the confirmed Su30Interior surfaces in the two existing DNM files."""
from pathlib import Path
import sys,json,hashlib,argparse
import numpy as np
from shapely.geometry import Polygon
import trimesh
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin/model-source'))
import dnm
from mesh import Mesh
BASE_SHA='dd9c29fd7e555be4ba1b7257adb91bcc63f7a7d3943b1b3421c865daa529ada7'
COCKPIT_SHA='59e8226dede7a10d526e48332043d9d2f4dc27c018b6f3b732b188b567274b31'
SHA=lambda b:hashlib.sha256(b).hexdigest()

class Envelope:
 def __init__(self,p,ns):
  lu={dnm.fil(n):n for n in ns};self.tri={};self.cache={}
  for name in ['Fuselage_0_4.srf','Fuselage_0_6.srf','Cockpit_cover_6_30.srf','Cockpit_cover_6_31.srf']:
   m=dnm.mesh(p[name]);v=np.array(m.v)+np.array(next(s[4:] for s in lu[name] if s.startswith('POS ')).split()[:3],float)
   self.tri[name]=v[np.array([[ix[0],ix[j],ix[j+1]] for ix,c,b in m.f for j in range(1,len(ix)-1)])]
 def section(self,z,glass=True):
  key=(round(float(z),8),glass)
  if key in self.cache:return self.cache[key]
  seg=[]
  for name,t in self.tri.items():
   if not glass and name!='Fuselage_0_4.srf':continue
   keep=(t[:,:,2].min(1)<=z)&(t[:,:,2].max(1)>=z)&(t[:,:,0].min(1)<.9)&(t[:,:,0].max(1)>-.9)&(t[:,:,1].max(1)>.45)
   for q in t[keep]:
    pts=[]
    for a,b in zip(q,np.roll(q,-1,axis=0)):
     if (a[2]-z)*(b[2]-z)<0:pts.append((a+(z-a[2])/(b[2]-a[2])*(b-a))[:2])
    if len(pts)==2 and np.linalg.norm(pts[0]-pts[1])>1e-9:seg.append(pts)
  self.cache[key]=np.array(seg);return self.cache[key]
 def halfwidth(self,y,z):
  seg=self.section(z);a=seg[:,0];b=seg[:,1];dy=b[:,1]-a[:,1];ok=(abs(dy)>1e-10)&((a[:,1]-y)*(b[:,1]-y)<=0)
  t=np.divide(y-a[:,1],dy,out=np.zeros(len(a)),where=abs(dy)>1e-10);x=a[:,0]+t*(b[:,0]-a[:,0]);x=abs(x[ok]);x=x[(x>.08)&(x<.9)]
  if not len(x):raise ValueError(('No closed exterior boundary',y,z))
  return float(x.min())
 def width_range(self,lo,hi,z):
  values=[]
  for zz in [z-.008,z,z+.008]:
   for y in np.linspace(lo,hi,max(2,int((hi-lo)/.004)+2)):
    try:values.append(self.halfwidth(float(y),float(zz)))
    except ValueError:pass
  assert values,(lo,hi,z)
  return min(values)-.008
 def ceiling(self,x,z):
  seg=self.section(z);a=seg[:,0];b=seg[:,1];dx=b[:,0]-a[:,0];ok=(abs(dx)>1e-10)&((a[:,0]-x)*(b[:,0]-x)<=0);t=np.divide(x-a[:,0],dx,out=np.zeros(len(a)),where=abs(dx)>1e-10);y=a[:,1]+t*(b[:,1]-a[:,1]);y=y[ok&(y>.86)]
  if not len(y):raise ValueError(('No ceiling',x,z))
  return float(y.min())
 def ceiling_band(self,lo,hi,z):
  seg=self.section(z);xs=sorted(set([lo,hi]+[float(x) for x in seg[:,:,0].ravel() if lo<x<hi]));return min(self.ceiling(x,z) for x in xs)

def solid(rings,color):
 """Closed loft; merge the collapsed step-ring vertices before serialization."""
 v=np.array(rings).reshape(-1,3);n=len(rings[0]);tri=[]
 for j in range(len(rings)-1):
  for i in range(n):
   a=j*n+i;b=j*n+(i+1)%n;c=(j+1)*n+(i+1)%n;d=(j+1)*n+i;tri.extend([[a,b,c],[a,c,d]])
 # Triangulate true planar end polygons, including nonconvex shoulders.
 import triangle
 for j,reverse in [(0,True),(len(rings)-1,False)]:
  poly=np.array(rings[j])[:,:2];unique=[];ids=[]
  for i,q in enumerate(poly):
   if not unique or np.linalg.norm(q-unique[-1])>1e-8:unique.append(q);ids.append(j*n+i)
  if np.linalg.norm(unique[0]-unique[-1])<1e-8:unique.pop();ids.pop()
  a=np.array(unique);pslg={'vertices':a,'segments':np.array([[i,(i+1)%len(a)] for i in range(len(a))])};result=triangle.triangulate(pslg,'pQ');assert len(result['vertices'])==len(a)
  for t in result['triangles']:tri.append([ids[int(i)] for i in (t[::-1] if reverse else t)])
 tm=trimesh.Trimesh(v,np.array(tri),process=True);tm.update_faces(tm.nondegenerate_faces(height=1e-10));tm.remove_unreferenced_vertices()
 # Collapsed step rings can leave a long edge opposite several shorter collinear
 # edges. Split that existing triangle; never cover a hole with a new surface.
 for _ in range(4):
  counts=np.bincount(tm.edges_unique_inverse);bad=tm.edges_unique[counts==1];splits={}
  for a,b in bad:
   A=tm.vertices[a];B=tm.vertices[b];d=B-A;u=(tm.vertices-A)@d/(d@d);dist=np.linalg.norm(tm.vertices-(A+u[:,None]*d),axis=1);ids=np.flatnonzero((u>1e-8)&(u<1-1e-8)&(dist<1e-9))
   if len(ids):splits[tuple(sorted((int(a),int(b))))]=list(ids[np.argsort(u[ids])]) if a<b else list(ids[np.argsort(u[ids])][::-1])
  if not splits:break
  faces=[]
  for face in tm.faces:
   done=False
   for j in range(3):
    a,b,c=map(int,face[[j,(j+1)%3,(j+2)%3]]);key=tuple(sorted((a,b)))
    if key in splits:
     mid=splits[key] if a<b else splits[key][::-1];chain=[a]+mid+[b];faces.extend([[x,y,c] for x,y in zip(chain,chain[1:])]);done=True;break
   if not done:faces.append(face)
  tm=trimesh.Trimesh(tm.vertices,np.array(faces),process=False)
 tm.fix_normals();assert tm.is_watertight and tm.is_winding_consistent,(tm.euler_number,tm.body_count)
 out=Mesh();out.v=list(map(tuple,tm.vertices));out.f=[(list(map(int,t)),color,False) for t in tm.faces];return out

def panel(env):
 # Union of the former box and its cap. Steps retain the front/back cap overhang.
 zs=sorted(set(np.round(np.arange(6.02,6.26001,.015),8).tolist()+[6.02,6.085,6.235,6.26]));rings=[]
 for z in zs:
  states=[False,True] if z==6.085 else [True,False] if z==6.235 else [6.085<z<6.235]
  for tall in states:
   ys=[.685,.85,.955,.9925] if tall else [.9925]*4
   left=[];right=[]
   for y in ys:
    w=min(.355,env.width_range(.685,1.0175,z));left.append((-w,y,z));right.append((w,y,z))
   caplo=caphi=min(.38,env.width_range(.9925,1.0175,z))
   ring=right+[(caplo,.9925,z),(caphi,1.0175,z),(-caphi,1.0175,z),(-caplo,.9925,z)]+left[::-1]
   rings.append(ring)
 m=solid(rings,(30,34,37))
 m.f=[(ix,(24,28,30) if min(m.v[i][1] for i in ix)>=.9925-1e-8 else c,b) for ix,c,b in m.f]
 return m

def console(env,sign):
 # Retain the original console aft of Z=5.95; only the proven forward protrusion is tapered.
 rings=[]
 for z in [2.5,5.55]+list(np.round(np.arange(5.60,6.60001,.025),7)):
  outer=.465 if z<=5.55 else min(.465,env.width_range(.58,.82,z));inner=outer-.07
  (ai,ao,ay),(bi,bo,by),(ci,co,cy)=[(inner,outer,y) for y in [.58,.70,.82]]
  ring=[(sign*ai,ay,z),(sign*ao,ay,z),(sign*bo,by,z),(sign*co,cy,z),(sign*ci,cy,z),(sign*bi,by,z)];rings.append(ring)
 return solid(rings,(35,40,42))

def floor_front(env):
 rings=[]
 for z in [2.3,5.55]+list(np.round(np.arange(5.60,6.90001,.025),7)):
  w=.44 if z<=5.55 else min(.44,env.width_range(.48,.58,z))
  rings.append([(-w,.48,z),(w,.48,z),(w,.58,z),(-w,.58,z)])
 return solid(rings,(36,40,45))

def front_wall(env):
 rings=[]
 for z in [6.8,6.82,6.84,6.86,6.88]:
  side=[]
  for y in [.53,.57,.61,.65,.69,.73,.77]:
   w=min(.36,env.width_range(.53,.77,z));side.append((w,y,z))
  rings.append(side+[(-x,y,z) for x,y,z in side[::-1]])
 return solid(rings,(38,42,47))

def rear_wall(env):
 # A fitted aft enclosure, not a loose high rectangle: the deck slopes from
 # the real rear shell down to the space just behind the unchanged seat.
 rings=[];xs=np.linspace(-.57,.57,47)
 for z in np.linspace(2.31,3.63,45):
  height=1.47-(float(z)-2.31)/(3.63-2.31)*.43
  top=[]
  for x in xs:
   dx=1.14/46
   ymax=min(env.ceiling_band(max(-.57,float(x)-dx),min(.57,float(x)+dx),float(z)+dz) for dz in [-.015,0,.015])-.004
   top.append((float(x),min(height,ymax),float(z)))
  rings.append([(-.415,.56,z),(.415,.56,z),(.415,.86,z)]+top[::-1]+[(-.415,.86,z)])
 return solid(rings,(43,48,53))

def build(p,ns):
 original=dnm.mesh(p['Su30Interior.srf']);env=Envelope(p,ns);out=Mesh()
 # Every seat, display, floor and console aft section keeps its original coordinates/colors.
 for i,(ix,c,b) in enumerate(original.f):
  if i<18 or 54<=i<66 or 114<=i<126:continue
  out.face([original.v[j] for j in ix],c,b)
 out.parts={}
 for name,m in [('floor-front',floor_front(env)),('front-wall',front_wall(env)),('panel',panel(env)),('console-left',console(env,-1)),('console-right',console(env,1)),('rear-wall',rear_wall(env))]:
  start=len(out.f);out.merge(m);out.parts[name]=[start,len(out.f)]
 return out

def run(base,cpbase,outdir):
 assert SHA(base.read_bytes())==BASE_SHA;assert SHA(cpbase.read_bytes())==COCKPIT_SHA
 p,ns=dnm.read(base);cp,cn=dnm.read(cpbase);assert p['Su30Interior.srf']==cp['Su30Interior.srf'];m=build(p,ns);srf=m.srf();outdir.mkdir(parents=True,exist_ok=True);p['Su30Interior.srf']=srf;cp['Su30Interior.srf']=srf
 for name,packs,nodes in [('su30sm.dnm',p,ns),('su30smcockpit.dnm',cp,cn)]:dnm.write(outdir/name,packs,nodes)
 audit=dict(changed_packs=['Su30Interior.srf'],all_nodes_exact=True,model_sha256=SHA((outdir/'su30sm.dnm').read_bytes()),cockpit_sha256=SHA((outdir/'su30smcockpit.dnm').read_bytes()),vertices=len(m.v),faces=len(m.f),parts=m.parts);(outdir/'audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--baseline',type=Path,required=True);a.add_argument('--cockpit-baseline',type=Path,required=True);a.add_argument('--output',type=Path,required=True);v=a.parse_args();run(v.baseline,v.cockpit_baseline,v.output)
