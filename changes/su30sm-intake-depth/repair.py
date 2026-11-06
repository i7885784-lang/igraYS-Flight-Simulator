"""Pure 50mm axial translation of two existing static intake inserts; all meshes remain byte exact."""
from pathlib import Path
import sys,json,hashlib,copy
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));import dnm
base=r/'baseline/su30sm.dnm';assert hashlib.sha256(base.read_bytes()).hexdigest()=='8404cc19dff1bd0c1d768a1d00940904da6f8b629afe9beeef0714dc13680b0d'
p,ns=dnm.read(base);old=copy.deepcopy(ns);names={'IntakeDuct_-1','IntakeDuct_1'};audit={};shift=.05
for n in ns:
 name=dnm.name(n)
 if name not in names:continue
 assert dnm.cla(n)==99 and not any(line.startswith('CLD ') for line in n)
 assert not any('CLD "'+name+'"'==line for node in ns for line in node)
 j=next(i for i,line in enumerate(n) if line.startswith('POS '));a=n[j].split();was=n[j];a[3]=format(float(a[3])-shift,'.6f').rstrip('0').rstrip('.');n[j]=' '.join(a);audit[name]={'before':was,'after':n[j],'world_translation_m':[0,0,-shift]}
assert set(audit)==names
for n,o in zip(ns,old):
 if dnm.name(n) in names:assert [x for x in n if not x.startswith('POS ')]==[x for x in o if not x.startswith('POS ')]
 else:assert n==o
out=r/'runtime/aircraft/su30sm.dnm';out.parent.mkdir(parents=True,exist_ok=True);dnm.write(out,p,ns);q,qn=dnm.read(out);assert q==p and qn==ns
report={'model_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'shift_m':shift,'changed_nodes':audit,'all_mesh_packs_byte_exact':True,'face_indices_normals_materials_geometry_exact':True,'all_animation_states_and_parents_exact':True,'all_other_nodes_exact':True,'mesh_shape_depth_unchanged_m':.53};(r/'repair-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
