from pathlib import Path
import os,sys,subprocess,time,re,ctypes,json,shutil
from PIL import ImageGrab
lab=Path(__file__).resolve().parent;rt=Path(os.environ.get('GAME_RUNTIME',str(lab/'runtime')));case=sys.argv[1];out=lab/'checks'/os.environ.get('CHECK_NAME',case);out.mkdir(parents=True,exist_ok=True)
(out/'results.json').unlink(missing_ok=True)
profile=lab/('user-'+case);shutil.copytree(rt/'config',profile/'config',dirs_exist_ok=True)
cfg=profile/'config/flight.cfg';cfg.write_text(cfg.read_text()+'\nTRSPLATER '+os.environ.get('LATE_TRANSPARENT','TRUE')+'\n')
(profile/'config/option.cfg').write_text('OPENDEMO FALSE\nFONTHEIGHT 18\nLANGUAGE "FILE:ru.uitxt"\n')
ident=os.environ.get('AIRCRAFT_CHECK','SU-27_FLANKER');ground=case in ['canopy','ground'];height=({'SU-27_FLANKER':2.48,'MIG-29_FULCRUM':1.74,'SU-57_FELON':2.18,'SU-34_FULLBACK':2.53}.get(ident,3.12)) if ground else 1000
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
(out/'start.yfs').write_text(fixture)
fixture=fixture.replace('STRAIGHT_TEST','AOMORI')
(out/'start.yfs').write_text(fixture)
views=[('rear-high',25,60,65),('top',0,89,70),('side-high',75,45,65)]
script='WAITFOR:GUI\nSLEEP:500\n'+'GUI:CLOSEMODAL\n'*4+'SLEEP:8000\nFILE:OPEN Z:'+str(out/'start.yfs')+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\nFLIGHTCMD:TESTADVANCE .1\nREM WARM_READY\nSLEEP:12000\nBTNFUNC:PAUSESIMULATION\nFLIGHTCMD:AIRCOMMAND $PLAYER POSITION 48641.81m 3m -11082.90m\nFLIGHTCMD:AIRCOMMAND $PLAYER ATTITUDE 0deg 0deg 0deg\n'+'BTNFUNC:VIEWZOOM\n'*26
for name,h,p,d in views:
 script+=f'BTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABAIM 0 -.3 -5\nFLIGHTCMD:LABVIEW {h} {p} {d} 0\nREM SHOT_{name}\nFLIGHTCMD:MODELCHECK\nSLEEP:1800\n'
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
 wait('Script>>REM WARM_READY')
 for _ in range(20):combo('q')
 combo('Tab')
 for name,*_ in views:
  wait('Script>>REM SHOT_'+name);time.sleep(.4);ImageGrab.grab(xdisplay=':99').save(out/(name+'.png'))
 states=[dict(re.findall(r'(\w+)=(-?[0-9.]+)',s)) for s in log.read_text(errors='replace').splitlines() if s.startswith('MODELCHECK ')]
 assert states and all(s['active']=='1' and s['ab']=='1' for s in states),states
 (out/'results.json').write_text(json.dumps({'passed':True,'aircraft':ident,'paused_body_live_engine_warmup':True,'shadow_overlap_views':[v[0] for v in views],'states':states},indent=2))

finally:
 game.terminate()
 try:game.wait(timeout=10)
 except subprocess.TimeoutExpired:game.kill();game.wait()
