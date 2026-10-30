from pathlib import Path
import math,warnings
import numpy as np
from scipy.spatial.transform import Rotation
from mesh import Mesh,node
import dnm

def state(R=np.eye(3),t=np.zeros(3),show=1):
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');h,p,b=Rotation.from_matrix(R).as_euler('YXZ')
 return 'STA '+' '.join(map(str,[*np.round(t,7),round(-h*32768/math.pi),round(-p*32768/math.pi),round(b*32768/math.pi),show]))
def transform(n,idx):
 ss=[s.split()[1:] for s in n if s.startswith('STA ')];s=ss[min(idx,len(ss)-1)];t=np.array(s[:3],float);h,p,b=np.array(s[3:6],float)*math.pi/32768;return Rotation.from_euler('YXZ',[-h,-p,b]).as_matrix(),t

def add(p,ns,name,m,cla=99,states=None):
 fn=name+'.srf';p[fn]=m.srf();n=node(name,fn,cla)
 if states:
  i=n.index('NST 1');j=n.index('POS 0 0 0 0 0 0 1');n[i:j]=['NST '+str(len(states))]+states
 ns.append(n);return n

def double(m):
 for ids,c,b in list(m.f):m.face([m.v[i] for i in ids[::-1]],c,b)
 return m
