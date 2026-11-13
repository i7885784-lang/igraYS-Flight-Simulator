"""Compare contacts only for the single modified fixed skin across 201 gear poses."""
from pathlib import Path
import sys,json,numpy as np,hashlib
root=Path(__file__).resolve().parent.parent/'su30sm-local-skin'
sys.path.insert(0,str(root/'validation'));from model import Model
out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True);sets={};report={}
for label,path in zip(['before','after'],map(Path,sys.argv[1:3])):
 m=Model(path);hits=[];cache={};target='MainBayFixedSkin_Left'
 for g in np.linspace(0,1,201):
  m.sample(g)
  for b in sorted(m.objects):
   if b==target:continue
   R,t=m.poses[target];S,v=m.poses[b];key=(b,R.tobytes(),t.tobytes(),S.tobytes(),v.tobytes())
   if key not in cache:cache[key]=m.collide(target,b) is not None
   if cache[key]:hits.append([round(float(g),4),b])
 sets[label]={tuple(x) for x in hits};report[label]={'model_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'samples':201,'target':target,'pairs_per_pose':len(m.objects)-1,'hits':hits};print(label,'hits',len(hits),flush=True)
report['added']=sorted(sets['after']-sets['before']);report['removed']=sorted(sets['before']-sets['after']);(out/'contacts.json').write_text(json.dumps(report,indent=2));assert not report['added'],report['added'];print('no added contacts',flush=True)
