from pathlib import Path
import json,subprocess,sys,numpy as np,collections
from model import Model
r=Path(__file__).parent;old=Model(r/'baseline/su30sm.dnm');names=['GearLink_Torque'+k+'_'+s for s in ['Left','Right'] for k in ['Upper','Lower']];pairs={tuple(sorted((a,b))) for a in names for b in old.objects if a!=b and not b.startswith(('Su30Dry','Su30Plume'))};baseline={};samples=np.linspace(0,1,201)
for g in samples:
 old.sample(float(g))
 for a,b in pairs:
  if old.collide(a,b) is not None:baseline[(round(float(g),3),a,b)]=True
out=[]
for angle in [11,12,13,14,15,16,17,18]:
 subprocess.run([sys.executable,str(r/'rotate_links.py'),str(angle)],check=True,stdout=subprocess.DEVNULL);m=Model(r/('links-'+str(float(angle))+'.dnm'));introduced=[];remain=[];jointgap=anchor=0
 for g in samples:
  m.sample(float(g));old.sample(float(g))
  for a,b in pairs:
   q=m.collide(a,b)
   if q is not None:
    key=(round(float(g),3),a,b)
    if key not in baseline:introduced.append({'g':key[0],'a':a,'b':b,'point':q.tolist()})
    if 'MainBayFixedSkin' in a or 'MainBayFixedSkin' in b:remain.append({'g':key[0],'a':a,'b':b})
  for side in ['Left','Right']:
   up='GearLink_TorqueUpper_'+side;low='GearLink_TorqueLower_'+side;R,t=m.poses[up];B,p=m.poses[low];L=m.boxes[up][1][1];jointgap=max(jointgap,float(np.linalg.norm(t+R@np.array([0,L,0])-p)));Lo=m.boxes[low][1][1];Ro,to=old.poses[up];Bo,po=old.poses[low];anchor=max(anchor,float(np.linalg.norm(t-to)),float(np.linalg.norm(p+B@np.array([0,Lo,0])-(po+Bo@np.array([0,Lo,0])))))
 result={'angle_deg':angle,'introduced':introduced,'remaining_mainfixed':remain,'joint_gap_max_m':jointgap,'anchor_drift_max_m':anchor};out.append(result);(r/'rotate-fine-scan.json').write_text(json.dumps(out,indent=2));print(angle,'new',len(introduced),'main',len(remain),'joint',jointgap,'anchor',anchor,collections.Counter((h['a'],h['b']) for h in introduced),flush=True)
