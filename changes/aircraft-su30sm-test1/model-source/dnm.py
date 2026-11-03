from pathlib import Path
import re,math
from mesh import Mesh,pack_dnm

def read(path):
 ls=Path(path).read_text().splitlines();packs={};i=2
 while i<len(ls):
  if not ls[i].strip():i+=1;continue
  if not ls[i].startswith('PCK '):break
  _,name,n=ls[i].split();n=int(n);packs[name]=ls[i+1:i+1+n];i+=n+1
 text='\n'.join(ls[i:]);nodes=[]
 for block in re.split(r'(?m)^SRF ',text):
  if not block.strip() or block.strip()=='END':continue
  ls=('SRF '+block).splitlines();end=ls.index('END');nodes.append(ls[:end+1])
 return packs,nodes

def mesh(lines):
 m=Mesh();i=1
 while i<len(lines) and lines[i]!='F':
  if lines[i].startswith('V '):m.v.append(tuple(map(float,lines[i].split()[1:4])))
  i+=1
 while i<len(lines):
  if lines[i]!='F':i+=1;continue
  j=lines.index('E',i);data=lines[i:j];ids=list(map(int,next(x[2:] for x in data if x.startswith('V ')).split()));col=tuple(map(int,next(x[2:] for x in data if x.startswith('C ')).split()));m.f.append((ids,col,'B' in data));i=j+1
 return m

def write(path,packs,nodes):Path(path).write_text(pack_dnm(list(packs.items()),sum(nodes,[])))
def name(n):return n[0][5:].strip('"')
def fil(n):return next(s[4:] for s in n if s.startswith('FIL ')).strip('"')
def cla(n):return int(next(s[4:] for s in n if s.startswith('CLA ')))
def edit(n,prefix,value):return [prefix+value if s.startswith(prefix) else s for s in n]
