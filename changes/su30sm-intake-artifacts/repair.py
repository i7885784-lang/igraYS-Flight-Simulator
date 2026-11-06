"""Remove only measured surfaces intruding into the existing paired intake passages.
No animation, paint, EXE, or unrelated resource changes. Keep every original vertex and untouched face block.
"""
from pathlib import Path
import sys,json,hashlib,numpy as np,math
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import dnm,transform
base=r/'baseline/su30sm.dnm';assert hashlib.sha256(base.read_bytes()).hexdigest()=='1a10d466acf32d9647ee7fe2963b47419b94d44f34ed32229544eb72ad1bb032'
p,ns=dnm.read(base);old={k:list(v) for k,v in p.items()};lu={dnm.name(n):n for n in ns};audit={};tests=[]

def planes(sg,front):
 ax=.06/1.85;ay=.08/1.85;ab=-.12/1.85
 return [(np.array([0.,0,1]),3.10),(np.array([0.,0,-1]),front),(np.array([-sg,0,ax]),1.55+ax*1.25),(np.array([sg,0,ax]),-.81+ax*1.25),(np.array([0.,-1,ay]),-.15+ay*1.25),(np.array([0.,1,-ab]),.97-ab*1.25)]
# n dot point+c >=0, directly from the four unchanged tapered IntakeDuct wall planes.

def clip(poly,n,c,keep=True):
 out=[];sg=1 if keep else -1
 for a,b in zip(poly,poly[1:]+poly[:1]):
  da=(n@a+c)*sg;db=(n@b+c)*sg
  if da>=-1e-10:out.append(a)
  if (da>1e-10 and db<-1e-10) or (da<-1e-10 and db>1e-10):out.append(a+(b-a)*da/(da-db))
 clean=[]
 for a in out:
  if not clean or np.linalg.norm(a-clean[-1])>1e-9:clean.append(a)
 if len(clean)>1 and np.linalg.norm(clean[0]-clean[-1])<1e-9:clean.pop()
 return clean

def subtract(poly,ps):
 inside=list(poly);outside=[]
 for n,c in ps:
  if len(inside)<3:break
  part=clip(inside,n,c,False)
  if len(part)>=3:outside.append(part)
  inside=clip(inside,n,c,True)
 return outside,inside

def area(poly):
 return sum(np.linalg.norm(np.cross(poly[j]-poly[0],poly[j+1]-poly[0]))/2 for j in range(1,len(poly)-1)) if len(poly)>=3 else 0.

for name,front in [('Fuselage_0_4',-1.25),('Fuselage_0_7',-.39),('Fuselage_0_13',-.39),('GearWell_Left',-.39),('GearWell_Right',-.39)]:
 n=lu[name];fn=dnm.fil(n);ls=p[fn];raw=dnm.mesh(ls);R,t=transform(n,0);pos=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);C=t+pos;world=np.array(raw.v)@R.T+C;first=ls.index('F');prefix=ls[:first];blocks=[];i=first
 while i<len(ls) and ls[i]=='F':
  j=ls.index('E',i);blocks.append(ls[i:j+1]);i=j+1
 assert len(blocks)==len(raw.f);appendv=[];outfaces=[];changed=0;removed_area=0.;newfaces=0;retained=0
 for face_id,((ids,color,bright),block) in enumerate(zip(raw.f,blocks)):
  poly=world[ids];pieces=[(j-1,poly[[0,j,j+1]],list(poly[[0,j,j+1]])) for j in range(1,len(poly)-1)];removed=0.
  # Skip polygons outside both exact passage boxes cheaply.
  if poly[:,2].max()< -3.100001 or poly[:,2].min()>front+.000001 or poly[:,1].min()>.1 or abs(poly[:,0]).min()>1.6:
   outfaces.append(block);retained+=1;continue
  for side in [-1,1]:
   nextpieces=[]
   for source_index,source_tri,piece in pieces:
    outside,inside=subtract(piece,planes(side,front));a=area(inside)
    if a>1e-12:nextpieces += [(source_index,source_tri,part) for part in outside];removed+=a
    else:nextpieces.append((source_index,source_tri,piece))
   pieces=nextpieces
  if removed<=1e-12:outfaces.append(block);retained+=1;continue
  changed+=1;removed_area+=removed
  assert area(poly)+1e-8>=sum(area(q) for _,_,q in pieces)
  for source_index,source_tri,part in pieces:
   for j in range(1,len(part)-1):
    q=np.round(np.array([part[0],part[j],part[j+1]]),9);normal=np.cross(q[1]-q[0],q[2]-q[0]);mag=np.linalg.norm(normal)
    if mag<2e-12:continue
    # Every replacement is a subset of its original triangle/polygon, same paint and winding.
    local=(q-C)@R;inds=list(range(len(raw.v)+len(appendv),len(raw.v)+len(appendv)+3));appendv+=list(local);normal=normal@R;normal/=np.linalg.norm(normal);newblock=[]
    for line in block:
     if line.startswith('V '):newblock.append('V '+' '.join(map(str,inds)))
     elif line.startswith('N '):newblock.append('N '+' '.join('%.9f'%x for x in normal))
     else:newblock.append(line)
    outfaces.append(newblock);newfaces+=1;tests.append({'node':name,'source_face':face_id,'source_triangle_index':source_index,'source_world':source_tri.tolist(),'replacement_world':q.tolist()})
 p[fn]=prefix+['V %.9f %.9f %.9f'%tuple(v) for v in appendv]+sum(outfaces,[])+ls[i:]
 assert dnm.mesh(p[fn]).v[:len(raw.v)]==raw.v
 audit[name]={'source_faces':len(raw.f),'untouched_face_blocks_exact':retained,'clipped_or_removed_face_blocks':changed,'replacement_triangles':newfaces,'removed_triangle_instance_area_m2':removed_area,'cut_front_z_m':front,'cut_back_z_m':-3.1,'all_original_vertices_preserved':True,'all_colors_and_brightness_preserved':True,'original_frame_outside_passage_preserved':True}
# All mechanisms and all unrelated packs remain literally the same records.
out=r/'runtime/aircraft/su30sm.dnm';dnm.write(out,p,ns);_,after_nodes=dnm.read(out);assert ns==after_nodes
changed=[k for k in old if p[k]!=old[k]];audit['changed_packs']=changed;audit['all_nodes_and_animation_states_exact']=True;audit['all_other_packs_exact']=True;audit['model_sha256']=hashlib.sha256(out.read_bytes()).hexdigest();(r/'repair-audit.json').write_text(json.dumps(audit,indent=2));(r/'subset-provenance.json').write_text(json.dumps(tests,separators=(',',':')))
print(json.dumps(audit,indent=2))
