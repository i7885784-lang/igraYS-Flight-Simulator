import math
from PIL import Image,ImageFont,ImageDraw
class Mesh:
 def __init__(self):self.v=[];self.f=[]
 def face(self,pts,c,bright=False):
  ids=list(range(len(self.v),len(self.v)+len(pts)));self.v+=list(pts);self.f.append((ids,c,bright))
 def box(self,x,y,z,dx,dy,dz,c):
  p=[(x+a*dx/2,y+b*dy/2,z+d*dz/2) for a,b,d in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
  for ids in [(0,3,2,1),(4,5,6,7),(0,4,7,3),(1,2,6,5),(0,1,5,4),(3,7,6,2)]:self.face([p[i] for i in ids],c)
 def tube(self,a,b,rad,c,n=12,inner=0):
  # General cylinder aligned with its segment.
  d=[b[i]-a[i] for i in range(3)];ln=math.sqrt(sum(x*x for x in d));d=[x/ln for x in d];helper=(0,1,0) if abs(d[1])<.9 else (1,0,0)
  u=[d[1]*helper[2]-d[2]*helper[1],d[2]*helper[0]-d[0]*helper[2],d[0]*helper[1]-d[1]*helper[0]];ln=math.sqrt(sum(x*x for x in u));u=[x/ln for x in u];v=[d[1]*u[2]-d[2]*u[1],d[2]*u[0]-d[0]*u[2],d[0]*u[1]-d[1]*u[0]]
  def point(p,t,rr):return tuple(p[j]+rr*(u[j]*math.cos(t)+v[j]*math.sin(t)) for j in range(3))
  for i in range(n):
   t=2*math.pi*i/n;s=2*math.pi*(i+1)/n
   self.face([point(a,t,rad),point(a,s,rad),point(b,s,rad),point(b,t,rad)],c)
   if inner:
    self.face([point(b,t,rad),point(b,s,rad),point(b,s,inner),point(b,t,inner)],c)
   else:self.face([a,point(a,s,rad),point(a,t,rad)],c);self.face([b,point(b,t,rad),point(b,s,rad)],c)
 def text(self,text,x,y,z,h,c=(212,226,222)):
  font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14);bounds=font.getbbox(text);im=Image.new('L',(bounds[2]+2,19));ImageDraw.Draw(im).text((0,-bounds[1]),text,font=font,fill=255);s=h/14
  for j in range(im.height):
   k=0
   while k<im.width:
    if im.getpixel((k,j))<110:k+=1;continue
    start=k
    while k<im.width and im.getpixel((k,j))>=110:k+=1
    self.face([(x+start*s,y-j*s,z),(x+k*s,y-j*s,z),(x+k*s,y-(j+1)*s,z),(x+start*s,y-(j+1)*s,z)],c,True)
 def srf(self):
  ls=['SURF']+['V %.6f %.6f %.6f'%v for v in self.v]
  for ids,c,b in self.f:
   pts=[self.v[i] for i in ids];n=[0.,0.,0.]
   for aa,bb in zip(pts,pts[1:]+pts[:1]):
    n[0]+=(aa[1]-bb[1])*(aa[2]+bb[2]);n[1]+=(aa[2]-bb[2])*(aa[0]+bb[0]);n[2]+=(aa[0]-bb[0])*(aa[1]+bb[1])
   l=math.sqrt(sum(x*x for x in n));n=[x/l if l>1e-14 else 0 for x in n]
   ls+=['F','C '+' '.join(map(str,c)),'N %.6f %.6f %.6f'%tuple(n),'V '+' '.join(map(str,ids))]+(['B'] if b else [])+['E']
  return ls+['E']
 def merge(self,m):
  offset=len(self.v);self.v+=m.v;self.f += [([i+offset for i in ids],c,b) for ids,c,b in m.f]
 def shift(self,x,y,z):self.v=[(a+x,b+y,c+z) for a,b,c in self.v];return self

def node(name,file,cla=99,canopy=False,gear=False):
 ls=[f'SRF "{name}"',f'FIL {file}',f'CLA {cla}', 'NST 2' if canopy or gear else 'NST 1','STA 0 0 0 0 0 0 '+('0' if gear else '1')]
 if canopy:ls+=['STA 0 0 0 0 6372 0 1']
 if gear:ls+=['STA 0 0 0 0 0 0 1']
 ls+=['POS 0 1.35 3.0 0 0 0 1' if canopy else 'POS 0 0 0 0 0 0 1','CNT 0 0 0','PAX 1 0 0','REL DEP','NCH 0','END'];return ls

def pack_dnm(packs,nodes):
 ls=['DYNAMODEL','DNMVER 2']
 for name,lines in packs:ls += [f'PCK {name} {len(lines)}']+lines
 return '\n'.join(ls+nodes+['END'])+'\n'

