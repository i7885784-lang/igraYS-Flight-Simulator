from pathlib import Path
import sys,json,hashlib,numpy as np,trimesh
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin/model-source'))
from common import dnm,transform
sha=lambda b:hashlib.sha256(b).hexdigest()
def verify(base,model,out):
 p,ns=dnm.read(base);q,nt=dnm.read(model);lu={dnm.name(n):n for n in nt};oldlu={dnm.name(n):n for n in ns}
 assert len(q)==len(p)+4 and all(q[k]==v for k,v in p.items());changed=[];maxrest=0.
 parents={s[4:].strip('"'):dnm.name(n) for n in nt for s in n if s.startswith('CLD ')}
 for n in ns:
  name=dnm.name(n);m=lu[name]
  if n==m:continue
  changed.append(name);omit=('POS ','CLA ') if name.startswith('Su30NozzleThroat_') else ('POS ',)
  assert [s for s in n if not s.startswith(omit)]==[s for s in m if not s.startswith(omit)]
  if name.startswith('Su30NozzleThroat_'):assert dnm.cla(m)==284+int(name.rsplit('_',1)[1])
  assert parents[name] in ['Su30NozzleGimbal_0','Su30NozzleGimbal_1']
  a=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);b=np.array(next(s[4:] for s in m if s.startswith('POS ')).split()[:3],float);c=np.array(next(s[4:] for s in lu[parents[name]] if s.startswith('POS ')).split()[:3],float);maxrest=max(maxrest,float(np.linalg.norm(b+c-a)))
 assert len(changed)==70 and maxrest<1e-10
 seals={}
 for side in range(2):
  name='Su30NozzleJointSeal_'+str(side);m=dnm.mesh(q[name+'.srf']);v,inv=np.unique(np.round(m.v,9),axis=0,return_inverse=True);f=np.array([[inv[ids[0]],inv[ids[j]],inv[ids[j+1]]] for ids,c,b in m.f for j in range(1,len(ids)-1)]);tm=trimesh.Trimesh(v,f,process=False);assert tm.is_watertight and tm.is_winding_consistent and tm.body_count==1 and tm.volume>0 and tm.area_faces.min()>1e-12
  seals[name]=dict(watertight=True,components=1,volume_m3=float(tm.volume),minimum_triangle_area_m2=float(tm.area_faces.min()))
  g=lu['Su30NozzleGimbal_'+str(side)];assert sum(s.startswith('STA ') for s in g)==61
  R,t=transform(g,0);assert np.max(abs(R-np.eye(3)))<1e-12
 # Check rendered gimbal axis against the force model independently, all encoded states.
 maxaxis=0.
 for side in range(2):
  g=lu['Su30NozzleGimbal_'+str(side)]
  for idx,a in enumerate([0]+[x*.5 for x in range(1,31)]+[-x*.5 for x in range(1,31)]):
   R,_=transform(g,idx);rad=np.deg2rad(a);cant=np.deg2rad(32)
   expected=np.array([(1 if side==0 else -1)*np.sin(cant)*np.sin(rad),-np.cos(cant)*np.sin(rad),np.cos(rad)])
   maxaxis=max(maxaxis,float(np.linalg.norm(R@np.array([0,0,1])-expected)))
 assert maxaxis<.00014 # DNM uses integer angle units pi/32768.
 result=dict(render_force_direction_max_error=maxaxis,baseline_sha256=sha(base.read_bytes()),model_sha256=sha(model.read_bytes()),all_original_packs_exact=len(p),original_nodes_exact=len(ns)-len(changed),nozzle_nodes_only_POS_rebased=len(changed),all_original_STA_CNT_PAX_exact=True,neutral_position_max_error_m=maxrest,new_nodes=[dnm.name(n) for n in nt if dnm.name(n) not in oldlu],new_seals=seals,protected_pack_sha256={k:sha(('\n'.join(v)+'\n').encode()) for k,v in p.items()})
 out.write_text(json.dumps(result,indent=2));print('PASS original SRFs/gear/cockpit unaffected; nozzle rig neutral pose exact; two closed seals')
if __name__=='__main__':verify(*map(Path,sys.argv[1:]))
