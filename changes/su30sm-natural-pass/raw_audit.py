from pathlib import Path
import sys,json,numpy as np,collections
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));import dnm
p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm');stats={};invalid=[];nonfinite=[]
for pack,lines in p.items():
 m=dnm.mesh(lines);v=np.asarray(m.v);deg=0;count=0
 if not len(v):continue
 if not np.isfinite(v).all():nonfinite.append(pack)
 for ids,c,b in m.f:
  if not all(0<=i<len(v) for i in ids):invalid.append(pack);continue
  for k in range(1,len(ids)-1):
   q=v[[ids[0],ids[k],ids[k+1]]];deg+=int(np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))<1e-12);count+=1
 stats[pack]={'raw_fan_triangles':count,'degenerate':deg}
assert not invalid and not nonfinite
out={'packs':len(p),'nodes':len(ns),'invalid_index_packs':invalid,'nonfinite_packs':nonfinite,'unfiltered_degenerate_triangle_count':sum(s['degenerate'] for s in stats.values()),'packs_with_degenerate_triangles':{k:v for k,v in stats.items() if v['degenerate']},'per_pack':stats};(r/'raw-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='per_pack'})
