from pathlib import Path
import math,json,copy
import numpy as np
from scipy.interpolate import PchipInterpolator
from mesh import Mesh,node
from rig import rig_node
from gear_v3 import clip,cut_bay,normal
import dnm
lab=Path(__file__).resolve().parent;dest=lab/'runtime/aircraft';dest.mkdir(parents=True,exist_ok=True);packs={};nodes=[];stats={}
BLUE=(91,132,158);WHITE=(206,216,220);BELLY=(105,133,150);DARK=(28,38,46)
def face(m,pts,c,bright=False,up=None):
 if len(pts)<3:return
 nn=normal(pts)
 if sum(x*x for x in nn)<.5:return
 if up is not None and sum(a*b for a,b in zip(nn,up))<0:pts=pts[::-1]
 m.face(pts,c,bright)
def both(m,pts,c):face(m,pts,c);face(m,pts[::-1],c)
def camo(x,z):
 if z>7.95:return (208,221,231)
 ix,iz=math.floor(abs(x)/.32),math.floor(z/.32)
 border=2.65+1.15*math.exp(-((z+3.3)/2.6)**2)
 border=round(border/.32)*.32 + .32*(((iz*iz+3*iz+17)%7-3)//2)
 if abs(x)>6.75:return (137,175,199)
 if -4.0<z<-2.8 and 3.5<abs(x)<5.5:return (62,115,151)
 return (224,233,238) if abs(x)>border else (87,139,174)

def paint(m,poly,up=True):
 if not up:face(m,poly,BELLY,up=(0,-1,0));return
 xs=[v[0] for v in poly];zs=[v[2] for v in poly]
 for ix in range(math.floor(min(xs)/.30),math.ceil(max(xs)/.30)):
  p=clip(clip(poly,0,ix*.30,True),0,(ix+1)*.30,False)
  if len(p)<3:continue
  for iz in range(math.floor(min(zs)/.34),math.ceil(max(zs)/.34)):
   q=clip(clip(p,2,iz*.34,True),2,(iz+1)*.34,False)
   if len(q)>=3:face(m,q,camo((ix+.5)*.30,(iz+.5)*.34),up=(0,1,0))
def add(name,m,cla=99,pos=(0,0,0),states=None,parent=None):
 fn=name+'.srf';packs[fn]=m.srf();n=node(name,fn,cla)
 n=dnm.edit(n,'POS ',' '.join(map(str,pos))+' 0 0 0 1')
 if states:
  a=n.index('NST 1');b=next(i for i,x in enumerate(n) if x.startswith('POS '));n[a:b]=['NST '+str(len(states))]+['STA '+' '.join(map(str,s)) for s in states]
 nodes.append(n)
 if parent:
  pi=next(i for i,a in enumerate(nodes) if dnm.name(a)==parent);nodes[pi]=dnm.edit(nodes[pi],'NCH ',str(sum(x.startswith('CLD ') for x in nodes[pi])+1));nodes[pi].insert(-1,'CLD "'+name+'"')
 return n

def orient(mesh,pivot,axis):
 ax=np.array(axis,dtype=float);ax/=np.linalg.norm(ax);ez=np.array([-ax[2],0,ax[0]]);mesh.v=[(float(np.dot(np.array(v)-pivot,ax)),v[1]-pivot[1],float(np.dot(np.array(v)-pivot,ez))) for v in mesh.v];return round(math.atan2(ax[2],ax[0])*32768/math.pi)

def surface(poly,y=.12,thick=.07):
 m=Mesh();pts=[(x,y,z) for x,z in poly];paint(m,pts);paint(m,[(x,y-thick,z) for x,z in poly],False)
 for a,b in zip(pts,pts[1:]+pts[:1]):
  both(m,[a,b,(b[0],b[1]-thick,b[2]),(a[0],a[1]-thick,a[2])],(112,143,162))
  m.tube((a[0],a[1]+.004,a[2]),(b[0],b[1]+.004,b[2]),.006,(78,107,126),6)
 return m

def cut2(poly,a,b,c,positive=True):
 out=[]
 for p,q in zip(poly,poly[1:]+poly[:1]):
  v=(a*p[0]+b*p[1]+c)*(1 if positive else -1);w=(a*q[0]+b*q[1]+c)*(1 if positive else -1)
  if v>=-1e-9:out.append(p)
  if v*w<0:
   t=v/(v-w);out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
 return out
