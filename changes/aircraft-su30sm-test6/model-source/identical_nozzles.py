from pathlib import Path
import numpy as np,json
from common import dnm,state,transform
r=Path(__file__).resolve().parent.parent
p,ns=dnm.read(r/'source-stage.dnm');M=np.diag([-1.,1.,1.])
left=[];right=[]
for n in ns:
 if dnm.cla(n)!=270:continue
 pos=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float)
 (left if pos[0]<0 else right).append(n)
assert len(left)==len(right)==32
for a,b in zip(left,right):
 mesh=dnm.mesh(p[dnm.fil(a)]);mesh.v=[tuple(M@v) for v in mesh.v];mesh.f=[(ids[::-1],c,bright) for ids,c,bright in mesh.f]
 p[dnm.fil(b)]=mesh.srf()
 pos=np.array(next(s[4:] for s in a if s.startswith('POS ')).split()[:3],float);b[:]=dnm.edit(b,'POS ',' '.join(map(str,M@pos))+' 0 0 0 1')
 ia=[i for i,s in enumerate(b) if s.startswith('STA ')];assert len(ia)==21
 for i,idx in enumerate(ia):
  R,t=transform(a,i);b[idx]=state(M@R@M,M@t)
dnm.write(r/'source-stage.dnm',p,ns)
(r/'nozzle-symmetry.json').write_text(json.dumps({'same_reference_meshes':True,'pairs':32,'states_per_pair':21,'operation':'mirror X of left mesh, pivot, states; reverse face winding'},indent=2))
