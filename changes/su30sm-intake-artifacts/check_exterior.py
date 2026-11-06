from pathlib import Path
import sys,json,hashlib
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));import dnm
p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm');old,on=dnm.read(r/'baseline/su30sm.dnm');assert ns==on
fn='Fuselage_0_4.srf'
def faces(ls):
 out=[];i=ls.index('F')
 while i<len(ls) and ls[i]=='F':j=ls.index('E',i);out.append(tuple(ls[i:j+1]));i=j+1
 return out
source=faces(old[fn]);result=set(faces(p[fn]));ids=json.loads((r/'repair-audit.json').read_text())['Fuselage_0_4']['protected_source_face_ids'];assert len(ids)>0
for i in ids:assert source[i] in result,i
report={'model_sha256':hashlib.sha256((r/'runtime/aircraft/su30sm.dnm').read_bytes()).hexdigest(),'protected_original_F4_face_blocks':len(ids),'all_protected_face_blocks_byte_identical':True,'selection':'Conservative original outside-X/bottom-Y source envelopes, centroid and inset-vertex samples, 1mm tolerance; missing chart samples protect, never invent a height','full_continuous_visibility_proof':False};(r/'exterior-protection.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
