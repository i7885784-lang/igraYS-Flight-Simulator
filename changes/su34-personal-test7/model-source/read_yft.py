"""GTA V legacy RSC7 geometry reader. Layout references: CodeWalker by Neodymium/dexyfex; see NOTICE.txt. No textures/systems imported."""
from pathlib import Path
import struct,zlib,json,sys
import numpy as np
from scipy.spatial.transform import Rotation
class YFT:
 def __init__(self,path):
  b=Path(path).read_bytes();magic,self.version,sf,gf=struct.unpack_from('<4sIII',b);assert magic==b'RSC7' and self.version==162,(magic,self.version)
  size=lambda f:(0x200<<(f&15))*(((f>>27)&1)+(((f>>26)&1)<<1)+(((f>>25)&1)<<2)+(((f>>24)&1)<<3)+(((f>>17)&127)<<4)+(((f>>11)&63)<<5)+(((f>>7)&15)<<6)+(((f>>5)&3)<<7)+(((f>>4)&1)<<8))
  self.sys_size=size(sf);self.gfx_size=size(gf);self.data=zlib.decompress(b[16:],-15);assert len(self.data)==self.sys_size+self.gfx_size
 def off(self,p):
  if p>>28==5:r=p-0x50000000
  elif p>>28==6:r=self.sys_size+p-0x60000000
  else:raise ValueError(hex(p))
  assert 0<=r<len(self.data);return r
 def u(self,fmt,p,ofs=0):return struct.unpack_from('<'+fmt,self.data,self.off(p)+ofs)
 def ptr(self,p,ofs=0):return self.u('Q',p,ofs)[0]
 def string(self,p):
  o=self.off(p);end=self.data.index(0,o);return self.data[o:end].decode('utf8',errors='replace')
 def bones(self,sp):
  count=self.u('H',sp,0x5e)[0];bp=self.ptr(sp,0x20);out=[]
  for i in range(count):
   p=bp+i*80;q=self.u('4f',p);t=self.u('3f',p,0x10);scale=self.u('3f',p,0x20);parent=self.u('h',p,0x32)[0];name=self.string(self.ptr(p,0x38))
   T=np.eye(4);T[:3,:3]=Rotation.from_quat(q).as_matrix()@np.diag(scale);T[:3,3]=t
   W=out[parent]['matrix']@T if parent>=0 else T
   out.append({'name':name,'parent':parent,'translation':t,'rotation':q,'scale':scale,'tag':self.u('H',p,0x44)[0],'matrix':W,'position':W[:3,3]})
  return out
 def parse(self):
  root=0x50000000;dp=self.ptr(root,0x30);self.name=self.string(self.ptr(root,0x58));skel=self.ptr(dp,0x18);self.skeleton=self.bones(skel)
  self.meshes=self.drawable_meshes(dp)
  tags={b['tag']:i for i,b in enumerate(self.skeleton)}
  group=self.ptr(root,0xf0)
  self.physics_children=[]
  if group:
   lod=self.ptr(group,0x10)
   if lod:
    children=self.ptr(lod,0xd0);count=self.u('B',lod,0x11d)[0]
    for i in range(count):
     child=self.ptr(children,8*i);tag=self.u('H',child,0x12)[0];drawable=self.ptr(child,0xa0)
     assert tag in tags
     if not drawable:continue
     bone=tags[tag];meshes=self.drawable_meshes(drawable,force_bone=bone)
     self.physics_children.append({'index':i,'bone':bone,'meshes':len(meshes)})
     self.meshes.extend(meshes)
  return self
 def drawable_meshes(self,dp,force_bone=None):
  models=self.ptr(dp,0x50)
  if not models:return []
  arr=self.ptr(models);cnt=self.u('H',models,8)[0];meshes=[]
  sizes=[0,4,4,8,0,8,12,16,4,4,4,0,0,0,0,0]
  for mi in range(cnt):
   mp=self.ptr(arr,mi*8);gp=self.ptr(mp,8);ng=self.u('H',mp,16)[0];binding=self.u('I',mp,0x28)[0];bone=binding>>24;skin=(binding>>8)&255;sm=self.ptr(mp,0x20)
   for gi in range(ng):
    g=self.ptr(gp,gi*8);vb=self.ptr(g,0x18);ib=self.ptr(g,0x38);ni=self.u('I',g,0x58)[0];nv=self.u('H',g,0x60)[0];stride=self.u('H',vb,8)[0];nvb=self.u('I',vb,0x18)[0];assert nv==nvb
    data=self.ptr(vb,0x10) or self.ptr(vb,0x20);info=self.ptr(vb,0x30);flags,ds,_,nc,types=self.u('IHBBQ',info);assert ds==stride
    attrs={};offset=0
    for semantic in range(16):
     if not flags&(1<<semantic):continue
     typ=(types>>(semantic*4))&15;sz=sizes[typ];assert sz>0,(typ,semantic)
     fmt,dim={1:('f2',2),2:('f4',1),3:('f2',4),5:('f4',2),6:('f4',3),7:('f4',4),8:('u1',4),9:('u1',4),10:('i1',4)}[typ]
     attrs[semantic]=np.ndarray((nv,dim),dtype='<'+fmt,buffer=self.data,offset=self.off(data)+offset,strides=(stride,np.dtype(fmt).itemsize)).copy();offset+=sz
    assert offset==stride,(offset,stride);idxptr=self.ptr(ib,16);nic=self.u('I',ib,8)[0];assert ni==nic and ni%3==0;faces=np.frombuffer(self.data,dtype='<u2',count=ni,offset=self.off(idxptr)).reshape(-1,3).copy();assert faces.max()<nv
    pos=attrs[0].astype(float);norm=attrs.get(3);palette_count=self.u('H',g,0x72)[0];palette_ptr=self.ptr(g,0x68);palette=list(self.u(str(palette_count)+'H',palette_ptr)) if palette_count else []
    if not skin:
     T=self.skeleton[force_bone if force_bone is not None else bone]['matrix'];pos=pos@T[:3,:3].T+T[:3,3]
     if norm is not None:norm=norm@T[:3,:3].T
    meshes.append({'model':mi,'geometry':gi,'bone':force_bone if force_bone is not None else bone,'skin':skin,'shader':self.u('H',sm,gi*2)[0],'positions':pos,'normals':norm,'faces':faces,'weights':attrs.get(1),'indices':attrs.get(2),'palette':palette,'raw_positions':attrs[0].astype(float)})
  return meshes
if __name__=='__main__':
 r=YFT(sys.argv[1]).parse();print('MODEL',r.name,'bones',len(r.skeleton),'meshes',len(r.meshes))
 for i,b in enumerate(r.skeleton):print('BONE',i,b['name'],b['parent'],np.round(b['position'],3))
 for m in r.meshes:print('MESH',m['model'],m['geometry'],'bone',m['bone'],'skin',m['skin'],'shader',m['shader'],'palette',m['palette'],'verts',len(m['positions']),'tri',len(m['faces']),np.round(m['positions'].min(0),2),np.round(m['positions'].max(0),2),'weights',np.unique(m['weights']) if m['weights'] is not None else None)
