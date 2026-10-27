from pathlib import Path
import sys,json,hashlib,math,numpy as np
lab=Path(__file__).resolve().parent;sys.path.insert(0,str(lab/'model-source'));import dnm
from scipy.spatial.transform import Rotation
rt=lab/'runtime';checks=[]
def check(name,condition,detail=None):
 checks.append({'check':name,'passed':bool(condition),'detail':detail});assert condition,name
base=lab.parent/'su47-test-1/runtime'
for name in ['su47','su57']:
 files=[name+'.dat',name+'.dnm',name+'_coarse.dnm',name+'coll.srf',name+'cockpit.srf']
 check(name+' preserved byte for byte',all((rt/'aircraft'/p).read_bytes()==(base/'aircraft'/p).read_bytes() for p in files),files)
for kind,ident in [('su27','SU-27_FLANKER'),('mig29','MIG-29_FULCRUM')]:
 p,n=dnm.read(rt/'aircraft'/(kind+'.dnm'));classes=[dnm.cla(a) for a in n];meshes={k:dnm.mesh(v) for k,v in p.items()}
 check(kind+' unique nodes',len({dnm.name(a) for a in n})==len(n))
 check(kind+' finite valid geometry',all(m.f and np.isfinite(m.v).all() and all(len(f)>=3 and min(f)>=0 and max(f)<len(m.v) for f,c,b in m.f) for m in meshes.values()))
 check(kind+' moving systems present',all(c in classes for c in [210,211,212,220,221,226,228,229,110,111]),sorted(set(classes)))
 check(kind+' no emissive underside',all(not b or c[:3]==(238,133,57) for m in meshes.values() for f,c,b in m.f))
 gear=[a for a in n if dnm.cla(a)==210];check(kind+' sampled gear all 21 states',all(sum(s.startswith('STA ') for s in a)==21 for a in gear),len(gear))
 check(kind+' far LOD registration',kind+'_coarse.dnm' in (rt/'aircraft/aircraft.lst').read_text())
 check(kind+' datum and registration',('IDENTIFY '+ident) in (rt/'aircraft'/(kind+'.dat')).read_text().replace(chr(34),'') and kind+'.dnm' in (rt/'aircraft/aircraft.lst').read_text())
 # Check stowed main wheel height and ground wheel contacts from serialized DNM.
 values={}
 for a in gear:
  if dnm.name(a) not in ['UC_Main_Left_Tyre','UC_Main_Right_Tyre','wheel_L','wheel_R']:continue
  m=meshes[dnm.fil(a)];v=np.array(m.v);states=[s.split()[1:] for s in a if s.startswith('STA ')]
  s=states[0];t=np.array(s[:3],float);h,pi,b=np.array(s[3:6],float)*math.pi/32768;R=Rotation.from_euler('YXZ',[-h,-pi,b]).as_matrix();q=v@R.T+t;values[dnm.name(a)]={'stowed_min':q.min(0).tolist(),'stowed_max':q.max(0).tolist()}
 check(kind+' main wheels inside upper bay envelope',values and all(v['stowed_max'][1]<(.31 if kind=='su27' else .44) for v in values.values()),values)
 # Physical direction check: left roll lifts left trailing edge and lowers right.
 directions={}
 for cla,index in [(220,2),(221,1 if kind=='su27' else 2),(228,2),(229,2)]:
  a=next(a for a in n if dnm.cla(a)==cla);v=np.array(meshes[dnm.fil(a)].v);st=[x.split()[1:] for x in a if x.startswith('STA ')][index];t=np.array(st[:3],float);h,pi,b=np.array(st[3:6],float)*math.pi/32768;R=Rotation.from_euler('YXZ',[-h,-pi,b]).as_matrix();q=v@R.T+t;mask=v[:,2]<v[:,2].min()+.12;dy=float((q[mask,1]-v[mask,1]).mean());directions[str(cla)]=dy
 check(kind+' roll and pitch surface direction',directions['220']>0 and directions['221']<0 and directions['228']>0 and directions['229']>0,directions)
 coll=dnm.mesh((rt/'aircraft'/(kind+'coll.srf')).read_text().splitlines());check(kind+' nonempty collider',len(coll.f)>50,len(coll.f))
# No source image or sound is imported; editable source only.
src=lab/'model-source/upstream';check('geometry-only upstream files',not any(p.suffix.lower() in ['png','.png','.rgb','.wav','.ogg','.nas','.jpg'] for p in src.rglob('*') if p.is_file()))
(lab/'validation.json').write_text(json.dumps({'passed':True,'checks':checks,'limitations':['No native Windows 10 x86 runtime test','Visual review is not exhaustive mathematical intersection proof','Native flight dynamics retained as game approximation']},indent=2));print('PASS',len(checks))
