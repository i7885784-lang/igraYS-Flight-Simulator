from pathlib import Path
import sys,json,numpy as np
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import dnm,transform
p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm');lu={dnm.name(n):n for n in ns};v=[]
for n in ns:
 name=dnm.name(n)
 if name.startswith(('Gear','Wheel','Door','Su30Plume','Su30Dry','Su30Nozzle','Intake','MainBay','AirbrakeActuator','AirbrakeBay','Su30Interior')):continue
 m=dnm.mesh(p[dnm.fil(n)])
 if not m.v:continue
 R,t=transform(n,0);pos=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);v.extend(np.array(m.v)@R.T+t+pos)
v=np.array(v);lo,hi=v.min(0),v.max(0);L=transform(lu['WheelCarrier_Left'],100)[1];R=transform(lu['WheelCarrier_Right'],100)[1];N=transform(lu['WheelCarrier_Nose'],100)[1]
actual={'length_m':float(hi[2]-lo[2]),'wingspan_m':float(hi[0]-lo[0]),'height_m':float(hi[1]+2.52),'wheelbase_m':float(N[2]-(L[2]+R[2])/2),'main_track_m':float(R[0]-L[0])}
dat=(r/'runtime/aircraft/su30sm.dat').read_text().splitlines()
for key,centre in [('LEFTGEAR',L),('RIGHGEAR',R),('WHELGEAR',N)]:
 values=np.array([float(s.rstrip('m')) for s in next(line for line in dat if line.startswith(key+' ')).split()[1:4]])
 assert np.max(abs(values[[0,2]]-centre[[0,2]]))<1e-6 and abs(values[1]+2.52)<1e-6, 'Physics contact mismatches visual wheel: '+key
ref=json.loads((r/'drawing-dimensions.json').read_text());out={'actual':actual,'reference':ref,'difference_m':{k:actual[k]-ref[k] for k in actual},'main_centres':[L.tolist(),R.tolist()],'nose_centre':N.tolist(),'no_smoothing_normals':not any(' R ' in s for lines in p.values() for s in lines if s.startswith('V '))}
assert abs(actual['wheelbase_m']-5.57)<1e-5 and abs(actual['main_track_m']-4.1)<1e-5
assert abs(actual['wingspan_m']-14.7)<1e-4 and abs(actual['height_m']-6.36)<.01
assert out['no_smoothing_normals'];(r/'dimensions.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
