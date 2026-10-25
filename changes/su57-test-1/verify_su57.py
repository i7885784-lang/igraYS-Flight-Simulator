from pathlib import Path
import math,json,hashlib,struct,re
import numpy as np
from PIL import Image
import dnm
from mesh import Mesh
from collision_su57 import rotation
lab=Path(__file__).resolve().parent;rt=lab/'runtime';base=lab.parent/'aircraft-lab6/runtime';packs,nodes=dnm.read(rt/'aircraft/su57.dnm');byname={dnm.name(a):a for a in nodes};checks={};details={};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parents={v[4:].strip('"'):dnm.name(a) for a in nodes for v in a if v.startswith('CLD ')}
checks['unique_node_names']=len(nodes)==len(byname);checks['valid_parent_references']=all(x in byname for x in parents) and all(x in byname for x in parents.values());checks['matching_close_and_far_models']=(rt/'aircraft/su57.dnm').read_bytes()==(rt/'aircraft/su57_coarse.dnm').read_bytes()
for name in byname:
 seen=set();cur=name
 while cur in parents:
  assert cur not in seen;seen.add(cur);cur=parents[cur]
checks['acyclic_node_graph']=True
meshes={name:dnm.mesh(packs[dnm.fil(a)]) for name,a in byname.items()};checks['finite_valid_geometry']=all(all(math.isfinite(t) for v in m.v for t in v) and all(len(ids)>=3 and all(0<=i<len(m.v) for i in ids) for ids,c,b in m.f) for m in meshes.values());checks['skin_uses_sunlight']=all(not any(b for ids,c,b in meshes[name].f) for name,a in byname.items() if dnm.cla(a) not in [30,110,111])
trial=Mesh();trial.face([(0,0,0),(1,0,0),(1,0,1)],(100,120,140));trial.face([(0,1,0),(1,1,0),(1,1,1)],(100,120,140),True);checks['emission_flag_roundtrip']=[x[2] for x in dnm.mesh(trial.srf()).f]==[False,True]
def transform(name):
 a=byname[name];v=list(map(float,next(x[4:] for x in a if x.startswith('POS ')).split()));R=rotation(v[3:6]);T=np.array(v[:3])
 if name in parents:
  rr,tt=transform(parents[name]);T=tt+rr@T;R=rr@R
 return R,T
points=[]
for name,a in byname.items():
 if dnm.cla(a) in [110,111,140,141,142,143,144,145,146,147,151]:continue
 R,T=transform(name);points += [T+R@np.array(v) for v in meshes[name].v]
pts=np.array(points);low=pts.min(axis=0);high=pts.max(axis=0);details['measured_length_m']=float(high[2]-low[2]);details['measured_span_m']=float(high[0]-low[0]);details['height_with_gear_m']=float(high[1]+2.0)
checks['length_20_1m']=abs(details['measured_length_m']-20.1)<.03;checks['span_14_1m']=abs(details['measured_span_m']-14.1)<.03;checks['height_about_4_6m']=abs(details['height_with_gear_m']-4.6)<.08
checks['all_14_control_surface_classes']=all(any(dnm.cla(a)==c for a in nodes) for c in range(180,194));checks['no_su27_dorsal_brake']=not any(dnm.cla(a)==4 for a in nodes);checks['four_gear_door_leaves']=sum(dnm.cla(a)==143 for a in nodes)==2 and sum(dnm.cla(a) in [144,145] for a in nodes)==2
# Fins must lean away from centre, not towards one another.
for label,sg in [('L',-1),('R',1)]:
 name='Fin_'+label;R,T=transform(name);tip=T+R@np.array([0,2.23,-.03]);checks['fin_'+label+'_canted_outward']=sg*(tip[0]-T[0])>.5
stats=json.loads((lab/'model-stats.json').read_text());checks['all_wheels_touch_same_ground']=all(abs(a['contact_y']+2.0)<1e-8 for a in stats['gear']);checks['all_bays_have_real_cuts_and_doors']=all(a['cut_faces']>0 and a['exterior_door_faces']>0 for a in stats['gear'])
# Sample stowing motion against the actual x/z bay openings whenever wheel is inside hull height.
for cfg in stats['gear']:
 title=cfg['title'];P=np.array(cfg['pivot']);A=np.array(cfg['wheel_center'])-P;x0,x1,z0,z1=cfg['rect'];radius=cfg['radius'];margin=0
 okay=True
 for q in np.linspace(.001,1,101):
  leg=max(0,min(1,(q-.12)/.88));theta=(1-leg)*math.pi/2;R=rotation([0,theta*32768/math.pi,0]);C=P+R@A
  if C[1]+radius>-.8:
   # Wheel thickness along X; two nose wheels each 0.20m wide.
   width=.25 if title=='Nose' else .10
   okay &= x0+.005<C[0]-width and C[0]+width<x1-.005 and z0-.025<C[2]-radius and C[2]+radius<z1+.025
 checks[title+'_wheel_path_within_bay']=bool(okay)
for mechanism in ['gear','canopy']:checks['native_'+mechanism+'_out_and_back']=json.loads((lab/f'captures/su57/after/real-{mechanism}/results.json').read_text())['passed']
controls=json.loads((lab/'captures/su57/after/live-controls/results.json').read_text());checks['native_keyboard_all_six_directions_flap_brake']=controls['passed'];details['native_input_checks']=controls['checks']
videos=json.loads((lab/'videos/checks.json').read_text());checks['three_live_videos_decoded']=videos['passed'] and len(videos['native_end_states'])==3
canopylog=(lab/'captures/su57/after/real-canopy/cycle.log').read_text(errors='replace');states=[{k:float(v) for k,v in re.findall(r'(\w+)=(-?[0-9.]+)',line)} for line in canopylog.splitlines() if line.startswith('SU27CHECK ')];checks['ground_start_ready']=bool(states) and all(v['factor']==1 and v['L']==1 and v['R']==1 and v['parking']==0 for v in states)
for kind in ['su27','mig29']:checks[kind+'_existing_model_preserved']=sha(rt/f'aircraft/{kind}.dnm')==sha(base/f'aircraft/{kind}.dnm') and sha(rt/f'aircraft/{kind}.dat')==sha(base/f'aircraft/{kind}.dat')
col=dnm.mesh((rt/'aircraft/su57coll.srf').read_text().splitlines());cs=np.array(col.v);checks['collision_includes_wings_fins_and_canopy']=cs[:,0].max()>7.04 and cs[:,0].min()<-7.04 and cs[:,1].max()>2.55 and cs[:,2].max()>10 and cs[:,2].min()<-10;checks['collision_is_simplified']=len(col.f)<2000;details['collision_faces']=len(col.f)
# Same underside receives direct sun after inversion.
means=[]
for name in ['shaded-bottom','inverted-bottom']:
 im=np.asarray(Image.open(lab/f'captures/su57/after/lighting/{name}.png').convert('RGB'),dtype=float)[140:760,180:1100];r,g,b=im[:,:,0],im[:,:,1],im[:,:,2];mask=(r>.68*g)&(b>.9*g)&(r<220);lum=.2126*r+.7152*g+.0722*b;means.append(float(lum[mask].mean()))
checks['underside_darkens_away_from_sun']=means[1]>means[0]*1.35;details['underside_shadow_sun_luminance']=means
binary=(rt/'ysflight32_gl1.exe').read_bytes();pe=struct.unpack_from('<I',binary,0x3c)[0];checks['Win32_GUI_build']=struct.unpack_from('<H',binary,pe+4)[0]==0x14c and struct.unpack_from('<H',binary,pe+24+68)[0]==2;checks['production_has_no_validation_commands']=b'MODELCHECK t=' not in binary and b'ARMAMENTCHECK time=' not in binary
checks['new_aircraft_is_registered']='aircraft/su57.dat aircraft/su57.dnm' in (rt/'aircraft/aircraft.lst').read_text();checks['clean_keyboard_default']='REM PRIMARYINPUT KEYBOARD' in (rt/'config/ctlassign.cfg').read_text() and 'KEY LEFT AILERONLEFT' in (rt/'config/ctlassign.cfg').read_text()
checks={k:bool(v) for k,v in checks.items()}
result={'passed':all(checks.values()),'checks':checks,'details':details,'model_sha256':sha(rt/'aircraft/su57.dnm'),'exe_sha256':sha(rt/'ysflight32_gl1.exe')};(lab/'checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));assert result['passed']
