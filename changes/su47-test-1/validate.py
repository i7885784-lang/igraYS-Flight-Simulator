from pathlib import Path
import sys,json,math,hashlib
import numpy as np
from PIL import Image
lab=Path(__file__).resolve().parent;sys.path.insert(0,str(lab/'portable-source'));import dnm
(lab/'validation.json').unlink(missing_ok=True)
rt=lab/'runtime/aircraft';packs,nodes=dnm.read(rt/'su47.dnm');meshes={dnm.name(n):dnm.mesh(packs[dnm.fil(n)]) for n in nodes};result={}
result['finite_valid_faces']=all(all(all(math.isfinite(x) for x in v) for v in m.v) and all(len(ids)>=3 and all(0<=i<len(m.v) for i in ids) for ids,c,b in m.f) for m in meshes.values())
result['unique_nodes']=len(nodes)==len(meshes)
result['all_twelve_control_classes']=all(any(dnm.cla(n)==c for n in nodes) for c in range(180,192))
result['gear_doors_canopy_present']=all(any(dnm.cla(n)==c for n in nodes) for c in [100,140,141,142,143,144,145,151])
result['no_assumed_nozzle_vectoring']=not any(dnm.cla(n) in [192,193] for n in nodes)
result['only_flames_emissive']=all(not any(b for inds,c,b in m.f) for name,m in meshes.items() if not name.startswith('Afterburner'))
result['forty_throttle_driven_nozzle_petals']=sum(dnm.name(n).startswith('NozzlePetal') and dnm.cla(n)==120 for n in nodes)==40
centers=np.mean([list(map(float,next(v[4:] for v in n if v.startswith('POS ')).split()[:3])) for n in nodes if dnm.name(n).startswith('NozzlePetalL')],axis=0)
n=next(n for n in nodes if dnm.name(n)=='NozzlePetalL0');m=meshes['NozzlePetalL0'];v=np.array(m.v);tip=v[v[:,2]<v[:,2].min()+.001].mean(0);pivot=np.array(list(map(float,next(v[4:] for v in n if v.startswith('POS ')).split()[:3])))
radii=[]
for st in [v for v in n if v.startswith('STA ')]:
 h,pp,b=[float(a)*math.pi/32768 for a in st.split()[4:7]];ch,sh,cp,sp,cb,sb=math.cos(h),math.sin(h),math.cos(pp),math.sin(pp),math.cos(b),math.sin(b)
 R=np.array([[ch,0,-sh],[0,1,0],[sh,0,ch]])@np.array([[1,0,0],[0,cp,sp],[0,-sp,cp]])@np.array([[cb,-sb,0],[sb,cb,0],[0,0,1]])
 q=R@tip+pivot;radii.append(float(np.linalg.norm(q[:2]-centers[:2])))
result['serialized_nozzle_aperture_opens']=radii[1]>radii[0]+.10
result['coarse_model_matches']=(rt/'su47.dnm').read_bytes()==(rt/'su47_coarse.dnm').read_bytes()
col=dnm.mesh((rt/'su47coll.srf').read_text().splitlines());q=np.array(col.v);result['collider_covers_wings_fins_nose_tail']=bool(q[:,0].max()>8.2 and q[:,0].min()<-8.2 and q[:,1].max()>3.2 and q[:,2].max()>11.2 and q[:,2].min()<-11.2)
base=lab.parent/'YSFlight_Su57_Test_2_32bit/aircraft';result['old_three_aircraft_preserved']=all((rt/f'{name}.{ext}').read_bytes()==(base/f'{name}.{ext}').read_bytes() for name in ['su27','mig29','su57'] for ext in ['dat','dnm'])
rows={}
for case in ['gear','canopy','controls','engine']:
 j=json.loads((lab/'checks'/case/'results.json').read_text());assert j['passed'];states=j['states'];rows[case]={key:[min(float(s[key]) for s in states),max(float(s[key]) for s in states),float(states[-1][key])] for key in ['gear','canopy','elevator','aileron','rudder','flap']}
result['native_engine_throttle_0_to_1']=min(float(s['throttle']) for s in json.loads((lab/'checks/engine/results.json').read_text())['states'])<.01 and max(float(s['throttle']) for s in json.loads((lab/'checks/engine/results.json').read_text())['states'])>.99
result['native_gear_out_back']=rows['gear']['gear'][0]<.01 and rows['gear']['gear'][1]>.99 and rows['gear']['gear'][2]<.01
result['native_canopy_out_back']=rows['canopy']['canopy'][0]<.01 and rows['canopy']['canopy'][1]>.99 and rows['canopy']['canopy'][2]<.01
result['native_six_control_directions']=all(rows['controls'][k][0]<-.95 and rows['controls'][k][1]>.95 for k in ['elevator','aileron','rudder'])
result['native_flap_full_travel']=rows['controls']['flap'][0]<.01 and rows['controls']['flap'][1]>.99 and rows['controls']['flap'][2]<.01
levels={}
for n in ['bottom','inverted']:
 a=np.array(Image.open(lab/'checks/inspect'/f'{n}.png').convert('RGB'),dtype=float);r,g,b=a[:,:,0],a[:,:,1],a[:,:,2];m=(r<120)&(g<120)&(b<140)&(r>.65*g)&(b<1.6*g)&(g>8);levels[n]=float((.2126*r+.7152*g+.0722*b)[m].mean())
result['underside_responds_to_sun']=levels['inverted']>levels['bottom']*1.25
flames={}
for at in [4,7,11,14]:
 a=np.array(Image.open(lab/f'checks/engine/engine-{at:02}.png'));flames[at]=int(((a[:,:,0]>170)&(a[:,:,1]>80)&(a[:,:,1]<210)&(a[:,:,2]<115)).sum())
result['native_afterburner_visible_and_off']=min(flames[4],flames[7])>500 and max(flames[11],flames[14])<50
for ident in ['SU-27_FLANKER','MIG-29_FULCRUM','SU-57_FELON']:result['smoke_'+ident]=json.loads((lab/'checks'/('smoke-'+ident)/'results.json').read_text())['passed']
report={'passed':all(result.values()),'checks':result,'native_ranges':rows,'underside_mask_luminance':levels,'afterburner_pixels':flames,'nozzle_exit_radii_m_idle_full':radii,'collision_faces':len(col.f),'model_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in rt.glob('su47*') if p.is_file()},'limits':['Win64/Wine functional verification; no native Windows 10 x86 run','Visual mechanism clearance checks are not an exhaustive collision proof','Simplified flight parameters; no claim of real Su-47 performance']}
(lab/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert report['passed']
