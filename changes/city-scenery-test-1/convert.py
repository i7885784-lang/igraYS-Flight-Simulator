from pathlib import Path
import sys,json,gzip,struct,numpy as np,collections,math
from scipy.spatial import Delaunay,cKDTree
from scipy.interpolate import LinearNDInterpolator
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'lib'));from mesh import Mesh
from ac_reference import AC
meta=json.loads((r/'sources.json').read_text());lon0,lat0,_=meta['origin'];lat,lon=np.deg2rad([lat0,lon0]);east=np.array([-np.sin(lon),np.cos(lon),0]);north=np.array([-np.sin(lat)*np.cos(lon),-np.sin(lat)*np.sin(lon),np.cos(lat)]);up=np.array([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)]);basis=np.c_[east,up,north]
def ecef(lon,lat,h):
 lo,la=np.deg2rad([lon,lat]);N=6378137/np.sqrt(1-6.69437999014e-3*np.sin(la)**2);return np.array([(N+h)*np.cos(la)*np.cos(lo),(N+h)*np.cos(la)*np.sin(lo),(N*(1-6.69437999014e-3)+h)*np.sin(la)])
origin=ecef(lon0,lat0,0);limit=1300;chunks={};samples=[];counts=collections.Counter()
def put(q,color,kind):
 q=np.array(q,float)
 if len(q)<3 or np.max(np.abs(q[:,[0,2]]))>limit:return
 cen=q.mean(0);key=(int(np.floor(cen[0]/250)),int(np.floor(cen[2]/250)));m=chunks.setdefault(key,Mesh());m.face(q,color);m.face(q[::-1],color);counts[kind]+=1
# BTG7/10: preserve ECEF placement, material and triangle/strip/fan topology.
b=gzip.decompress((r/'input/EGACbtg.gz/EGAC.btg.gz').read_bytes());ver,magic,stamp=struct.unpack_from('<HHI',b);assert magic==0x5347 and ver in [7,10];large=ver>=10;i=8;n=struct.unpack_from('<I' if large else '<H',b,i)[0];i+=4 if large else 2;objects=[];center=None;v=None
for k in range(n):
 typ=b[i];i+=1;fmt='<II' if large else '<HH';np_,ne=struct.unpack_from(fmt,b,i);i+=8 if large else 4;props={};els=[]
 for j in range(np_):
  t,size=struct.unpack_from('<BI',b,i);i+=5;props[t]=b[i:i+size];i+=size
 for j in range(ne):
  size=struct.unpack_from('<I',b,i)[0];i+=4;els.append(b[i:i+size]);i+=size
 if typ==0:center=np.array(struct.unpack_from('<ddd',els[0]))
 if typ==1:v=np.frombuffer(els[0],dtype='<f4').reshape(-1,3).astype(float)
 objects.append((typ,props,els))
assert i==len(b);v=(v+center-origin)@basis
for typ,props,els in objects:
 if typ not in [10,11,12]:continue
 mat=props.get(0,b'').decode();mask=props.get(1,b'\1')[0];stride=mask.bit_count();assert mask&1
 color=(99,126,76) if 'Grass' in mat else (225,208,75) if 'yellow' in mat.lower() else (224,224,213) if 'white' in mat.lower() else (77,81,83)
 for el in els:
  ids=np.frombuffer(el,dtype='<u4' if large else '<u2').reshape(-1,stride)[:,0];assert ids.max()<len(v)
  tris=ids.reshape(-1,3) if typ==10 else [(ids[k-2],ids[k-1],ids[k]) if k%2==0 else (ids[k-1],ids[k-2],ids[k]) for k in range(2,len(ids))] if typ==11 else [(ids[0],ids[k-1],ids[k]) for k in range(2,len(ids))]
  for tri in tris:
   q=v[list(tri)].copy();q[:,1]+=.025;put(q,color,'airport_triangles')
 # elevations from real airport triangle vertices
samples.extend(v.tolist())
for e in meta['entries']:
 ac=AC(r/'input'/e['path']);objects=ac.objects;detail=[o for o in objects if o['name']=='LOD_detail'];objects=objects;offset=(ecef(e['lon'],e['lat'],e['elevation'])-origin)@basis;road='roads' in e['path'];angle=np.deg2rad(e['heading']);R=np.array([[np.cos(angle),0,-np.sin(angle)],[0,1,0],[np.sin(angle),0,np.cos(angle)]])
 for o in objects:
  # AC3D FlightGear X=-North, Y=Up, Z=East. Reader converts to East/Up/North.
  vv=np.array(o['v'])@R.T+offset
  if not road:
   unique,inv=np.unique(np.round(vv,3),axis=0,return_inverse=True);parent=np.arange(len(unique))
   def find(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
   for face in o['f']:
    if len(face)<2:continue
    root=find(inv[face[0]])
    for vi in face[1:]:parent[find(inv[vi])]=root
   roots=np.array([find(i) for i in range(len(unique))]);minimum={}
   for i,key in enumerate(roots):minimum[key]=min(minimum.get(key,float('inf')),unique[i,1])
   floor=[point for point,key in zip(unique,roots) if point[1]<=minimum[key]+.1 and max(abs(point[[0,2]]))<limit];samples.extend(floor)
  for ids in o['f']:
   if len(ids)<3:continue
   q=vv[ids];normal=np.sum(np.cross(q,np.roll(q,-1,axis=0)),axis=0);length=np.linalg.norm(normal)
   if length<1e-7:continue
   normal/=length
   if road:
    q=q.copy();q[:,1]+=.08;put(q,(72,75,76),'road_faces');samples.extend(q.tolist())
   else:
    roof=abs(normal[1])>.3;center=q.mean(0);col=(109,83,67) if roof else [(181,173,151),(159,145,122),(182,174,163),(144,151,151)][int(abs(center[0]*.019+center[2]*.027))%4];put(q,col,'building_faces')
    # Lower edge samples carry the source building's terrain placement.
    pass # base samples were collected from connected buildings above
# Native collidable TerrMesh. Outside airport, heights are an explicit TIN
# approximation from the imported draped roads/building bases, not a full DEM.
a=np.array(samples);a=a[np.all(np.isfinite(a),axis=1)];a=a[(abs(a[:,0])<limit+1000)&(abs(a[:,2])<limit+1000)];xz=np.round(a[:,[0,2]],1);keys,idx=np.unique(xz,axis=0,return_index=True);heights=a[idx,1];interp=LinearNDInterpolator(keys,heights);tree=cKDTree(keys);step=25;axis=np.arange(-limit,limit+step/2,step);pts=np.array([(x,z) for z in axis for x in axis]);hh=interp(pts);bad=~np.isfinite(hh);hh[bad]=heights[tree.query(pts[bad])[1]];hh=np.clip(hh,-3,150)
N=len(axis)-1;ter=['TerrMesh',f'NBL {N} {N}',f'TMS {step} {step}']
for h in hh:ter.append(f'BLO {h:.3f} R 1 104 126 83 1 104 126 83')
ter+=['END'];packs=[('terrain.ter',ter)];objects=['TER','FIL "terrain.ter"',f'POS {-limit} 0 {-limit} 0 0 0','ID 0','END']
for k,m in sorted(chunks.items()):
 name=f'city_{k[0]}_{k[1]}.srf';packs.append((name,m.srf()));objects+=['SRF',f'FIL "{name}"','POS 0 0 0 0 0 0','ID 0','END']
ls=['FIELD','FLDNAME BELFAST_CITY_TEST','GND 104 126 83','SKY 95 157 210','DEFAREA LAND','BASEELV 0m','CANRESUME TRUE']
for name,data in packs:ls += [f'PCK "{name}" {len(data)}']+data
ls+=objects
out=r/'output';out.mkdir(exist_ok=True);(out/'belfast_test.fld').write_text('\n'.join(ls)+'\n');(out/'belfast_test.stp').write_text('N CITY_LOW\nC POSITION 0m 180m 0m\nC ATTITUDE 0deg 0deg 0deg\nP 0 0 0\nA 0 0 0\n');(out/'sce_belfast_test.lst').write_text('BELFAST_CITY_TEST scenery/belfast_test.fld scenery/belfast_test.stp\n');counts['spatial_chunks']=len(chunks);counts['terrain_grid_vertices']=len(hh);counts['elevation_samples']=len(keys);counts['btg_vertices']=len(v);(out/'conversion.json').write_text(json.dumps({'counts':counts,'bounds_m':[-limit,limit],'terrain_range_m':[float(hh.min()),float(hh.max())],'terrain_fallback':'TIN from imported road/building base heights outside airport BTG','textures':'own flat colours; no foreign atlas copied','origin_lon_lat':[lon0,lat0]},indent=2));print((out/'conversion.json').read_text())
