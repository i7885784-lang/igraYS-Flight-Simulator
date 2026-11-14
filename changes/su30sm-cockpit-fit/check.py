"""Verify the exact scope and the actual serialized cockpit surfaces."""
from pathlib import Path
import sys,json,argparse,hashlib
import numpy as np,trimesh,fcl
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE));from repair import dnm,BASE_SHA,COCKPIT_SHA,SHA
sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin/validation'));from triangles import classify

def geometry(p,ns,name,faceids=None):
 node=next(n for n in ns if dnm.fil(n)==name);m=dnm.mesh(p[name]);v=np.array(m.v)+np.array(next(s[4:] for s in node if s.startswith('POS ')).split()[:3],float);ix=[];src=[]
 for fi,(ids,c,b) in enumerate(m.f):
  if faceids is not None and fi not in faceids:continue
  for j in range(1,len(ids)-1):ix.append([ids[0],ids[j],ids[j+1]]);src.append(fi)
 return v,np.array(ix),src

def obj(v,ix):
 b=fcl.BVHModel();b.beginModel(len(v),len(ix));b.addSubModel(v,ix);b.endModel();return fcl.CollisionObject(b)

def intersections(a,b):
 av,ai,asrc=a;bv,bi,bsrc=b;res=fcl.CollisionResult();fcl.collide(obj(av,ai),obj(bv,bi),fcl.CollisionRequest(num_max_contacts=20000,enable_contact=True),res);hits=[]
 for c in res.contacts:
  kind=classify(av[ai[c.b1]],bv[bi[c.b2]],tol=2e-6)
  if kind in ['cross','coplanar_overlap']:hits.append(dict(a=asrc[c.b1],b=bsrc[c.b2],kind=kind))
 return hits

def run(base,cpbase,candidate,out):
 bp,bn=dnm.read(base);p,ns=dnm.read(candidate/'su30sm.dnm');bcp,bcn=dnm.read(cpbase);cp,cn=dnm.read(candidate/'su30smcockpit.dnm');audit=json.loads((candidate/'audit.json').read_text());assert SHA(base.read_bytes())==BASE_SHA and SHA(cpbase.read_bytes())==COCKPIT_SHA
 assert bn==ns and bcn==cn;assert list(bp)==list(p) and list(bcp)==list(cp);assert [k for k in p if p[k]!=bp[k]]==['Su30Interior.srf'];assert [k for k in cp if cp[k]!=bcp[k]]==['Su30Interior.srf'];assert cp['Su30Interior.srf']==p['Su30Interior.srf']
 old=dnm.mesh(bp['Su30Interior.srf']);new=dnm.mesh(p['Su30Interior.srf']);protected=[f for i,f in enumerate(old.f) if not (i<18 or 54<=i<66 or 114<=i<126)];assert len(protected)==84
 for (oi,oc,ob),(ni,nc,nb) in zip(protected,new.f):assert oc==nc and ob==nb and [old.v[i] for i in oi]==[new.v[i] for i in ni]
 result=dict(model_sha256=SHA((candidate/'su30sm.dnm').read_bytes()),cockpit_sha256=SHA((candidate/'su30smcockpit.dnm').read_bytes()),changed_packs=['Su30Interior.srf'],protected_model_packs=len(p)-1,protected_cockpit_packs=len(cp)-1,all_nodes_exact=True,protected_original_interior_faces=84,parts={},external_intersections={})
 for name,(start,end) in audit['parts'].items():
  a=geometry(p,ns,'Su30Interior.srf',set(range(start,end)));v,ix,src=a;tm=trimesh.Trimesh(v,ix,process=True);tm.remove_unreferenced_vertices();deg=int((tm.area_faces<1e-12).sum());assert tm.is_watertight and tm.is_winding_consistent and deg==0,(name,tm.is_watertight,deg)
  # Shared geometrical vertices are normal adjacent facets after merging.
  q=tm.triangles;boxes=np.c_[q.min(1),q.max(1)];selfhits=[]
  for i in range(len(q)):
   for j in tm.triangles_tree.intersection(boxes[i]):
    if j<=i or set(tm.faces[i])&set(tm.faces[j]):continue
    k=classify(q[i],q[j],tol=2e-6)
    if k in ['cross','coplanar_overlap']:selfhits.append([int(i),int(j),k])
  assert not selfhits,(name,selfhits[:5]);result['parts'][name]=dict(watertight=True,normals_consistent=True,degenerate=0,self_intersections=0,triangles=len(ix),euler=int(tm.euler_number))
  if name.startswith('console') or name=='floor-front':
   ix2=[i for i,t in enumerate(ix) if v[t,2].max()>5.55001];a=(v,ix[ix2],[src[i] for i in ix2])
  for target in ['Fuselage_0_4.srf','Fuselage_0_6.srf','Cockpit_cover_6_30.srf','Cockpit_cover_6_31.srf']:
   hits=intersections(a,geometry(p,ns,target));result['external_intersections'][name+' / '+target]=hits;print(name,target,len(hits),flush=True)
 out.write_text(json.dumps(result,indent=2));assert not any(result['external_intersections'].values()),'New exterior intersections';return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('baseline',type=Path);a.add_argument('cockpit_baseline',type=Path);a.add_argument('candidate',type=Path);a.add_argument('output',type=Path);v=a.parse_args();run(v.baseline,v.cockpit_baseline,v.candidate,v.output)
