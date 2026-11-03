from pathlib import Path
import sys,numpy as np,json,hashlib,zipfile
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import dnm,transform
p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm');M=np.diag([-1.,1.,1.]);left=[];right=[]
assert not any(' R ' in s for ls in p.values() for s in ls if s.startswith('V ')), 'Smooth normal found'
for n in ns:
 if dnm.cla(n)!=270:continue
 pos=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);(left if pos[0]<0 else right).append((n,pos))
assert len(left)==len(right)==32
for (a,pa),(b,pb) in zip(left,right):
 va=np.array(dnm.mesh(p[dnm.fil(a)]).v);vb=np.array(dnm.mesh(p[dnm.fil(b)]).v);assert np.max(abs(va@M-vb))<1e-6;assert np.max(abs(M@pa-pb))<1e-6
 for k in range(21):
  A,x=transform(a,k);B,y=transform(b,k);assert np.max(abs(M@A@M-B))<.0002
meta=json.loads((r/'conversion.json').read_text());assert meta['source_triangles']==418250
for key in ['release-photos','release-gear','release-engine']:
 q=r/'checks'/key/'results.json';assert json.loads(q.read_text())['passed'],key
checks={'scope':'targeted visual and mechanism test, user acceptance pending','flat_shading':True,'original_source_triangles':418250,'decimation':False,'identical_nozzle_pairs':32,'states_per_nozzle':21,'symmetry_mesh_tolerance_m':.000001,'main_box_drop_m':0,'stowed_fit':json.loads((r/'stowed-fit.json').read_text()),'native_linux_wine64':{key:json.loads((r/'checks'/key/'results.json').read_text()) for key in ['release-photos','release-gear','release-engine']},'limits':['Gear is an approximation; no factory kinematics claim.','No claim that all internal surface contacts are eliminated.','Flight dynamics inherited from Su27.','Dry exhaust is transparent geometry, not refractive heat haze.']}
checks['expected_models']={n:hashlib.sha256((r/'runtime/aircraft'/n).read_bytes()).hexdigest() for n in ['su30sm.dnm','su30smcoll.srf','su30smcockpit.dnm','su30sm.dat','air_su30sm.lst']}
(r/'CHECKS.json').write_text(json.dumps(checks,indent=2));print('Flat shading and all 32 mirrored nozzle pairs verified; native gear/engine checks passed.')
