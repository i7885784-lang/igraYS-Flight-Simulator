from pathlib import Path
import os,sys,subprocess,time,re,ctypes,json,shutil
from PIL import ImageGrab
lab=Path(__file__).resolve().parent;rt=Path(os.environ.get('GAME_RUNTIME',str(lab/'runtime')));case=sys.argv[1];out=lab/'checks'/os.environ.get('CHECK_NAME',case);out.mkdir(parents=True,exist_ok=True)
(out/'results.json').unlink(missing_ok=True)
profile=lab/('user-'+case);shutil.copytree(rt/'config',profile/'config',dirs_exist_ok=True)
(profile/'config/option.cfg').write_text('OPENDEMO FALSE\nFONTHEIGHT 18\nLANGUAGE "FILE:ru.uitxt"\n')
ground=case=='canopy';height=(2.48 if '27' in os.environ.get('AIRCRAFT_CHECK','') else 1.74) if ground else 1000
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
if case=='engine':fixture=fixture.replace('CTLTHROT 0.55','CTLTHROT 0.0')
(out/'start.yfs').write_text(fixture)
script='WAITFOR:GUI\nSLEEP:500\n'+'GUI:CLOSEMODAL\n'*4+'SLEEP:8000\nFILE:OPEN Z:'+str(out/'start.yfs')+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\nFLIGHTCMD:TESTADVANCE .1\nBTNFUNC:COCKPITVIEW\n'
if case in ['inspect','smoke']:
 views=[('front',180,0,110),('top',180,89,175),('side',90,0,130),('bottom',180,-89,175),('cockpit',130,20,48)]+[(f'orbit-{h}',h,25,120) for h in range(0,360,45)]+[(f'lower-{h}',h,-25,120) for h in range(0,360,45)]
 if case=='smoke':views=[('flight',140,25,110)]
 script+='BTNFUNC:PAUSESIMULATION\n'+'BTNFUNC:VIEWZOOM\n'*26
 for name,h,p,d in views:
  script+=f'BTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABAIM '+('0 .6 4.5' if name=='cockpit' else '0 0 0')+f'\nFLIGHTCMD:LABVIEW {h} {p} {d} 0\nREM SHOT_{name}\nSLEEP:1400\n'
 script+='FLIGHTCMD:AIRCOMMAND $PLAYER ATTITUDE 0deg 0deg 180deg\nBTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABVIEW 180 89 175 0\nREM SHOT_inverted\nSLEEP:1400\nFLIGHTCMD:MODELCHECK\nSLEEP:60000\n'
else:
 view={'gear':'40 -14 110','canopy':'120 18 65','controls':'140 30 115','engine':'0 8 85','brake':'140 27 100'}[case]
 script+=f'FLIGHTCMD:LABVIEW {view} 0\n'+'BTNFUNC:VIEWZOOM\n'*26+'REM CAPTURE_READY\n'
 for k in range(160):script+='FLIGHTCMD:MODELCHECK\nSLEEP:200\n'
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
with log.open('w') as f:game=subprocess.Popen([os.environ['WINELOADER'],str(rt/'ysflight64_gl1.exe'),'-userdir','Z:'+str(profile),'-configdir','Z:'+str(profile/'config'),'-script','Z:'+str(out/'run.script')],cwd=rt,stdout=f,stderr=f)
try:
 wait('Script>>SLEEP:8000')
 tree=subprocess.check_output(['xwininfo','-root','-tree'],text=True);window=next(int(w,16) for w,t in re.findall(r'(0x[0-9a-f]+) "([^"]+)"',tree) if 'YS' in t.upper() and 'FLIGHT' in t.upper())
 x.XMoveResizeWindow.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_int,ctypes.c_uint,ctypes.c_uint];x.XMoveResizeWindow(display,window,0,0,1280,960)
 x.XSetInputFocus.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];x.XSetInputFocus(display,window,1,0);x.XFlush(display)
 if case in ['inspect','smoke']:
  for name,*_ in views:
   wait('Script>>REM SHOT_'+name);time.sleep(.3);ImageGrab.grab(xdisplay=':99').save(out/(name+'.png'));print(name,flush=True)
  wait('Script>>REM SHOT_inverted');time.sleep(.3);ImageGrab.grab(xdisplay=':99').save(out/'inverted.png')
  t=wait('MODELCHECK t=');assert 'active=1' in t
  (out/'results.json').write_text(json.dumps({'passed':True,'aircraft':os.environ.get('AIRCRAFT_CHECK','SU-27_FLANKER'),'active':True,'frames':[v[0] for v in views]},indent=2))
 else:
  wait('Script>>REM CAPTURE_READY')
  events={'brake':[(.8,'b','tap'),(8.3,'b','tap')],'gear':[(.2,'g','tap'),(7.3,'g','tap')],'canopy':[(.8,'Alt_L+5','tap'),(8.3,'Alt_L+5','tap')],
   'controls':[(.2,'Down','down'),(1.5,'Down','up'),(2.0,'Up','down'),(3.3,'Up','up'),(3.8,'Left','down'),(5.1,'Left','up'),(5.6,'Right','down'),(6.9,'Right','up'),(7.4,'z','down'),(8.7,'z','up'),(8.8,'x','tap'),(9.2,'c','down'),(10.5,'c','up'),(10.6,'x','tap'),(11,'f','tap'),(11.15,'f','tap'),(11.3,'f','tap'),(11.45,'f','tap'),(17,'r','tap'),(17.15,'r','tap'),(17.3,'r','tap'),(17.45,'r','tap'),(23,'b','tap'),(24,'b','tap')],
   'engine':[(.2+i*.14,'q','tap') for i in range(20)]+[(3.3,'Tab','tap'),(9,'Tab','tap')]+[(10+i*.14,'a','tap') for i in range(20)]}[case]
  duration=26 if case=='controls' else 16;enc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1280x960','-framerate','12','-i','-','-an','-c:v','libx264','-pix_fmt','yuv420p',str(out/(case+'.mp4'))],stdin=subprocess.PIPE)
  began=time.monotonic();ei=0;shots=set()
  for k in range(duration*12):
   t=time.monotonic()-began
   while ei<len(events) and t>=events[ei][0]:
    _,name,action=events[ei]
    if action=='tap':combo(name)
    else:key(name,action=='down')
    ei+=1
   im=ImageGrab.grab(xdisplay=':99').convert('RGB');enc.stdin.write(im.tobytes())
   for at in [0,1,2,4,7,8,9,11,14,15,23.7]:
    if t>=at and at not in shots:im.save(out/f'{case}-{int(at*10):03}.png');shots.add(at)
   time.sleep(max(0,began+(k+1)/12-time.monotonic()))
  enc.stdin.close();assert enc.wait(timeout=20)==0
  states=[dict(re.findall(r'(\w+)=(-?[0-9.]+)',s)) for s in log.read_text(errors='replace').splitlines() if s.startswith('MODELCHECK ')]
  assert len(states)>30 and all(s['active']=='1' for s in states)
  if case=='gear':assert min(float(s['gear']) for s in states)<.01 and max(float(s['gear']) for s in states)>.99 and float(states[-1]['gear'])<.01
  if case=='canopy':assert max(float(s['canopy']) for s in states)>.99 and float(states[-1]['canopy'])<.01
  (out/'results.json').write_text(json.dumps({'passed':True,'native_XTest_keyboard_events':events,'states':states},indent=2))
finally:
 game.terminate()
 try:game.wait(timeout=10)
 except subprocess.TimeoutExpired:game.kill();game.wait()
