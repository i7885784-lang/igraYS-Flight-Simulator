from pathlib import Path
import sys,json,numpy as np
from PIL import Image
r=Path(sys.argv[1]);result={}
for heading,roi in [(45,(676,501,692,508)),(300,(654,502,676,507))]:
 values=[]
 for folder in ['su34-rear-before','su34-bridge-final']:
  a=np.array(Image.open(r/f'checks/{folder}/rear-{heading}.png').convert('RGB').crop(roi)).astype(int)
  mask=(a[:,:,1]>75)&(a[:,:,2]>80)&(a[:,:,0]<120)&(a.max(2)-a.min(2)>25)
  values.append(int(mask.sum()))
 assert values[0]>50 and values[1]==0,(heading,values)
 result[str(heading)]={'roi':roi,'visible_bright_backside_before':values[0],'visible_bright_backside_after':values[1]}
(r/'gap-pixel-checks.json').write_text(json.dumps(result,indent=2));print(result)
