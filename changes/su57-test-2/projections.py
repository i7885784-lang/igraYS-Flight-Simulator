from pathlib import Path
import numpy as np,math
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import dnm
from collision_su57 import rotation
lab=Path(__file__).resolve().parent

def polygons(path):
 packs,nodes=dnm.read(path);byn={dnm.name(n):n for n in nodes};parents={s[4:].strip('"'):dnm.name(n) for n in nodes for s in n if s.startswith('CLD ')}
 def pose(name):
  n=byn[name];v=list(map(float,next(s[4:] for s in n if s.startswith('POS ')).split()));R=rotation(v[3:6]);T=np.array(v[:3])
  if name in parents:
   rp,tp=pose(parents[name]);R=rp@R;T=tp+rp@T
  return R,T
 polys=[]
 for n in nodes:
  if dnm.cla(n) in [110,111,140,141,142,143,144,145,146,147,151]:continue
  name=dnm.name(n);R,T=pose(name);m=dnm.mesh(packs[dnm.fil(n)]);vs=np.array([T+R@np.array(v) for v in m.v])
  for ids,c,b in m.f:
   poly=vs[ids];normal=np.cross(poly[1]-poly[0],poly[2]-poly[0]);ll=np.linalg.norm(normal)
   normal=normal/ll if ll>1e-10 else np.array([0,1,0]);shade=.65+.35*abs(float(np.dot(normal,np.array([-.4,.8,.45]))));color=np.array(c[:3])/255*shade;alpha=c[3]/255 if len(c)==4 else 1
   polys.append((poly,tuple(color)+(alpha,)))
 return polys
new=polygons(lab/'runtime/aircraft/su57.dnm');old=polygons(lab.parent/'su57-lab1/runtime/aircraft/su57.dnm')
def draw(ax,polys,mode,title):
 if mode=='top':dims,depth,limits=(0,2),1,((-8,8),(-10.7,10.7))
 elif mode=='front':dims,depth,limits=(0,1),2,((-8,8),(-1.1,3.0))
 else:dims,depth,limits=(2,1),0,((-10.7,10.7),(-1.1,3.0))
 order=sorted(polys,key=lambda p:float(p[0][:,depth].mean()));ax.add_collection(PolyCollection([p[:,dims] for p,c in order],facecolors=[c for p,c in order],edgecolors='none',antialiaseds=False,linewidths=0));ax.set_xlim(*limits[0]);ax.set_ylim(*limits[1]);ax.set_aspect('equal');ax.set_facecolor('#e5ebef');ax.set_title(title,fontweight='bold',fontsize=15);ax.set_xticks([]);ax.set_yticks([])
 for sp in ax.spines.values():sp.set_color('#b1c0cc')
fig,axes=plt.subplots(2,2,figsize=(14,12),gridspec_kw={'height_ratios':[3.1,1]});draw(axes[0,0],old,'top','СВЕРХУ — ПЕРВЫЙ ТЕСТ');draw(axes[0,1],new,'top','СВЕРХУ — ПЕРЕСОБРАННАЯ МОДЕЛЬ');draw(axes[1,0],old,'front','СПЕРЕДИ — ПЕРВЫЙ ТЕСТ');draw(axes[1,1],new,'front','СПЕРЕДИ — ПЕРЕСОБРАННАЯ МОДЕЛЬ');fig.suptitle('Одинаковый масштаб • геометрические проекции без перспективы',fontsize=17);fig.tight_layout(rect=(0,0,1,.96));fig.savefig(lab/'comparison-orthos.png',dpi=130);plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(18,10),gridspec_kw={'width_ratios':[1,1,1.25]});draw(axes[0],new,'top','СВЕРХУ');draw(axes[1],new,'front','СПЕРЕДИ');draw(axes[2],new,'side','СБОКУ');fig.tight_layout();fig.savefig(lab/'model-orthos.png',dpi=130);plt.close(fig)
print('True orthographic projections ready')
