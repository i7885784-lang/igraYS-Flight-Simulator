from pathlib import Path
import re,numpy as np
class AC:
 def __init__(self,path):self.lines=Path(path).read_text().splitlines();self.i=0;self.objects=[];self.parse()
 def parse(self):
  while self.i<len(self.lines) and not self.lines[self.i].startswith('OBJECT '):self.i+=1
  self.obj(np.eye(3),np.zeros(3),[])
 def obj(self,PR,PT,parents):
  typ=self.lines[self.i].split()[1];self.i+=1;name=typ;loc=np.zeros(3);rot=np.eye(3);vs=[];fs=[];uv=[]
  while self.i<len(self.lines):
   s=self.lines[self.i];self.i+=1;a=s.split()
   if not a:continue
   if a[0]=='name':name=s[5:].strip('"')
   elif a[0]=='data':self.i+=1
   elif a[0]=='loc':loc=np.array(list(map(float,a[1:4])))
   elif a[0]=='rot':rot=np.array(list(map(float,a[1:10]))).reshape(3,3)
   elif a[0]=='numvert':
    n=int(a[1]);vs=[tuple(map(float,p.split()[:3])) for p in self.lines[self.i:self.i+n]];self.i+=n
   elif a[0]=='numsurf':
    for k in range(int(a[1])):
     flags=0
     while self.i<len(self.lines):
      p=self.lines[self.i].split();self.i+=1
      if p[0]=='SURF':flags=int(p[1],0)
      if p[0]=='refs':break
     rows=[x.split() for x in self.lines[self.i:self.i+int(p[1])]];self.i+=int(p[1]);fs.append([int(x[0]) for x in rows]);uv.append([(float(x[1]),float(x[2])) for x in rows])
   elif a[0]=='kids':
    R=PR@rot;T=PT+PR@loc;raw=[T+R@np.array(v) for v in vs];conv=[(float(v[2]),float(v[1]),float(-v[0])) for v in raw]
    if vs:self.objects.append({'name':name,'v':conv,'f':fs,'uv':uv,'parents':parents})
    for j in range(int(a[1])):self.obj(R,T,parents+[name])
    return
if __name__=='__main__':
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.collections import PolyCollection
 model=AC(Path(__file__).parent/'reference/Su-57.ac');out=Path(__file__).parent
 chosen=[o for o in model.objects if not any(s in o['name'].lower() for s in ['strut','post.','wheel','tyre'])]
 for o in chosen:
  v=np.array(o['v']);print(o['name'],len(o['f']),np.round(v.min(axis=0),2),np.round(v.max(axis=0),2))
 fig,axes=plt.subplots(1,2,figsize=(15,9))
 for ax,dims,depth,title in [(axes[0],(0,2),1,'TOP'),(axes[1],(0,1),2,'FRONT')]:
  polys=[]
  for o in chosen:
   for f in o['f']:
    if len(f)<3:continue
    pts=np.array([o['v'][i] for i in f]);polys.append((pts[:,depth].mean(),pts[:,dims],o['name']))
  polys.sort(key=lambda x:x[0]);ax.add_collection(PolyCollection([p for z,p,n in polys],facecolors=['#7399b0' if 'Glass' not in n else '#344e68' for z,p,n in polys],edgecolors='#354e60',linewidths=.12));ax.autoscale();ax.set_aspect('equal');ax.set_title(title);ax.grid(alpha=.3)
 fig.tight_layout();fig.savefig(out/'reference-orthos.png',dpi=120);print('OBJECTS',len(model.objects))
