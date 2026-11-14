"""Subtract proven imported F4 remnants in the existing OUTER door apertures.
The upper limit follows the unchanged GearWell ceiling; keep 12 mm below it.
Keep the original upper skin, original face attributes, and all original vertices verbatim.
"""
import numpy as np,shapely
from shapely.geometry import Polygon,box
from shapely.strtree import STRtree

def clip(poly,n,c,positive=True):
 out=[];sg=1 if positive else -1
 for a,b in zip(poly,poly[1:]+poly[:1]):
  da=(n@a+c)*sg;db=(n@b+c)*sg
  if da>=0:out.append(a)
  if (da>=0)!=(db>=0):out.append(a+(b-a)*da/(da-db))
 clean=[]
 for a in out:
  if not clean or np.linalg.norm(a-clean[-1])>1e-9:clean.append(a)
 if len(clean)>1 and np.linalg.norm(clean[0]-clean[-1])<1e-9:clean.pop()
 return clean

def area(q):
 return sum(np.linalg.norm(np.cross(q[i]-q[0],q[i+1]-q[0]))/2 for i in range(1,len(q)-1)) if len(q)>=3 else 0

def subtract(poly,planes):
 inside=list(poly);outside=[]
 for n,c in planes:
  if len(inside)<3:return [poly],0.
  part=clip(inside,n,c,False)
  if len(part)>=3 and area(part)>1e-13:outside.append(part)
  inside=clip(inside,n,c)
 removed=area(inside)
 assert sum(area(q) for q in outside)+removed<=area(poly)+1e-8
 return (outside,removed) if removed>1e-12 else ([poly],0.)

def cut(p,lu,roofs,dnm,world):
 cells=[];coverage={}
 for side,sg in [('Left',-1),('Right',1)]:
  rect=box(-2.4 if sg<0 else 1.87,-3.38,-1.87 if sg<0 else 2.4,-.41).union(box(-1.87 if sg<0 else 1.03,-.66,-1.03 if sg<0 else 1.87,-.41))
  cover=[]
  for Q in roofs[side]:
   poly=Polygon(Q[:,[0,2]])
   if poly.area<1e-12:continue
   b=np.linalg.solve(np.c_[Q[:,[0,2]],np.ones(3)],Q[:,1]);inter=poly.intersection(rect)
   for part in shapely.get_parts(inter):
    if part.geom_type!='Polygon' or part.area<1e-12:continue
    cover.append(part)
    for t in shapely.get_parts(shapely.constrained_delaunay_triangles(part)):
     uv=np.array(t.exterior.coords)[:3]
     if t.area<1e-12:continue
     if np.cross(uv[1]-uv[0],uv[2]-uv[0])<0:uv=uv[::-1]
     planes=[]
     for A,B in zip(uv,np.roll(uv,-1,axis=0)):
      dx,dz=B-A;planes.append((np.array([-dz,0,dx]),dz*A[0]-dx*A[1]))
     planes.append((np.array([b[0],-1,b[1]]),b[2]-.012))
     planes=[(n/np.linalg.norm(n),c/np.linalg.norm(n)) for n,c in planes]
     cells.append((t,planes))
  coverage[side]=float(rect.difference(shapely.union_all(cover)).area)
 print('roof projection missing',coverage,flush=True)
 print('interior cells',len(cells),flush=True);tree=STRtree([q for q,planes in cells])
 name='Fuselage_0_4';n=lu[name];fn=dnm.fil(n);ls=p[fn];m=dnm.mesh(ls);R,C=world(n);v=np.array(m.v)@R.T+C;first=ls.index('F');blocks=[];k=first
 while k<len(ls) and ls[k]=='F':
  end=ls.index('E',k)+1;blocks.append(ls[k:end]);k=end
 assert len(blocks)==len(m.f)
 vertex_lines=[s for s in ls[:first] if s.startswith('V ')];normals=[]
 for line in vertex_lines:
  s=line.split();normals.append(np.array(s[5:8],float) if len(s)>=8 and s[4]=='R' else None)
 out=[];newv=[];rows=[];total_removed=0.;protected=0;max_plane_error=0.;max_barycentric_violation=0.
 for fi,((ids,col,bright),block) in enumerate(zip(m.f,blocks)):
  q=v[ids]
  if q[:,2].min()>-.41 or q[:,2].max()<-3.38 or q[:,0].min()>2.4 or q[:,0].max()<-2.4 or (q[:,0].min()>-1.03 and q[:,0].max()<1.03):out.append(block);protected+=1;continue
  query=box(q[:,0].min(),q[:,2].min(),q[:,0].max(),q[:,2].max()).buffer(1e-10)
  hits=tree.query(query,predicate='intersects')
  if not len(hits):out.append(block);protected+=1;continue
  pieces=[(q[[0,j,j+1]],ids[0:1]+ids[j:j+2],list(q[[0,j,j+1]])) for j in range(1,len(ids)-1)];removed=0.
  for ci in hits:
   nextpieces=[]
   for source,source_ids,poly in pieces:
    rest,a=subtract(poly,cells[ci][1]);removed+=a;nextpieces.extend((source,source_ids,t) for t in rest)
   pieces=nextpieces
   if not pieces:break
  if removed<1e-11:out.append(block);protected+=1;continue
  kept=0.;start_newv=len(newv)
  for source,source_ids,poly in pieces:
   for j in range(1,len(poly)-1):
    tri=np.array([poly[0],poly[j],poly[j+1]])
    if area(tri)<1e-12:continue
    ab=np.array([source[1]-source[0],source[2]-source[0]]).T;weights2=np.linalg.lstsq(ab,(tri-source[0]).T,rcond=None)[0].T;weights3=np.c_[1-weights2.sum(1),weights2];residual=tri-(source[0]+weights2@ab.T);plane_error=float(np.max(np.linalg.norm(residual,axis=1)));bary_violation=float(max(0.,-weights3.min()));max_plane_error=max(max_plane_error,plane_error);max_barycentric_violation=max(max_barycentric_violation,bary_violation);assert plane_error<1e-7 and bary_violation<1e-6,(fi,plane_error,bary_violation)
    kept+=area(tri);local=(tri-C)@R;indices=list(range(len(m.v)+len(newv),len(m.v)+len(newv)+3))
    for Q,L in zip(tri,local):
     line='V '+' '.join('%.10f'%x for x in L)
     if all(normals[i] is not None for i in source_ids):
      ab=np.array([source[1]-source[0],source[2]-source[0]]).T;bc=np.linalg.lstsq(ab,Q-source[0],rcond=None)[0];weights=np.r_[1-sum(bc),bc];normal=weights@np.array([normals[i] for i in source_ids]);normal/=max(np.linalg.norm(normal),1e-15);line+=' R '+' '.join('%.9f'%x for x in normal)
     newv.append(line)
    out.append(['V '+' '.join(map(str,indices)) if s.startswith('V ') else s for s in block])
  assert kept+removed<=area(list(q))+1e-7,(fi,kept,removed,area(list(q)))
  rows.append({'source_face':fi,'new_vertex_start':len(m.v)+start_newv,'new_vertex_end':len(m.v)+len(newv),'source_area_m2':area(list(q)),'removed_area_m2':removed,'kept_area_m2':kept,'world_min':q.min(0).tolist(),'world_max':q.max(0).tolist()});total_removed+=removed
  if len(rows)%1000==0:print('clipped',len(rows),'source index',fi,flush=True)
 p[fn]=ls[:first]+newv+[s for b in out for s in b]+ls[k:]
 print('F4 clipped',len(rows),'retained raw',protected,'area',total_removed,flush=True)
 return {'changed_face_blocks':len(rows),'untouched_face_blocks_exact':protected,'original_vertices_exact':True,'removed_area_triangle_instances_m2':total_removed,'bay_rectangles_m':[[1.87,2.4,-3.38,-.41],[-2.4,-1.87,-3.38,-.41],[1.03,1.87,-.66,-.41],[-1.87,-1.03,-.66,-.41]],'ceiling_protection_m':.012,'cells':len(cells),'source_face_changes':rows,'replacement_max_plane_error_m':max_plane_error,'replacement_max_barycentric_violation':max_barycentric_violation,'roof_projection_unmodified_area_m2':coverage}
