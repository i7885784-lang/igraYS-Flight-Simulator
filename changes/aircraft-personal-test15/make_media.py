from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import shutil,json,subprocess,numpy as np
r=Path(__file__).resolve().parent;report=Path('/workspace/igraYS-Flight-Simulator/reports/personal-playtest-15');photos=report/'Photos';originals=report/'Originals';video=report/'Video'
for p in [photos,originals,video]:p.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
def pair(name,before,after,box):
 ps=[r/'checks'/before,r/'checks'/after];images=[Image.open(p).convert('RGB').crop(box) for p in ps];w,h=images[0].size;scale=min(2.5,640/w);W,H=round(w*scale),round(h*scale);out=Image.new('RGB',(W*2,H+34),(238,241,244));draw=ImageDraw.Draw(out)
 for i,im in enumerate(images):out.paste(im.resize((W,H)),(i*W,34));draw.text((i*W+8,7),'ДО' if i==0 else 'ПОСЛЕ',font=font,fill=(24,35,45));shutil.copy2(ps[i],originals/(name+('-before.png' if i==0 else '-after.png')))
 out.save(photos/(name+'.jpg'),quality=92)
pair('Su27-small-seam','su27-target-before/target-130-1.png','su27-target-verified/target-130-1.png',(320,450,550,535))
pair('Su27-other-side','su27-target-before/target-270-1.png','su27-target-verified/target-270-1.png',(760,390,950,505))
pair('Su34-cover-joint','su34-target-before/target-90-1.png','su34-target-final/target-90-1.png',(560,465,1190,640))
pair('Su34-other-side','su34-target-before/target-270-1.png','su34-target-final/target-270-1.png',(85,465,720,640))
pair('Su47-internal-boxes','su47-close-before/close-1-75.png','su47-close-final/close-1-75.png',(400,330,1220,710))
pair('Su47-other-side','su47-close-before/close-1-255.png','su47-close-final/close-1-255.png',(70,330,890,710))
pair('MiG29-closed-wheel','mig29-wheel-before/wheel-90.png','mig29-wheel-final/wheel-90.png',(430,390,820,580))
pair('MiG29-other-side','mig29-wheel-before/wheel-270.png','mig29-wheel-final/wheel-270.png',(450,390,850,580))
pair('MiG29-board','mig29-close-before/close-1-105.png','mig29-close-final/close-1-105.png',(370,410,960,725))
for kind in ['su27','su34','mig29','su47']:
 pair(kind+'-normal',kind+'-normal-before/overview.png',kind+'-normal-final/overview.png',(150,220,1160,820))
# Real videos: decode every input, export selected real-time segments only.
parts=r/'media-parts';parts.mkdir(exist_ok=True)
def clip(src,start,end,name,label):
 out=parts/(name+'.mp4');subprocess.run(['ffmpeg','-y','-loglevel','error','-ss',str(start),'-to',str(end),'-i',str(src),'-an','-vf',"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='"+label+"':x=12:y=h-34:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.65",'-c:v','libx264','-crf','24','-pix_fmt','yuv420p',str(out)],check=True);return out
gears=[]
for kind,label in [('su27','Su-27'),('su34','Su-34'),('mig29','MiG-29')]:
 d=kind+'-native-'+('final-gear' if kind=='mig29' else 'gear');src=r/'checks'/d/'gear.mp4';gears.append(clip(src,0,16,'gear-'+kind,label+' - landing gear'))
controls=[]
for kind,label in [('su27','Su-27'),('su34','Su-34'),('mig29','MiG-29'),('su47','Su-47'),('su57','Su-57')]:
 src=r/'checks'/(kind+'-native-controls')/'controls.mp4'
 for a,b,part in [(0,3.5,'pitch'),(3.6,7,'roll'),(7.1,10.8,'rudder'),(10.9,16.4,'flaps')]:controls.append(clip(src,a,b,kind+'-'+part,label+' - '+part))
for kind,label in [('su27','Su-27'),('mig29','MiG-29')]:
 for case in ['canopy','brake']:
  src=r/'checks'/(kind+'-native-final-'+case)/(case+'.mp4');controls.append(clip(src,0,8,kind+'-'+case,label+' - '+case))
def join(paths,name):
 f=parts/(name+'.txt');f.write_text(''.join("file '"+str(p)+"'\n" for p in paths));subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(f),'-c','copy',str(video/(name+'.mp4'))],check=True);subprocess.run(['ffmpeg','-v','error','-i',str(video/(name+'.mp4')),'-f','null','-'],check=True)
join(gears,'Landing_Gear');join(controls,'Controls')
# Source measurements and native logs, without any experimental model assets.
checks={}
for name in ['control-checks.json','preservation-checks.json','motion-audit.json','mig-motion-audit.json','return-lip-collision-checks.json','seam-regression-checks.json','mig29-final-closed-wheel-check.json']:
 checks[name]=json.loads((r/'clean-rebuild'/name).read_text())
checks['native']={}
for p in sorted((r/'checks').glob('*native*/results.json')):
 j=json.loads(p.read_text());assert j['passed'];checks['native'][p.parent.name]={'passed':True,'states':j['states']}
(report/'CHECKS.json').write_text(json.dumps(checks,indent=2))
