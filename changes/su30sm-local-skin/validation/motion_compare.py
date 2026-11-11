from pathlib import Path
import json,numpy as np,sys,hashlib
from model import Model
from common import dnm
r=Path(__file__).resolve().parent
names=['MainBayFixedSkin_Left','MainBayFixedSkin_Right','MainWheelBayShutter_Left','MainWheelBayShutter_Right']
result={}
assert len(sys.argv)==4,'usage: motion_compare.py BASELINE.dnm CANDIDATE.dnm OUTPUT_DIR'
outdir=Path(sys.argv[3]);outdir.mkdir(parents=True,exist_ok=True)
for label,path in zip(['before','candidate'],map(Path,sys.argv[1:3])):
 m=Model(path);pairs=set()
 for a in names:
  for b in m.objects:
   if b!=a:pairs.add(tuple(sorted((a,b))))
 cache={};hits=[]
 for i,g in enumerate(np.linspace(0,1,201)):
  m.sample(g)
  for a,b in sorted(pairs):
   R,t=m.poses[a];S,v=m.poses[b];key=(a,b,R.tobytes(),t.tobytes(),S.tobytes(),v.tobytes())
   if key not in cache:
    contact=m.collide(a,b);cache[key]=None if contact is None else [float(v) for v in contact]
   if cache[key] is not None:hits.append({'g':round(float(g),4),'a':a,'b':b,'point':cache[key]})
  if i%25==0:print(label,i,'hits',len(hits),flush=True)
 out={'model_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'samples':201,'pairs':len(pairs),'distinct_pose_pairs':len(cache),'hits':hits};(outdir/(label+'-motion.json')).write_text(json.dumps(out,indent=2));result[label]=out
if len(result)==2:
 keys=lambda rows:set((q['g'],q['a'],q['b']) for q in rows)
 old=keys(result['before']['hits']);new=keys(result['candidate']['hits']);out={'added_pairs_poses':sorted(new-old),'removed_pairs_poses':sorted(old-new),'old_count':len(old),'new_count':len(new)};(outdir/'motion-diff.json').write_text(json.dumps(out,indent=2));print('ADDED',len(new-old),sorted(set((a,b) for g,a,b in new-old)),flush=True)
