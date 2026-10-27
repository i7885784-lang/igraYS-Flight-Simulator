from pathlib import Path
import sys,numpy as np,json
lab=Path(__file__).resolve().parent;sys.path.insert(0,str(lab/'model-source'));import dnm
out={}
for kind in ['su27','mig29']:
 oldp,oldn=dnm.read(lab.parent/'internal-gear-test-3/runtime/aircraft'/(kind+'.dnm'));newp,newn=dnm.read(lab/'runtime/aircraft'/(kind+'.dnm'));assert oldn==newn
 count=0
 for fn,lines in newp.items():
  if not fn.startswith('FlushGearDoor'):assert lines==oldp[fn];continue
  m=dnm.mesh(lines);old=dnm.mesh(oldp[fn]);assert sorted(m.v)==sorted(old.v) and len(m.f)==len(old.f)
  for i in range(0,len(m.f)-1,2):
   ids,c,b=m.f[i]
   if len(ids)!=3:break
   q=np.array([m.v[j] for j in ids]);assert np.cross(q[1]-q[0],q[2]-q[0])[1]<=1e-12
   count+=1
 out[kind]={'unchanged_positions_and_animation':True,'exterior_triangles_face_down':count}
(lab/'lighting-checks.json').write_text(json.dumps({'passed':True,'aircraft':out},indent=2));print(out)
