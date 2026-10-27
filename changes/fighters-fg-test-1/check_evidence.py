from pathlib import Path
import json,subprocess,numpy as np
from PIL import Image
lab=Path(__file__).resolve().parent;root=lab/'checks';result={}
for kind in ['su27','mig29']:
 obj={}
 for case in ['gear','canopy','controls','brake','engine']:
  stage='release';p=root/f'{kind}-{case}-{stage}';j=json.loads((p/'results.json').read_text());s=j['states'];assert j['passed'] and all(x['active']=='1' for x in s)
  bounds={key:[min(float(x[key]) for x in s),max(float(x[key]) for x in s),float(s[-1][key])] for key in ['gear','canopy','flap','elevator','aileron','rudder','spoiler','throttle','ab']}
  if case in ['gear','canopy','brake']:
   key={'gear':'gear','canopy':'canopy','brake':'spoiler'}[case];lo,hi,last=bounds[key];assert lo<.01 and hi>.99 and last<.01
   q=[float(x[key]) for x in s];assert any(.05<v<.95 for v in q);assert any(q[i+1]>q[i]+.001 for i in range(len(q)-1)) and any(q[i+1]<q[i]-.001 for i in range(len(q)-1))
  if case=='controls':
   assert all(bounds[k][0]<-.99 and bounds[k][1]>.99 for k in ['elevator','aileron','rudder']);assert bounds['flap'][0]<.01 and bounds['flap'][1]>.99 and bounds['flap'][2]<.01
  if case=='engine':
   assert bounds['throttle'][0]<.01 and bounds['throttle'][1]>.99 and bounds['throttle'][2]<.01 and bounds['ab'][1]==1 and bounds['ab'][2]==0
   counts=[]
   for fn in ['engine-070.png','engine-140.png']:
    a=np.array(Image.open(p/fn).convert('RGB'));counts.append(int(((a[:,:,0]>210)&(a[:,:,1]>80)&(a[:,:,1]<190)&(a[:,:,2]<120)).sum()))
   assert counts[0]>500 and counts[1]<50;obj['afterburner_pixels_on_off']=counts
  video=p/(case+'.mp4');subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],check=True,stdout=subprocess.DEVNULL)
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=width,height,nb_frames','-of','json',str(video)],text=True));assert probe['streams'][0]['width']==1280
  obj[case]={'passed':True,'bounds_min_max_last':bounds,'video':probe}
 inspect=json.loads((root/f'{kind}-inspect-release/results.json').read_text());assert inspect['passed'] and len(inspect['frames'])==21
 obj['inspection_frames']=inspect['frames'];result[kind]=obj
for ident in ['SU-47_BERKUT','SU-57_FELON']:assert json.loads((root/('preserved-'+ident)/'results.json').read_text())['passed']
(lab/'evidence-checks.json').write_text(json.dumps({'passed':True,'aircraft':result,'preserved_flight_loads':['SU-47_BERKUT','SU-57_FELON'],'runtime':'Win64 diagnostic executable under Wine/Xvfb; live XTest keys for mechanisms'},indent=2));print('Native keys, cycles, AB pixels and all videos passed')
