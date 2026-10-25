from pathlib import Path
import json,math,hashlib,re,struct,itertools,copy
import dnm
from mesh import Mesh
from gear_v3 import cut_bay
lab=Path(__file__).resolve().parent;rt=lab/'runtime';checks={};details={};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
trial=Mesh();trial.face([(0,0,0),(1,0,0),(1,0,1)],(100,120,140));trial.face([(0,1,0),(1,1,0),(1,1,1)],(100,120,140),True);checks['serializer_retains_sunlight']=[a[2] for a in dnm.mesh(trial.srf()).f]==[False,True]
for kind in ['su27','mig29']:
 p,n=dnm.read(rt/f'aircraft/{kind}.dnm');names={dnm.name(a) for a in n};checks[kind+'_node_graph']=len(names)==len(n) and all(x[4:].strip('"') in names for a in n for x in a if x.startswith('CLD '))
 meshes=[dnm.mesh(p[dnm.fil(a)]) for a in n]
 checks[kind+'_surface_validity']=all(all(math.isfinite(q) for v in m.v for q in v) and all(len(ids)>=3 and all(0<=i<len(m.v) for i in ids) for ids,c,b in m.f) for m in meshes)
 checks[kind+'_lit_skin']=all('B' not in p[dnm.fil(a)] for a in n if dnm.cla(a) not in [2,30,31,32,33,34,35,110,111])
 checks[kind+'_LOD_matches']=(rt/f'aircraft/{kind}.dnm').read_bytes()==(rt/'aircraft'/('su27coarse.dnm' if kind=='su27' else 'mig29_coarse.dnm')).read_bytes()
 checks[kind+'_two_nose_leaves']=sum(dnm.cla(a)==143 for a in n)==2
 # Every removed shell vertex has BOTH a wall lip and a back vertex in the new liner.
 bp,bn=dnm.read(lab.parent/f'aircraft-lab2/runtime/aircraft/{kind}.dnm');skin=dnm.mesh(bp[dnm.fil(bn[0])])
 if kind=='su27':
  def front(v):
   x,y,z=v;f=max(0,min(1,(z-5.6)/1.1));f=f*f*(3-2*f);return x*(1-.2*f),.575+(y-.575)*(1-.17*f),z
  skin.v=[front(v) for v in skin.v]
 gs=json.loads((lab.parent/'aircraft-lab5/model-stats.json').read_text())[kind+'_gear']
 for cfg in gs:
  title=cfg['leg'];_,cut=cut_bay(copy.deepcopy(skin),cfg['rect'],title!='Nose',(.22,-.59) if kind=='su27' else (.14,-.93));well=dnm.mesh(p['Bay_'+title+'.srf']);offset=(0,.31,0) if title=='Nose' else ((.30 if title=='Left' else -.30),0,0)
  distance=lambda v:min(math.dist(v,w) for w in well.v)
  err=max(distance(tuple(v[k]+o[k] for k in range(3))) for ids,c,b in cut.f for v in [cut.v[i] for i in ids] for o in [(0,0,0),offset]);checks[kind+'_'+title+'_sealed_cavity_lip_and_back']=err<2e-6
 details[kind+'_nose_wheel_diameter_m']=gs[0]['radius']*2;details[kind+'_wheel_contact_y_m']=[a['contact_y'] for a in gs]
 for mechanism in ['gear','canopy']:
  result=json.loads((lab/f'captures/{kind}/after/real-{mechanism}/results.json').read_text());checks[kind+'_real_'+mechanism]=result['passed']
 # Hot start on the ground, with functional canopy and no forced parking brake.
 log=(lab/f'captures/{kind}/after/real-canopy/cycle.log').read_text(errors='replace');rows=[{k:float(v) for k,v in re.findall(r'(\w+)=(-?[0-9.]+)',line)} for line in log.splitlines() if line.startswith('SU27CHECK ')]
 checks[kind+'_ground_ready_engines']=bool(rows) and all(a['factor']>.999 and a['L']>.999 and a['R']>.999 and a['parking']==0 for a in rows)
 details[kind+'_hot_start']=rows[0] if rows else {}
 flame=[a for a in n if dnm.cla(a) in [110,111]];checks[kind+'_two_emissive_AB_plumes']=len(flame)==2 and all(all(b for ids,c,b in dnm.mesh(p[dnm.fil(a)]).f) for a in flame)
 if kind=='su27':
  rad=dnm.mesh(p['SU27_Radome.srf']);body=dnm.mesh(p[dnm.fil(n[0])]);edges=[]
  for ids,c,b in body.f:
   vs=[body.v[i] for i in ids]
   edges.extend((a,b) for a,b in zip(vs,vs[1:]+vs[:1]) if a[2]>6.68 and b[2]>6.68)
  def dist(pt,a,b):
   ab=[b[k]-a[k] for k in range(3)];d=sum(v*v for v in ab);t=max(0,min(1,sum((pt[k]-a[k])*ab[k] for k in range(3))/d)) if d else 0;return math.sqrt(sum((pt[k]-a[k]-t*ab[k])**2 for k in range(3)))
  error=max(min(dist(v,a,b) for a,b in edges) for v in rad.v if v[2]<6.74);details['nose_joint_max_gap_m']=error;checks['su27_nose_joint']=error<2e-6
  checks['su27_compact_nose']=max(abs(v[0]) for v in rad.v)<.521 and max(v[2] for v in rad.v)<=10.55
  checks['su27_single_canopy_shell']=sum(dnm.cla(a)==100 for a in n)==1
  checks['su27_articulated_brake_cylinder_and_piston']=sum(dnm.cla(a) in [160,161] for a in n)==2 and all('NST 21' in a for a in n if dnm.cla(a) in [160,161])
  ds=[a['length'] for a in json.loads((lab/'upgrade-stats.json').read_text())['brake_actuator_samples']];checks['su27_actuator_overlap_all_sampled_states']=all(.82<d<.82+1.32 for d in ds);details['brake_actuator_anchor_distances_m']=[min(ds),max(ds)]
checks['su27_real_brake']=json.loads((lab/'captures/su27/after/real-brake/results.json').read_text())['passed']
checks['su27_empty_first_person_shell']=(rt/'aircraft/su27cockpit.srf').read_text().strip()=='SURF\nE' and 'aircraft/su27cockpit.srf' in (rt/'aircraft/aircraft.lst').read_text() and 'INSTPANL' not in (rt/'aircraft/su27.dat').read_text()
lines=[x.split() for x in (rt/'aircraft/mig29.dat').read_text().splitlines() if x.startswith('HRDPOINT')];checks['mig29_seven_stores_one_center']=len(lines)==7 and sum(abs(float(a[1].rstrip('m')))<.01 for a in lines)==1
for typ,file in [('AIM9','aim9s.srf'),('AIM9X','aim9xs.srf'),('AIM120','aim120s.srf')]:
 m=dnm.mesh((rt/'misc'/file).read_text().splitlines());sz=[max(v[k] for v in m.v)-min(v[k] for v in m.v) for k in range(3)];points=[tuple(float(v.rstrip('m')) for v in a[1:4]) for a in lines if typ in a[4:]];checks['mig29_'+typ+'_no_store_overlap']=not any(all(abs(a[k]-b[k])<sz[k]+.01 for k in range(3)) for a,b in itertools.combinations(points,2))
b=(rt/'ysflight32_gl1.exe').read_bytes();pe=struct.unpack_from('<I',b,0x3c)[0];checks['production_win32_GUI']=struct.unpack_from('<H',b,pe+4)[0]==0x14c and struct.unpack_from('<H',b,pe+24+68)[0]==2;checks['new_hotstart_executable']=sha(rt/'ysflight32_gl1.exe')!=sha(lab.parent/'aircraft-lab5/runtime/ysflight32_gl1.exe');checks['no_lab_instrumentation_in_production']=b'MODELCHECK t=' not in b and b'ARMAMENTCHECK time=' not in b
result={'passed':all(checks.values()),'checks':checks,'details':details,'model_sha256':{k:sha(rt/f'aircraft/{k}.dnm') for k in ['su27','mig29']},'exe_sha256':sha(rt/'ysflight32_gl1.exe')};(lab/'checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['passed']
