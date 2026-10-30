"""Pixel regression: formerly black shadow pixels must contain visible exhaust now."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
r=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parent);results={}
for k in ['su27','mig29','su34','su47','su57']:
 planes={}
 for view in ['rear-high','top','side-high']:
  before=np.array(Image.open(r/f'checks/{k}-before/{view}.png').convert('RGB'));after=np.array(Image.open(r/f'checks/{k}-after/{view}.png').convert('RGB'));assert before.shape==after.shape
  black=before.max(2)<8
  restored=black & (after[:,:,2]>40) & (after[:,:,2]>after[:,:,1]*1.1) & (after[:,:,2]>after[:,:,0]*1.1)
  # Shadows elsewhere must remain black; removing them is not a valid fix.
  assert (black & (after.max(2)<8)).sum()>500
  body=(before[:,:,2]>before[:,:,0]*1.15)&(before[:,:,1]>before[:,:,0]*1.05)&(before[:,:,2]<200)&(before.max(2)>30)
  body_changed=int((body & (abs(after.astype(int)-before.astype(int)).max(2)>8)).sum())
  assert body_changed<max(10,int(body.sum()*.001)),(k,view,'opaque body changed')
  planes[view]={'opaque_blue_skin_changed_pixels':body_changed,'formerly_black_now_blue_pixels':int(restored.sum()),'unchanged_black_shadow_pixels':int((black & (after.max(2)<8)).sum())}
 assert sum(v['formerly_black_now_blue_pixels'] for v in planes.values())>500,(k,planes)
 assert sum(v['formerly_black_now_blue_pixels']>50 for v in planes.values())>=2,(k,planes)
 for mode in ['before','after']:
  state=json.loads((r/f'checks/{k}-{mode}/results.json').read_text());assert state['passed'] and all(s['active']=='1' and s['ab']=='1' for s in state['states'])
 results[k]=planes
if (r/'checks/su34-early-setting/results.json').exists():
 for view in ['rear-high','top','side-high']:
  a=np.array(Image.open(r/f'checks/su34-after/{view}.png').convert('RGB')).astype(int);b=np.array(Image.open(r/f'checks/su34-early-setting/{view}.png').convert('RGB')).astype(int)
  assert (abs(a-b).max(2)>8).mean()<.005,(view,'legacy early setting differs')
 results['legacy_early_transparency_setting']='matches corrected default'
(r/'overlap-regression.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
