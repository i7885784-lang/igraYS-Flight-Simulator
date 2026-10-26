from pathlib import Path
import subprocess,time,importlib.machinery,sys,json
from PIL import ImageGrab
r=Path('/workspace/ysflight-work');lab=r/'su57-lab2';model=sys.argv[1];phase=sys.argv[2];mode=sys.argv[3] if len(sys.argv)>3 else 'views';out=lab/'captures'/model/phase/mode;out.mkdir(parents=True,exist_ok=True);p=lab/('runtime-before' if phase=='before' else 'runtime');t=importlib.machinery.SourceFileLoader('helpers2',str(r/'v8_5-tests.py')).load_module();env=t.env;profile=r/'su57-lab2-user';(profile/'config').mkdir(parents=True,exist_ok=True)
(profile/'config/option.cfg').write_text('OPENDEMO FALSE\nFONTHEIGHT 18\nLANGUAGE "FILE:ru.uitxt"\n');(profile/'config/flight.cfg').write_text('DRWSHADOW FALSE\n')
if not Path('/tmp/.X99-lock').exists():
 f=(lab/'xvfb.log').open('w');x=subprocess.Popen([str(r/'toolchain/usr/bin/Xvfb'),':99','-screen','0','1920x1080x24','-ac','-nolisten','tcp'],env=env,stdout=f,stderr=f,start_new_session=True);(lab/'xvfb.pid').write_text(str(x.pid));time.sleep(1)
ident={'su27':'SU-27_FLANKER','mig29':'MIG-29_FULCRUM','su57':'SU-57_FELON'}[model];ground=mode in ['ground','gear-rear-ground','cockpit'];height=(2.18 if model=='su57' else (1.9 if model=='su27' else 1.7)) if ground else 1000
fixture=f'''YFSVERSI 20180930
FIELDNAM STRAIGHT_TEST 0 0 0 0 0 0 FALSE LOADAIR:FALSE
INITPLYR AIR 1
CANCONTI TRUE
ENVIRONM DAY
EXTENSIO AIRSHOW_V8 CONFIG 0 0 0 16 0.2 0.35
AIRPLANE {ident} TRUE
IDENTIFY 0
IDANDTAG 1 "MODEL_INSPECTION"
AIRPCMND UNLOADWP
AIRPCMND LOADWEPN AIM9X 20
AIRPCMND INITFUEL 50%
AIRPCMND ATTITUDE 0deg 0deg 0deg
AIRPCMND POSITION 0m {height}m 0m
AIRPCMND INITSPED {0 if ground else 180}m/s
AIRPCMND CTLLDGEA {'TRUE' if ground or mode=='gear-detail' else 'FALSE'}
AIRPCMND CTLTHROT {0 if ground else .55}
AIRPCMND CTLABRNR FALSE
'''
if ground:fixture=fixture.replace('FIELDNAM STRAIGHT_TEST','FIELDNAM AOMORI').replace(f'POSITION 0m {height}m 0m',f'POSITION 48641.81m {height}m -11082.90m')
if mode=='exhaust-ab':fixture=fixture.replace('CTLTHROT 0.55','CTLTHROT 1').replace('CTLABRNR FALSE','CTLABRNR TRUE')
pose=out/'pose.yfs';pose.write_text(fixture)
views=[('front',180,0,105),('front-quarter',140,35,108),('right',90,0,125),('rear-quarter',40,25,108),('rear',0,0,105),('left',-90,0,125),('top',180,89,165),('bottom',180,-89,165)]
if mode=='launch':views=[('menu-launched',140,20,105)]
if mode=='hero':views=[('photo-match',180,25,110)]
if mode=='pylons':views=[('pylons-close',100,-15,45)]
if mode=='lighting':views=[('sun-top',140,65,115),('shaded-bottom',140,-65,115),('inverted-bottom',140,65,115)]
if mode=='gear-detail':views=[('rear-close',0,-7,55),('side-close',95,-12,80)]
if mode=='cockpit':views=[('ready-ground',0,0,100)]
if mode=='cockpit-detail':views=[('cockpit-close',125,22,45),('cockpit-side',90,8,48)]
if mode=='brake-detail':views=[('brake-side-close',90,10,42),('brake-quarter-close',130,20,45)]
if mode in ['exhaust','exhaust-ab']:views=[('nozzles-close',0,0,45),('nozzles-quarter',35,10,50)]
if mode=='nose':views=[('nose-close',125,8,48),('nose-side',90,0,55)]
if mode=='topbottom':views=[views[6],views[7]]
if mode=='quick':views=[views[1],views[2],views[5],views[7]]
if ground and mode!='cockpit':views=[('gear-ground',140,5,100),('gear-side',90,0,115)]
if mode=='gear-rear-ground':views=[('rear-low',0,-4,80),('rear-quarter-low',30,-5,90)]
poses=[]
if mode=='gear':
 views=[]
 for q in [0,.1,.25,.5,.75,1]:poses.append((f'gear-{q:g}',40,-14,90,[q,0,0,0,0,0]))
elif mode=='canopy':
 views=[]
 for q in [0,.25,.5,.75,1]:poses.append((f'canopy-{q:g}',100,7,100,[0,q,0,0,0,0]))
elif mode=='controls':
 views=[]
 for title,vals in [('neutral',[0,0,0,0,0,0]),('pitch-up',[0,0,0,.8,0,0]),('pitch-down',[0,0,0,-.8,0,0]),('roll-left',[0,0,0,0,-.8,0]),('roll-right',[0,0,0,0,.8,0]),('rudder-left',[0,0,0,0,0,-.8]),('rudder-right',[0,0,0,0,0,.8]),('flaps-down',[0,0,1,0,0,0])]:poses.append((title,25,8,100,vals))
frames=[(a,h,pitch,d,None) for a,h,pitch,d in views]+poses
script=t.prefix+'SLEEP:18000\nFILE:OPEN Z:'+str(pose)+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\nFLIGHTCMD:TESTADVANCE .1\nBTNFUNC:PAUSESIMULATION\nSLEEP:1000\n'
if mode=='launch':script=script.replace('FILE:OPEN Z:'+str(pose)+'\nGUI:CLICK mainDlg flyNow','GUI:CLICK mainDlg su57Preview')+'FLIGHTCMD:REPORT\n'
if mode=='exhaust-ab':script+='FLIGHTCMD:AIRCOMMAND $PLAYER CTLTHROT 1\nFLIGHTCMD:AIRCOMMAND $PLAYER CTLABRNR TRUE\n'
if mode=='brake-detail':script+='BTNFUNC:SPOILERBRAKE\nFLIGHTCMD:TESTADVANCE 2.2\n'
for i,(name,h,pitch,d,values) in enumerate(frames):
 if values is not None:script+='FLIGHTCMD:MODELPOSE '+' '.join(map(str,values))+'\n'
 if mode=='lighting' and name=='inverted-bottom':script+='FLIGHTCMD:AIRCOMMAND $PLAYER ATTITUDE 0deg 0deg 180deg\n'
 if mode=='gear-detail':script+='FLIGHTCMD:LABAIM 0 -.3 -2.2\n'
 if mode=='nose':script+='FLIGHTCMD:LABAIM 0 .65 7.9\n'
 if mode=='cockpit-detail':script+='FLIGHTCMD:LABAIM 0 1.25 5.8\n'
 if mode=='brake-detail':script+='FLIGHTCMD:LABAIM 0 1.9 .5\n'
 if mode in ['exhaust','exhaust-ab']:script+='FLIGHTCMD:LABAIM 0 0 -8.4\n'
 script+='BTNFUNC:COCKPITVIEW\n'
 if mode!='cockpit':script+=f'FLIGHTCMD:LABVIEW {h} {pitch} {d} 0\n'
 if i==0 and mode!='cockpit':script+='BTNFUNC:VIEWZOOM\n'*26
 script+=f'FLIGHTCMD:SU27CHECK\nFLIGHTCMD:MODELCHECK\nSLEEP:{2400+i}\n'
script+='SLEEP:10000\n';file=out/'views.script';file.write_text(script);log=out/'views.log'
with log.open('w') as f:game=subprocess.Popen([t.wine,str(p/'exterior-lab64.exe'),'-userdir','Z:'+str(profile),'-configdir','Z:'+str(profile/'config'),'-script','Z:'+str(file)],cwd=p,env=env,stdout=f,stderr=f)
try:
 for k in range(60):
  try:info=t.window('resize');break
  except Exception as e:
   if k==0:print('WINDOW',str(e),flush=True)
   time.sleep(.15)
 for i,(name,*_) in enumerate(frames):
  t.wait(log,f'Script>>SLEEP:{2400+i}',100);time.sleep(.35);ImageGrab.grab(xdisplay=':99',bbox=(info['x'],info['y'],info['x']+info['width'],info['y']+info['height'])).save(out/(name+'.png'));print('CAPTURED',model,phase,mode,name,flush=True)
finally:t.u.key('alt+F4');game.wait(timeout=20)
