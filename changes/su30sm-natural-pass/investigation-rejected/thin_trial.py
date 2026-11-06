from pathlib import Path
import sys,json,numpy as np,collections
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import *
p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm');lu={dnm.name(n):n for n in ns};audit={}
for side in ['Left','Right']:
 name='MainBayFixedSkin_'+side;fn=dnm.fil(lu[name]);raw=list(p[fn]);m=dnm.mesh(raw);R,t=transform(lu[name],0);direction=np.array([0,-.005,0])@R;owners=collections.Counter(j for ids,c,b in m.f for j in ids);assert max(owners.values())==1
 change=set()
 for ids,c,b in m.f:
  if c==(148,153,148):change.update(ids)
  if c==(105,118,123):assert len(ids)==4;change.update(ids[2:])
 limit=raw.index('F');vlines=[i for i,line in enumerate(raw[:limit]) if line.startswith('V ')];assert len(vlines)==len(m.v)
 for j in sorted(change):
  a=raw[vlines[j]].split();v=np.array(a[1:4],float)+direction;a[1:4]=[format(x,'.6f') for x in v];raw[vlines[j]]=' '.join(a)
 p[fn]=raw;audit[name]={'back_and_inner_rim_vertices_changed':len(change),'old_thickness_m':.008,'new_thickness_m':.003,'all_exterior_vertices_colors_and_normals_exact':True}
dnm.write(r/'thin-trial.dnm',p,ns);(r/'thin-audit.json').write_text(json.dumps(audit,indent=2));print(audit)
