from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path(__file__).parent/'model-source'))
import dnm
import numpy as np
r=Path(__file__).parent;p,ns=dnm.read(r/'baseline/su30sm.dnm');old={k:list(v) for k,v in p.items()};audit={}
for name in ['GearWell_Left','GearWell_Right']:
 node=next(n for n in ns if dnm.name(n)==name);key=dnm.fil(node);lines=p[key];verts=np.array([list(map(float,s.split()[1:4])) for s in lines if s.startswith('V ')]);out=[];removed=[];i=0
 while i<len(lines):
  if lines[i]!='F':out.append(lines[i]);i+=1;continue
  j=lines.index('E',i);face=lines[i:j+1];ids=list(map(int,next(s[2:] for s in face if s.startswith('V ')).split()));q=verts[ids]
  # Front cap of the gear well crossing the intake: z ~ -0.39m,
  # with lower vertices below the intake upper lip. Do not touch other faces.
  bad=bool(np.all((q[:,2]>-.42)&(q[:,2]<-.38)) and np.ptp(q[:,2])<.003 and np.ptp(q[:,1])>.40 and q[:,1].min()<-.15)
  if bad:removed.append({'original_line':i+1,'vertex_indices':ids,'face_block_sha256':hashlib.sha256('\n'.join(face).encode()).hexdigest()})
  else:out.extend(face)
  i=j+1
 assert removed,name;p[key]=out;audit[name]={'removed_faces':removed,'vertex_records_unchanged': [s for s in lines if s.startswith('V ')]==[s for s in out if s.startswith('V ')]}
# Exact text equality for all other packed meshes and the entire node hierarchy.
changed=[k for k in p if p[k]!=old[k]];assert len(changed)==2
output=r/'runtime/aircraft/su30sm.dnm';dnm.write(output,p,ns);pp,nn=dnm.read(output);assert nn==ns
for k in old:
 if k not in changed:assert pp[k]==old[k]
report={'changed_packs':changed,'nodes_transforms_states_hierarchy_unchanged':True,'all_other_meshes_exactly_unchanged':True,'audit':audit,'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest()};(r/'audit.json').write_text(json.dumps(report,indent=2));print({n:len(v['removed_faces']) for n,v in audit.items()})
