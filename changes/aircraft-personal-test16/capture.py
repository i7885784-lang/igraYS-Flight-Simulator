from pathlib import Path
import os,sys,subprocess,time,re,ctypes,json,shutil
from PIL import ImageGrab
import fcntl
_capture_lock=open("/tmp/ysflight-native-capture.lock","w")
fcntl.flock(_capture_lock,fcntl.LOCK_EX)
lab=Path(__file__).resolve().parent;rt=Path(os.environ.get('GAME_RUNTIME',str(lab/'runtime')));case=sys.argv[1];out=lab/'checks'/os.environ.get('CHECK_NAME',case);out.mkdir(parents=True,exist_ok=True)
(out/'results.json').unlink(missing_ok=True)
profile=lab/('user-'+case);shutil.copytree(rt/'config',profile/'config',dirs_exist_ok=True)
(profile/'config/option.cfg').write_text('OPENDEMO FALSE\nFONTHEIGHT 18\nLANGUAGE "FILE:ru.uitxt"\n')
ident=os.environ.get('AIRCRAFT_CHECK','SU-27_FLANKER');ground=case in ['canopy','ground'];height=({'SU-27_FLANKER':2.48,'MIG-29_FULCRUM':1.74,'SU-57_FELON':2.18,'SU-34_FULLBACK':2.53}.get(ident,3.12)) if ground else (10000 if case=='controls' else 1000)
fixture=f'''YFSVERSI 20180930
FIELDNAM {'AOMORI' if ground else 'STRAIGHT_TEST'} 0 0 0 0 0 0 FALSE LOADAIR:FALSE
INITPLYR AIR 1
CANCONTI TRUE
ENVIRONM DAY
EXTENSIO AIRSHOW_V8 CONFIG 0 0 0 16 0.2 0.35
AIRPLANE SU-27_FLANKER TRUE
IDENTIFY 0
IDANDTAG 1 "SU47_CHECK"
AIRPCMND UNLOADWP
AIRPCMND INITFUEL 50%
AIRPCMND ATTITUDE 0deg 0deg 0deg
AIRPCMND POSITION {'48641.81m' if ground else '0m'} {height}m {'-11082.90m' if ground else '0m'}
AIRPCMND INITSPED {0 if ground else 180}m/s
AIRPCMND CTLLDGEA {'TRUE' if ground else 'FALSE'}
AIRPCMND CTLTHROT {0 if ground else .55}
AIRPCMND CTLABRNR FALSE
'''
fixture=fixture.replace('SU-27_FLANKER',os.environ.get('AIRCRAFT_CHECK','SU-27_FLANKER'))
if ident in ['SU-27_FLANKER','SU-57_FELON','SU-34_FULLBACK']:fixture=fixture.replace('AIRPCMND UNLOADWP','AIRPCMND UNLOADWP\nAIRPCMND LOADWEPN AIM9X '+('4' if ident=='SU-57_FELON' else '2'))
if case=='engine':fixture=fixture.replace('CTLTHROT 0.55','CTLTHROT 0.0')
if os.environ.get('GEAR_DOWN')=='1':fixture=fixture.replace('CTLLDGEA FALSE','CTLLDGEA TRUE')
(out/'start.yfs').write_text(fixture)
script='WAITFOR:GUI\nSLEEP:500\n'+'GUI:CLOSEMODAL\n'*4+'SLEEP:8000\nFILE:OPEN Z:'+str(out/'start.yfs')+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\nFLIGHTCMD:TESTADVANCE .1\nBTNFUNC:COCKPITVIEW\n'
if case in ['inspect','smoke','ground','cabin']:
 views=[('front',180,0,110),('top',180,89,175),('side',90,0,130),('bottom',180,-89,175)]+[(f'quarter-{h}',h,23,120) for h in [45,135,225,315]]
 if ident=='SU-27_FLANKER':views += [('tip-rail',160,15,28)]
 if ident=='MIG-29_FULCRUM':views += [('intake',160,-10,45)]
 if ident=='SU-34_FULLBACK':views=[(n,h,p,d*1.20) for n,h,p,d in views]
 if ident=='SU-34_FULLBACK':views += [('cabin-front',160,15,55),('cabin-side',95,15,55)]
 if ident=='SU-57_FELON':views += [('cockpit-rear',40,40,35),('cockpit-front',140,30,35),('pylons',145,-20,75)]
 if case=='ground':views=[('ground-intake',160,-8,55),('ground-top',150,45,85)]
 if case=='cabin':views=[('cabin-front',160,15,55),('cabin-side',95,15,55)]
 if case=='smoke':views=[('flight',140,25,110)]
 if os.environ.get('CHECK_VIEWS'):views=[v for v in views if v[0] in os.environ['CHECK_VIEWS'].split(',')]
 views=json.loads(os.environ['CAPS'])
 script+='BTNFUNC:PAUSESIMULATION\nREM DIAG_READY\nSLEEP:3000\n'+'BTNFUNC:VIEWZOOM\n'*26
 for name,h,p,d,aim,pose in views:
  script+=f'FLIGHTCMD:MODELPOSE {pose}\nBTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABAIM {aim}\nFLIGHTCMD:LABVIEW {h} {p} {d} 0\nREM SHOT_{name}\nSLEEP:1400\n'
 script+='FLIGHTCMD:AIRCOMMAND $PLAYER ATTITUDE 0deg 0deg 180deg\nBTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABVIEW 180 89 175 0\nREM SHOT_inverted\nSLEEP:1400\nFLIGHTCMD:MODELCHECK\nSLEEP:60000\n'
else:
 view={'gear':'140 -30 65','canopy':'120 18 65','controls':'115 8 72','engine':'38 -3 50','brake':'140 27 45','orbit':'0 18 145'}[case]
 if ident=='SU-34_FULLBACK' and case=='brake':view='0 12 90'
 if case=='engine':script+='FLIGHTCMD:LABAIM 0 -.3 '+str({'SU-27_FLANKER':-8.7,'MIG-29_FULCRUM':-6.1,'SU-34_FULLBACK':-8.5,'SU-47_BERKUT':-9.5,'SU-57_FELON':-8.0}[ident])+'\n'
 if case=='brake' and ident=='SU-27_FLANKER':script+='FLIGHTCMD:LABAIM 0 1.1 -.5\n'
 script+=f'FLIGHTCMD:LABVIEW {view} 0\n'+'BTNFUNC:VIEWZOOM\n'*26+'REM CAPTURE_READY\n'
 if case=='orbit':
  script+='BTNFUNC:PAUSESIMULATION\n'
  for h in range(0,361,10):script+=f'BTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABAIM 0 0 0\nFLIGHTCMD:LABVIEW {h} -15 145 0\nFLIGHTCMD:MODELCHECK\nSLEEP:220\n'
 else:
  for k in range(80 if case in ['gear','engine'] else 160):script+='FLIGHTCMD:MODELCHECK\nSLEEP:200\n'
  if case=='gear':
   script+='BTNFUNC:PAUSESIMULATION\n'
   details=[('intake-left',150,-10,42,'1.7 0 -2'),('intake-right',210,-10,42,'-1.7 0 -2'),('nose-side',100,-12,32,'0 0 3.5'),('nose-bottom',180,-60,28,'0 0 3.5'),('rear',0,-10,48,'0 -.2 -7.5')]
   for name,h,p,d,aim in details:script+=f'BTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABAIM {aim}\nFLIGHTCMD:LABVIEW {h} {p} {d} 0\nREM FINAL_{name}\nSLEEP:1800\n'
 if case=='engine':
  script+='BTNFUNC:PAUSESIMULATION\nBTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABAIM 0 -.3 '+str({'SU-27_FLANKER':-8.7,'MIG-29_FULCRUM':-6.1,'SU-34_FULLBACK':-8.5,'SU-47_BERKUT':-9.5,'SU-57_FELON':-8.0}[ident])+'\nFLIGHTCMD:LABVIEW 0 -3 34 0\nREM FINAL_engine-idle\nSLEEP:5000\n'
 script+='SLEEP:60000\n'
(out/'run.script').write_text(script);log=out/'game.log'
def wait(needle,timeout=90):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  t=log.read_text(errors='replace')
  if needle in t:return t
  if game.poll() is not None:raise RuntimeError('Game exited '+str(game.returncode)+'\n'+t[-1500:])
  time.sleep(.1)
 raise RuntimeError('Timeout '+needle+'\n'+log.read_text(errors='replace')[-1000:])
x=ctypes.CDLL('libX11.so.6');xt=ctypes.CDLL('libXtst.so.6');x.XOpenDisplay.restype=ctypes.c_void_p;display=x.XOpenDisplay(b':99')
x.XStringToKeysym.argtypes=[ctypes.c_char_p];x.XStringToKeysym.restype=ctypes.c_ulong;x.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong];x.XKeysymToKeycode.restype=ctypes.c_uint
xt.XTestFakeKeyEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong];x.XFlush.argtypes=[ctypes.c_void_p]
def key(name,down):xt.XTestFakeKeyEvent(display,x.XKeysymToKeycode(display,x.XStringToKeysym(name.encode())),int(down),0);x.XFlush(display)
def combo(name):
 for k in name.split('+'):
  key(k,True)
  if '+' in name:time.sleep(.07)
 time.sleep(.25 if '+' in name else .12)
 for k in reversed(name.split('+')):
  key(k,False)
  if '+' in name:time.sleep(.05)
with log.open('w') as f:game=subprocess.Popen([os.environ['WINELOADER'],str(rt/os.environ.get('GAME_EXE','ysflight64_gl1.exe')),'-userdir','Z:'+str(profile),'-configdir','Z:'+str(profile/'config'),'-script','Z:'+str(out/'run.script')],cwd=rt,stdout=f,stderr=f)
try:
 wait('Script>>SLEEP:8000')
 tree=subprocess.check_output(['xwininfo','-root','-tree'],text=True);window=next(int(w,16) for w,t in re.findall(r'(0x[0-9a-f]+) "([^"]+)"',tree) if 'YS' in t.upper() and 'FLIGHT' in t.upper())
 x.XMoveResizeWindow.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_int,ctypes.c_uint,ctypes.c_uint];x.XMoveResizeWindow(display,window,0,0,1280,960)
 x.XSetInputFocus.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];x.XSetInputFocus(display,window,1,0);x.XFlush(display)
 subprocess.run([os.environ['WINELOADER'],str(lab/'resize_window.exe')],check=True,stdout=subprocess.DEVNULL)
 if case in ['inspect','smoke','ground','cabin']:
  if os.environ.get('DIAGNOSTIC')=='1':
   wait('Script>>REM DIAG_READY');combo('Control_L+Shift_L+F9')
  for name,*_ in views:
   wait('Script>>REM SHOT_'+name);time.sleep(.3);ImageGrab.grab(xdisplay=':99').save(out/(name+'.png'));print(name,flush=True)
  wait('Script>>REM SHOT_inverted');time.sleep(.3);ImageGrab.grab(xdisplay=':99').save(out/'inverted.png')
  t=wait('MODELCHECK t=');assert 'active=1' in t
  (out/'results.json').write_text(json.dumps({'passed':True,'aircraft':os.environ.get('AIRCRAFT_CHECK','SU-27_FLANKER'),'active':True,'frames':[v[0] for v in views]},indent=2))
 else:
  wait('Script>>REM CAPTURE_READY')
  events={'orbit':[],'brake':[(.8,'b','tap'),(8.3,'b','tap')],'gear':[(.2,'g','tap'),(7.3,'g','tap')],'canopy':[(.8,'Alt_L+5','tap'),(8.3,'Alt_L+5','tap')],
   'controls':[(.2,'Down','down'),(1.5,'Down','up'),(2.0,'Up','down'),(3.3,'Up','up'),(3.8,'Left','down'),(5.1,'Left','up'),(5.6,'Right','down'),(6.9,'Right','up'),(7.4,'z','down'),(8.7,'z','up'),(8.8,'x','tap'),(9.2,'c','down'),(10.5,'c','up'),(10.6,'x','tap'),(11,'f','tap'),(11.15,'f','tap'),(11.3,'f','tap'),(11.45,'f','tap'),(17,'r','tap'),(17.15,'r','tap'),(17.3,'r','tap'),(17.45,'r','tap'),(23,'b','tap'),(24,'b','tap')],
   'engine':[(.2+i*.14,'q','tap') for i in range(20)]+[(3.3,'Tab','tap'),(7,'Tab','tap'),(7.6,'Tab','tap'),(10.5,'Tab','tap')]+[(10+i*.14,'a','tap') for i in range(20)]}[case]
  duration=26 if case=='controls' else 14 if case=='orbit' else 16;enc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1280x960','-framerate','12','-i','-','-an','-c:v','libx264','-pix_fmt','yuv420p',str(out/(case+'.mp4'))],stdin=subprocess.PIPE)
  began=time.monotonic();ei=0;shots=set()
  for k in range(duration*12):
   t=time.monotonic()-began
   while ei<len(events) and t>=events[ei][0]:
    _,name,action=events[ei]
    if action=='tap':combo(name)
    else:key(name,action=='down')
    ei+=1
   im=ImageGrab.grab(xdisplay=':99').convert('RGB');enc.stdin.write(im.tobytes())
   if case=='engine':
    lines=[v for v in log.read_text(errors='replace').splitlines() if v.startswith('MODELCHECK ')]
    if lines:
     now=dict(re.findall(r'(\w+)=(-?[0-9.]+)',lines[-1]));opening=float(now['nozzle'])
     for label,condition in [('narrow',now['ab']=='1' and .18<opening<.32),('wide',now['ab']=='1' and opening>.835)]:
      if condition and label not in shots:
       im.save(out/('plume-'+label+'.png'));(out/('plume-'+label+'.json')).write_text(json.dumps(now,indent=2));shots.add(label)

   for at in [0,1,2,4,7,8,9,11,14,15,23.7]:
    if t>=at and at not in shots:im.save(out/f'{case}-{int(at*10):03}.png');shots.add(at)
   time.sleep(max(0,began+(k+1)/12-time.monotonic()))
  enc.stdin.close();assert enc.wait(timeout=20)==0
  states=[dict(re.findall(r'(\w+)=(-?[0-9.]+)',s)) for s in log.read_text(errors='replace').splitlines() if s.startswith('MODELCHECK ')]
  assert len(states)>=12 and all(s['active']=='1' for s in states)
  if case=='engine':
   assert all((out/('plume-'+n+'.png')).exists() for n in ['narrow','wide']), 'Missing transition screenshots'
   ab=[s for s in states if s['ab']=='1']
   if 'jetLX' in ab[0]:
    assert max(float(v['jetLX']) for v in ab)-min(float(v['jetLX']) for v in ab)>.08
    assert max(float(v['jetRX']) for v in ab)-min(float(v['jetRX']) for v in ab)>.08
  if case=='gear':
   values=[float(s['gear']) for s in states];peak=values.index(max(values))
   assert values[0]<.01 and max(values)>.99 and values[-1]<.01
   assert any(.01<v<.99 for v in values[:peak]) and any(.01<v<.99 for v in values[peak+1:])
  if case=='canopy':
   if ident=='SU-34_FULLBACK':assert max(abs(float(s['canopy'])) for s in states)<.001
   else:assert max(float(s['canopy']) for s in states)>.99 and float(states[-1]['canopy'])<.01
  if case=='gear':
   for name,*_ in details:
    wait('Script>>REM FINAL_'+name);time.sleep(.25);ImageGrab.grab(xdisplay=':99').save(out/(name+'.png'));print('final',name,flush=True)
  if case=='engine':
   wait('Script>>REM FINAL_engine-idle');time.sleep(.4);ImageGrab.grab(xdisplay=':99').save(out/'engine-idle-rear.png')
  (out/'results.json').write_text(json.dumps({'passed':True,'native_XTest_keyboard_events':events,'states':states},indent=2))
finally:
 game.terminate()
 try:game.wait(timeout=10)
 except subprocess.TimeoutExpired:game.kill();game.wait()
