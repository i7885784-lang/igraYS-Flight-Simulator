"""Verify the serialized result, not just the boolean library's in-memory solids."""
from pathlib import Path
import sys,json,hashlib,argparse
import numpy as np,trimesh
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'su30sm-local-skin/model-source'))
import dnm
NAMES=['MainBayFixedSkin_Left','MainBayFixedSkin_Right','GearDoor_Left_Inner','GearDoor_Right_Outer']
sha=lambda b:hashlib.sha256(b).hexdigest()
def verify(base,candidate,out):
 p,ns=dnm.read(base);q,nt=dnm.read(candidate);assert ns==nt,'Node/parent/axis/animation records changed';assert list(p)==list(q)
 changed=[k for k in p if p[k]!=q[k]];assert set(changed)=={n+'.srf' for n in NAMES}|{'Fuselage_0_4.srf'}
 result=dict(baseline_sha256=sha(base.read_bytes()),model_sha256=sha(candidate.read_bytes()),all_original_nodes_exact=True,node_count=len(ns),changed_packs=changed,protected_packs={k:sha(('\n'.join(v)+'\n').encode()) for k,v in p.items() if k not in changed},geometry={})
 palette={c for n in NAMES for ids,c,b in dnm.mesh(p[n+'.srf']).f}|{(105,118,123),(148,153,148)}
 for n in NAMES:
  lines=q[n+'.srf'];m=dnm.mesh(lines);v=np.array(m.v);f=np.array([ids for ids,c,b in m.f]);assert f.shape[1]==3 and np.isfinite(v).all();assert {c for ids,c,b in m.f}<=palette
  tm=trimesh.Trimesh(v,f,process=False);areas=tm.area_faces;normals=np.array([list(map(float,s[2:].split())) for s in lines if s.startswith('N ')]);cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);unit=cross/np.linalg.norm(cross,axis=1)[:,None];dots=np.einsum('ij,ij->i',normals,unit)
  sortedfaces=np.sort(f,axis=1);duplicate=len(f)-len(np.unique(sortedfaces,axis=0))
  stat=dict(vertices=len(v),triangles=len(f),watertight=bool(tm.is_watertight),winding_consistent=bool(tm.is_winding_consistent),components=int(tm.body_count),min_area_m2=float(areas.min()),degenerate=int(np.sum(areas<1e-14)),min_normal_dot=float(dots.min()),duplicate_faces=duplicate,volume_m3=float(tm.volume))
  print(n,stat,flush=True);result['geometry'][n]=stat
  assert stat['watertight'] and stat['winding_consistent'] and stat['components']==1 and stat['degenerate']==0 and stat['min_normal_dot']>.99 and not duplicate
 out.write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--baseline',type=Path,required=True);a.add_argument('--candidate',type=Path,required=True);a.add_argument('--output',type=Path,required=True);v=a.parse_args();verify(v.baseline,v.candidate,v.output)
