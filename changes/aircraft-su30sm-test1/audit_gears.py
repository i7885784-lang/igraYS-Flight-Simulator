from pathlib import Path
import sys,json,numpy as np,collections,os
from model import Model
r=Path(__file__).resolve().parent;m=Model();names=list(m.objects);doors=[n for n in names if n.startswith('GearDoor_')];moving=[n for n in names if n.startswith(('GearUpper_','GearPiston_','GearAxle_','Wheel_','WheelHub_'))];fixed=[n for n in names if n not in doors+moving];meta=json.loads((r/'gear.json').read_text());Ps={c['name']:np.array(c['P']) for c in meta['gear']};hits=[];allowed=[];steps=int(os.environ.get('POSES','41'));limitprint=18
assert len(names)>=119 and len(doors)==4 and len(moving)==15, 'Incomplete collision scene'
print('Loaded',len(names),'meshes; poses',steps,flush=True)
for g in np.linspace(0,1,steps):
 m.sample(float(g))
 for a in moving+doors:
  for b in fixed+doors:
   if a==b:continue
   if a in doors and b in doors and a>b:continue
   q=m.collide(a,b)
   if q is None:continue
   intentional=False;reason=''
   title=next((s for s in ['Nose','Left','Right'] if '_'+s in a),None)
   if title and np.linalg.norm(q-Ps[title])<.16 and a.startswith('GearUpper_') and b.startswith(('GearBearing_', 'GearWell_')):intentional=True;reason='trunnion attachment'
   if g==0 and a in doors and (b in doors or b.startswith(('Fuselage_', 'GearWell_'))):intentional=True;reason='closed skin mating (inspect contact locations separately)'
   if g<=.02 and a.startswith('GearDoor_Nose_') and b.startswith('GearDoor_Nose_') and abs(q[0])<.015:intentional=True;reason='adjacent nose leaves share their seam before rotation'
   h={'g':round(float(g),6),'a':a,'b':b,'point':q.round(6).tolist()}
   (allowed if intentional else hits).append({**h,**({'reason':reason} if intentional else {})})
   if not intentional and len(hits)<=limitprint:print(h,flush=True)
 # Rubber must remain clear of its own suspension through swivel and folding.
 for a in [n for n in moving if n.startswith('Wheel_')]:
  title=a.split('_',1)[1]
  for b in [n for n in moving if n.startswith(('GearUpper_','GearPiston_','GearAxle_')) and n.endswith('_'+title)]:
   q=m.collide(a,b)
   if q is not None:
    h={'g':round(float(g),6),'a':a,'b':b,'point':q.round(6).tolist()};hits.append(h)
    if len(hits)<=limitprint:print(h,flush=True)
print('HITS',len(hits),collections.Counter((q['a'],q['b']) for q in hits),flush=True);(r/('gear-audit-'+str(steps)+'.json')).write_text(json.dumps({'passed':not hits,'poses':steps,'hits':hits,'mating_contacts':allowed},indent=2))
