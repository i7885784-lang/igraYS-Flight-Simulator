"""Diagnostic RGB screenshots make a real background hole measurable."""
from pathlib import Path
import sys,json,numpy as np
from PIL import Image
r=Path(sys.argv[1]);results={}
for view,roi in [('right-side',(660,443,713,474)),('left-side',(565,438,620,477))]:
 images=[np.array(Image.open(r/f'checks/{folder}/{view}.png').convert('RGB').crop(roi)).astype(int) for folder in ['su27-down-before','su27-down-final']]
 counts=[int(((a.max(2)-a.min(2)<10)&(a.min(2)>130)&(a.max(2)<180)).sum()) for a in images]
 assert counts[0]>50 and counts[1]==0,(view,counts)
 results[view]={'roi':roi,'gray_background_before_pixels':counts[0],'gray_background_after_pixels':counts[1]}
(r/'gap-pixel-checks.json').write_text(json.dumps(results,indent=2));print(results)
