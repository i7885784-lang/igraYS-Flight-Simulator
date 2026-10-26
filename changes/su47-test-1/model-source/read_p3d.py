from pathlib import Path
import struct,json
class Reader:
 def __init__(self,p):self.b=Path(p).read_bytes();self.i=0
 def read(self,f):v=struct.unpack_from('<'+f,self.b,self.i);self.i+=struct.calcsize('<'+f);return v[0] if len(v)==1 else v
 def string(self):end=self.b.index(0,self.i);s=self.b[self.i:end].decode('utf8',errors='replace');self.i=end+1;return s
 def magic(self,s):assert self.b[self.i:self.i+len(s)]==s,(self.i,self.b[self.i:self.i+8]);self.i+=len(s)
 def parse(self):
  self.magic(b'MLOD');version,n=self.read('II');lods=[]
  for _ in range(n):
   self.magic(b'P3DM');major,minor,np,nn,nf,flags=self.read('IIIIII')
   points=[self.read('fffI') for _ in range(np)];normals=[self.read('fff') for _ in range(nn)];faces=[]
   for _ in range(nf):
    nv=self.read('I');vs=[self.read('IIff') for _ in range(4)];fl=self.read('I');texture=self.string();material=self.string();faces.append({'v':vs[:nv],'flags':fl,'texture':texture,'material':material})
   self.magic(b'TAGG');tags={}
   while True:
    active=self.read('B');name=self.string();size=self.read('I');data=self.b[self.i:self.i+size];self.i+=size
    if name=='#EndOfFile#':break
    if active:tags[name]=data
   resolution=self.read('f');lods.append(dict(points=points,normals=normals,faces=faces,tags=tags,resolution=resolution))
  assert self.i==len(self.b),(self.i,len(self.b));return lods
if __name__=='__main__':
 import sys
 lods=Reader(sys.argv[1] if len(sys.argv)>1 else Path(__file__).parent/'upstream/Su_47_Berkut.p3d').parse()
 for l in lods:print(l['resolution'],len(l['points']),len(l['faces']),list(l['tags'])[:60])
