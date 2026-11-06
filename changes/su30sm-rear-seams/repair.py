from surface import *
from scipy.interpolate import LinearNDInterpolator,NearestNDInterpolator,RegularGridInterpolator
from scipy.spatial import cKDTree
from shapely.geometry import box
from source_surface import envelope,parts
from topology import panel
import json,collections
p,ns,lu,ss=surfaces(r/'baseline/su30sm.dnm');_,_,_,glob=surfaces(r/'reference-source.dnm');audit={};hs={};references={-1:[],1:[]}
for name in ['MainBayFixedSkin_Left','MainBayFixedSkin_Right']:
 heights={}
 for q,c in ss[name]:
  for v in q:
   k=tuple(np.round(v[[0,2]],4));heights[k]=min(heights.get(k,float('inf')),float(v[1]))
 surf=[]
 # Match the fixed inboard panel edge to the unchanged outer door across a 2mm gap.
 side='Left' if name.endswith('Left') else 'Right';sg=-1 if side=='Left' else 1
 door=ss['GearDoor_'+side+('_Inner' if sg<0 else '_Outer')];dp=[Polygon(q[:,[0,2]]) for q,c in door];dt=STRtree(dp);dc=np.array([np.linalg.solve(np.c_[q[:,[0,2]],np.ones(3)],q[:,1]) for q,c in door])
 def atdoor(z):
  ids=dt.query(Point(sg*1.872,z).buffer(1e-9),predicate='intersects')
  return None if not len(ids) else float((dc[ids]@np.array([sg*1.872,z,1])).min())
 for q,c in ss[name]:
  z=q.copy()
  for k,v in enumerate(q):
   z[k,[0,2]]=np.round(v[[0,2]],4);z[k,1]=heights[tuple(np.round(v[[0,2]],4))]
   w=max(0,1-(1.87-abs(v[0]))/.10)**2
   if w>0:
    target=atdoor(v[2])
    if target is not None:z[k,1]=(1-w)*z[k,1]+w*target
  if abs(np.cross(z[1]-z[0],z[2]-z[0])[1])>1e-10:surf.append((z,c))
 # Close the small accidental internal holes of this stationary skin only.
 pp=[Polygon(q[:,[0,2]]) for q,c in surf];dom=shapely.union_all(pp,grid_size=1e-6);vv=np.concatenate([q for q,c in surf]);uv,inv=np.unique(np.round(vv[:,[0,2]],6),axis=0,return_inverse=True);ys=np.full(len(uv),np.inf);np.minimum.at(ys,inv,vv[:,1]);hf=LinearNDInterpolator(uv,ys)
 from shapely.affinity import scale
 desired=box(1.03,-3.38,1.87,-.41).difference(box(1.05,-1.86,1.87,-.66))
 if sg<0:desired=scale(desired,xfact=-1,yfact=1,origin=(0,0))
 supportPolys=[Polygon(q[:,[0,2]]) for q,c in surf];supportTree=STRtree(supportPolys);supportCo=np.array([np.linalg.solve(np.c_[q[:,[0,2]],np.ones(3)],q[:,1]) for q,c in surf]);colorTree=cKDTree([q.mean(0)[[0,2]] for q,c in surf])
 for hole in parts(desired.difference(dom)):
  for t in shapely.get_parts(shapely.constrained_delaunay_triangles(hole)):
   xy=np.array(t.exterior.coords)[:3];h=hf(xy)
   for j,v in enumerate(xy):
    ids=supportTree.query(Point(v).buffer(1e-9),predicate='intersects')
    if len(ids):h[j]=float((supportCo[ids]@np.r_[v,1]).min())
   if not np.isfinite(h).all():continue
   q=np.c_[xy[:,0],h,xy[:,1]];color=surf[colorTree.query(xy.mean(0))[1]][1]
   if np.cross(q[1]-q[0],q[2]-q[0])[1]>0:q=q[::-1]
   surf.append((q,color))
 # Make the stationary closing sheet single-valued and conforming in height.
 from scipy.spatial import Delaunay
 values=np.concatenate([q for q,c in surf]);uv,ix=np.unique(np.round(values[:,[0,2]],6),axis=0,return_inverse=True);height=np.full(len(uv),np.inf);np.minimum.at(height,ix,values[:,1])
 # Preserve all genuine height breaks of the unchanged mating door edge.
 zzset=set()
 for q,c in door:
  for A,B in zip(q,np.roll(q,-1,axis=0)):
   da=A[0]-sg*1.872;db=B[0]-sg*1.872
   if abs(da)<1e-8:zzset.add(float(A[2]))
   if da*db<0:zzset.add(float((A+(B-A)*da/(da-db))[2]))
 for zz0 in sorted(zzset):
  if -3.38<=zz0<=-.41:
   y=atdoor(zz0)
   if y is not None:uv=np.vstack([uv,[sg*1.87,zz0]]);height=np.r_[height,y]
 uv2,ix=np.unique(np.round(uv,8),axis=0,return_inverse=True);he=np.full(len(uv2),np.inf);np.minimum.at(he,ix,height);uv=uv2;height=he;dtess=Delaunay(uv)
 colorParts=envelope(ss[name]);group=collections.defaultdict(list)
 for poly,a,c in colorParts:group[c].append(poly)
 cps=[];cc=[]
 for color,pp in group.items():
  for poly in parts(shapely.union_all(pp,grid_size=1e-6)):cps.append(poly);cc.append(color)
 colorIndex=STRtree(cps);colorNear=cKDTree([[q.centroid.x,q.centroid.y] for q in cps]);newSurf=[]
 for ids in dtess.simplices:
  xy=uv[ids]
  if abs(np.linalg.det(np.c_[xy,np.ones(3)]))<1e-10:continue
  q=np.c_[xy[:,0],height[ids],xy[:,1]];coef=np.linalg.solve(np.c_[xy,np.ones(3)],q[:,1]);rem=Polygon(xy).intersection(desired)
  if rem.area<1e-12:continue
  cuts=[]
  for k in colorIndex.query(rem,predicate='intersects'):
   cut=rem.intersection(cps[k]);cuts.extend((q,cc[k]) for q in parts(cut));rem=rem.difference(cut)
  cuts.extend((q,cc[colorNear.query([q.centroid.x,q.centroid.y])[1]]) for q in parts(rem))
  for poly,color in cuts:
   for t in shapely.get_parts(shapely.constrained_delaunay_triangles(poly)):
    xy=np.array(t.exterior.coords)[:3];q=np.c_[xy[:,0],np.c_[xy,np.ones(3)]@coef,xy[:,1]]
    if np.cross(q[1]-q[0],q[2]-q[0])[1]>0:q=q[::-1]
    if abs(np.cross(q[1]-q[0],q[2]-q[0])[1])>1e-10:newSurf.append((q,color))
 surf=newSurf;references[sg].extend(surf)
 R,C=transform(lu[name],0);m,meta=panel(surf,R,C);p[dnm.fil(lu[name])]=m.srf();ss[name]=surf
for side,sg in [('Left',-1),('Right',1)]:
 name='MainWheelBayShutter_'+side;source=glob[name];vv=np.concatenate([q for q,c in source]);uv,inv=np.unique(np.round(vv[:,[0,2]],6),axis=0,return_inverse=True);yy=np.full(len(uv),np.inf);np.minimum.at(yy,inv,vv[:,1]);lin=LinearNDInterpolator(uv,yy);near=NearestNDInterpolator(uv,yy)
 def original(x,z):
  v=float(lin([[sg*x,z]])[0]);return v if np.isfinite(v) else float(near([[sg*x,z]])[0])
 support=ss['MainBayFixedSkin_'+side]+ss['GearDoor_'+side+('_Inner' if sg<0 else '_Outer')];sp=[Polygon(q[:,[0,2]]) for q,c in support];st=STRtree(sp);co=np.array([np.linalg.solve(np.c_[q[:,[0,2]],np.ones(3)],q[:,1]) for q,c in support]);SV=np.concatenate([q for q,c in support]);supportNear=NearestNDInterpolator(SV[:,[0,2]],SV[:,1])
 def edgeheight(x,z):
  point=Point(sg*x,z);ids=st.query(point.buffer(3e-6),predicate='intersects');return float((co[ids]@np.array([sg*x,z,1])).min()) if len(ids) else float(supportNear([[sg*x,z]])[0])
 # Include genuine height breaks on all mating edges, not just uniform samples.
 def profile_nodes(axis,value,lo,hi):
  coords={lo,hi}
  for q,c in support:
   for A,B in zip(q,np.roll(q,-1,axis=0)):
    aa=A[axis]-(sg*value if axis==0 else value);bb=B[axis]-(sg*value if axis==0 else value)
    if abs(aa)<1e-9:coords.add(float(A[2] if axis==0 else abs(A[0])))
    if aa*bb<0:
     V=A+(B-A)*aa/(aa-bb);coords.add(float(V[2] if axis==0 else abs(V[0])))
  coords=sorted(x for x in coords if lo<=x<=hi)
  y=[edgeheight(value,t) if axis==0 else edgeheight(t,value) for t in coords]
  from shapely.geometry import LineString
  return np.array(LineString(np.c_[coords,y]).simplify(.00003,preserve_topology=False).coords)[:,0]
 xx=np.unique(np.r_[np.linspace(1.052,1.870,43),profile_nodes(2,-1.86,1.052,1.870),profile_nodes(2,-.66,1.052,1.870)])
 zz=np.unique(np.r_[np.linspace(-1.858,-.662,61),profile_nodes(0,1.05,-1.858,-.662),profile_nodes(0,1.872,-1.858,-.662)])
 H=np.empty((len(xx),len(zz)))
 for i,x in enumerate(xx):
  for j,z in enumerate(zz):
   v=original(x,z);delta=[]
   for d,ex,ez,sx,sz in [(x-1.052,1.052,z,1.05,z),(1.870-x,1.870,z,1.872,z),(z+1.858,x,-1.858,x,-1.86),(-.662-z,x,-.662,x,-.66)]:
    if d<.10:delta.append((1/max(d,1e-9)**2,edgeheight(sx,sz)-original(ex,ez),d))
   H[i,j]=v+((1-min(d for w,a,d in delta)/.10)**2*sum(w*a for w,a,d in delta)/sum(w for w,a,d in delta) if delta else 0)
 hf=RegularGridInterpolator((xx,zz),H,bounds_error=False,fill_value=None);hs[sg]=hf
 domain=box(min(sg*1.052,sg*1.870),-1.858,max(sg*1.052,sg*1.870),-.662);allcolor=envelope(source);group=collections.defaultdict(list)
 for poly,a,c in allcolor:group[c].append(poly)
 polys=[];cols=[]
 for c,pp in group.items():
  for q in parts(shapely.union_all(pp,grid_size=1e-6).buffer(.00001).buffer(-.00001)):polys.append(q);cols.append(c)
 tree=STRtree(polys);ct=cKDTree([[q.centroid.x,q.centroid.y] for q in polys]);surf=[]
 for i in range(len(xx)-1):
  for j in range(len(zz)-1):
   for indices in [[(i,j),(i+1,j),(i+1,j+1)],[(i,j),(i+1,j+1),(i,j+1)]]:
    v=np.array([[sg*xx[a],H[a,b],zz[b]] for a,b in indices]);coeff=np.linalg.solve(np.c_[v[:,[0,2]],np.ones(3)],v[:,1]);rem=Polygon(v[:,[0,2]]).intersection(domain)
    if rem.area<1e-12:continue
    pieces=[]
    for k in tree.query(rem,predicate='intersects'):
     cut=rem.intersection(polys[k]);pieces.extend((q,cols[k]) for q in parts(cut));rem=rem.difference(cut)
    pieces.extend((q,cols[ct.query([q.centroid.x,q.centroid.y])[1]]) for q in parts(rem))
    for pp,c in pieces:
     for t in shapely.get_parts(shapely.constrained_delaunay_triangles(pp)):
      xy=np.array(t.exterior.coords)[:3];q=np.c_[xy[:,0],np.c_[xy,np.ones(3)]@coeff,xy[:,1]]
      if np.cross(q[1]-q[0],q[2]-q[0])[1]>0:q=q[::-1]
      surf.append((q,c))
 references[sg].extend(surf)
 R,C=transform(lu[name],0);m,meta=panel(surf,R,C,thickness=.001);p[dnm.fil(lu[name])]=m.srf();audit[name]={'faces':len(m.f),'outline':domain.wkt,'physical_seam_target_m':.002};print(name,len(m.f),flush=True)
# Clip only the overlapping original body within the closing assembly footprint.
# Each reference triangle defines an exact plane; no nearest-point height fill.
refpoly=[];refq=[];refcoef=[]
for sg in [-1,1]:
 for q,c in references[sg]:
  if abs(np.cross(q[1]-q[0],q[2]-q[0])[1])<1e-10:continue
  refpoly.append(Polygon(q[:,[0,2]]));refq.append(q);refcoef.append(np.linalg.solve(np.c_[q[:,[0,2]],np.ones(3)],q[:,1]))
tree=STRtree(refpoly);refcoef=np.array(refcoef);refq=np.array(refq)
def clip(poly,normal,constant):
 out=[]
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  da=a@normal+constant;db=b@normal+constant
  if da>=-1e-12:out.append(a)
  if (da>=0)!=(db>=0):out.append(a+(b-a)*da/(da-db))
 return np.array(out)
name='Fuselage_0_4';n=lu[name];m=dnm.mesh(p[dnm.fil(n)]);R,C=transform(n,0);C=C+np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);out=Mesh();seen=set();affected=0
# Outside pieces keep the exact source positions/materials; triangulation only.
def emit(poly,color,bright):
 if len(poly)<3:return
 for k in range(1,len(poly)-1):
  t=np.array([poly[0],poly[k],poly[k+1]]);key=tuple(sorted(tuple(v) for v in np.round(t,6)))
  if key in seen or np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))<1e-11:continue
  seen.add(key);out.face((t-C)@R,color,bright)
rawBody=list(p[dnm.fil(n)]);firstFace=rawBody.index('F');blocks=[];bi=firstFace
while bi<len(rawBody) and rawBody[bi]=='F':
 bj=rawBody.index('E',bi)+1;blocks.append(rawBody[bi:bj]);bi=bj
rawPrefix=rawBody[:firstFace];rawSuffix=rawBody[bi:];keptBlocks=[];changedMeshes=[]
for faceIndex,(ids,color,bright) in enumerate(m.f):
 out=Mesh();seen=set()
 for j in range(1,len(ids)-1):
  q=np.array([m.v[i] for i in [ids[0],ids[j],ids[j+1]]])@R.T+C;remainder=[q]
  for sg in [-1,1]:
   rest=[];bounds=[(np.array([1.,0,0]),-min(sg*1.03,sg*1.87)),(np.array([-1.,0,0]),max(sg*1.03,sg*1.87)),(np.array([0.,0,1]),3.38),(np.array([0.,0,-1]),-.41)]
   for poly in remainder:
    inside=poly;outside=[]
    for normal,c in bounds:
     if len(inside)<3:break
     discard=clip(inside,-normal,-c)
     if len(discard)>=3:outside.append(discard)
     inside=clip(inside,normal,c)
    rest.extend(outside)
    if len(inside)<3:continue
    candidates=tree.query(box(inside[:,0].min()-1e-8,inside[:,2].min()-1e-8,inside[:,0].max()+1e-8,inside[:,2].max()+1e-8))
    if not len(candidates):emit(inside,color,bright);continue
    if inside[:,1].min()>refq[candidates,:,1].max()+.012:emit(inside,color,bright);continue
    affected+=1
    for k in candidates:
     xy=np.array(refpoly[k].exterior.coords)[:3];sign=1 if np.cross(xy[1]-xy[0],xy[2]-xy[0])>0 else -1;piece=inside
     for a,b in zip(xy,np.roll(xy,-1,axis=0)):
      d=b-a;normal=np.array([-d[1],0,d[0]])*sign;c=sign*(d[1]*a[0]-d[0]*a[1]);piece=clip(piece,normal,c+float(normal@np.array([1e-8,0,1e-8])))
      if len(piece)<3:break
     if len(piece)<3:continue
     a,b,c=refcoef[k];piece=clip(piece,np.array([-a,1,-b]),-c-.012);emit(piece,color,bright)
   remainder=rest
  for poly in remainder:emit(poly,color,bright)
 # Preserve source face records verbatim if clipping did not remove area.
 original=np.array([m.v[i] for i in ids]);area=sum(np.linalg.norm(np.cross(original[j]-original[0],original[j+1]-original[0]))/2 for j in range(1,len(ids)-1));ov=np.array(out.v);newArea=sum(np.linalg.norm(np.cross(ov[ii[1]]-ov[ii[0]],ov[ii[2]]-ov[ii[0]]))/2 for ii,c,b in out.f)
 if abs(area-newArea)<max(1e-12,area*1e-9):keptBlocks.append(blocks[faceIndex])
 else:changedMeshes.append((faceIndex,out))
newVertices=[];newBlocks=[];offset=len(m.v)
for faceIndex,mesh in changedMeshes:
 newVertices.extend('V %.10f %.10f %.10f'%v for v in mesh.v)
 for ids,c,b in mesh.f:
  block=[('V '+' '.join(str(offset+i) for i in ids)) if line.startswith('V ') else line for line in blocks[faceIndex]];newBlocks.append(block)
 offset+=len(mesh.v)
p[dnm.fil(n)]=rawPrefix+newVertices+sum(keptBlocks,[])+sum(newBlocks,[])+rawSuffix
audit[name]={'source_faces_kept_verbatim':len(keptBlocks),'source_faces_clipped':len(changedMeshes),'all_original_vertices_normals_and_material_records_preserved':True,'scope_abs_x':[1.03,1.87],'scope_z':[-3.38,-.41],'clearance_above_closing_skin_m':.012};print(audit[name],flush=True)
dnm.write(r/'runtime/aircraft/su30sm.dnm',p,ns);(r/'repair-audit.json').write_text(json.dumps(audit,indent=2))
