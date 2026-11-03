from pathlib import Path
import os,sys,subprocess,time,re,ctypes,json,shutil
from PIL import ImageGrab
r=Path(__file__).parent;ident=sys.argv[1] if len(sys.argv)>1 else 'SU-30SM_CUSTOM';out=r/'checks'/('camera-'+ident);out.mkdir(parents=True,exist_ok=True);rt=r/'runtime';profile=r/('user-camera-'+ident);shutil.copytree(rt/'config',profile/'config',dirs_exist_ok=True);(profile/'config/option.cfg').write_text('OPENDEMO FALSE\nFONTHEIGHT 18\nLANGUAGE "FILE:ru.uitxt"\n')
fixture=f'''YFSVERSI 20180930
FIELDNAM STRAIGHT_TEST 0 0 0 0 0 0 FALSE LOADAIR:FALSE
INITPLYR AIR 1
CANCONTI TRUE
ENVIRONM DAY
AIRPLANE {ident} TRUE
IDENTIFY 0
IDANDTAG 1 "CAMERA_CHECK"
AIRPCMND UNLOADWP
AIRPCMND INITFUEL 50%
AIRPCMND POSITION 0m 1000m 0m
AIRPCMND ATTITUDE 0deg 0deg 0deg
AIRPCMND INITSPED 180m/s
AIRPCMND CTLLDGEA FALSE
AIRPCMND CTLTHROT 0.55
AIRPCMND CTLABRNR FALSE
''';(out/'start.yfs').write_text(fixture)
script='WAITFOR:GUI\nSLEEP:500\n'+'GUI:CLOSEMODAL\n'*4+'SLEEP:4000\nFILE:OPEN Z:'+str(out/'start.yfs')+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\nBTNFUNC:COCKPITVIEW\nREM CAMERA_READY\nSLEEP:60000\n';script=script.replace('WAITFOR:FLYING\nBTNFUNC:COCKPITVIEW\n','WAITFOR:FLYING\nBTNFUNC:OUTSIDEPLAYERVIEW\n'+'BTNFUNC:VIEWZOOM\n'*26+'BTNFUNC:COCKPITVIEW\n');(out/'run.script').write_text(script)
log=out/'game.log';x=ctypes.CDLL('libX11.so.6');xt=ctypes.CDLL('libXtst.so.6');x.XOpenDisplay.restype=ctypes.c_void_p;d=x.XOpenDisplay(os.environ['DISPLAY'].encode());assert d
x.XStringToKeysym.argtypes=[ctypes.c_char_p];x.XStringToKeysym.restype=ctypes.c_ulong;x.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong];x.XKeysymToKeycode.restype=ctypes.c_uint
xt.XTestFakeKeyEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong];xt.XTestFakeButtonEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong];xt.XTestFakeMotionEvent.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ulong];x.XFlush.argtypes=[ctypes.c_void_p]
def key(name,v):xt.XTestFakeKeyEvent(d,x.XKeysymToKeycode(d,x.XStringToKeysym(name.encode())),int(v),0);x.XFlush(d)
def move(px,py):xt.XTestFakeMotionEvent(d,0,px,py,0);x.XFlush(d)
def button(v):xt.XTestFakeButtonEvent(d,1,int(v),0);x.XFlush(d)
def tap():key('space',True);time.sleep(.08);key('space',False);time.sleep(.12)
def shot(n):ImageGrab.grab(bbox=(0,0,1024,768),xdisplay=os.environ['DISPLAY']).save(out/(n+'.png'))
with log.open('w') as f:
 app=subprocess.Popen([os.environ['WINELOADER'],str(rt/'ysflight64_gl1.exe'),'-userdir','Z:'+str(profile),'-configdir','Z:'+str(profile/'config'),'-script','Z:'+str(out/'run.script')],cwd=rt,stdout=f,stderr=f)
 enc=None
 try:
  end=time.monotonic()+100
  while 'Script>>REM CAMERA_READY' not in log.read_text(errors='replace'):
   if app.poll() is not None:raise RuntimeError(log.read_text(errors='replace')[-1000:])
   if time.monotonic()>end:raise RuntimeError('Camera flight timeout')
   time.sleep(.2)
  subprocess.run([os.environ['WINELOADER'],str(r/'resize_capture.exe')],check=True);time.sleep(.4)
  tree=subprocess.check_output(['xwininfo','-root','-tree'],text=True);win=next(int(w,16) for w,t in re.findall(r'(0x[0-9a-f]+) "([^"]+)"',tree) if 'YS' in t.upper() and 'FLIGHT' in t.upper())
  x.XMoveWindow.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_int];x.XMoveWindow(d,win,0,0);x.XSetInputFocus.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];x.XSetInputFocus(d,win,1,0);x.XFlush(d);time.sleep(.5)
  enc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','x11grab','-framerate','12','-video_size','1024x768','-i',os.environ['DISPLAY']+'.0+0,0','-an','-c:v','libx264','-pix_fmt','yuv420p',str(out/'camera.mp4')],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  shot('forward');move(500,380);time.sleep(.2);button(True);time.sleep(.2)
  for k in range(1,7):move(500+30*k,380-5*k);time.sleep(.1)
  button(False);time.sleep(.4);shot('look-right');tap();tap();time.sleep(.4);shot('reset-forward');time.sleep(.8)
  text=log.read_text(errors='replace');matches=re.findall(r'COCKPITLOOK drag h=([-0-9.]+) p=([-0-9.]+)',text);assert matches and abs(float(matches[-1][0]))>.1,'Mouse drag did not rotate camera';assert 'COCKPITLOOK reset=1' in text,'Double space did not reset'
  (out/'results.json').write_text(json.dumps({'passed':True,'aircraft':ident,'left_mouse_drag':list(matches[-1]),'double_space_reset':True,'from_external_zoom_26':True,'cockpit_position':'0 1.18 5.55' if ident=='SU-30SM_CUSTOM' else 'existing aircraft eye point'},indent=2))
 finally:
  if enc:
   enc.terminate()
   try:enc.wait(timeout=10)
   except subprocess.TimeoutExpired:enc.kill()
  app.terminate()
  try:app.wait(timeout=10)
  except subprocess.TimeoutExpired:app.kill()
