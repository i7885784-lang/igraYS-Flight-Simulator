"""Run genuine Windows executables, inspect extremes, then actual keyboard inputs."""
from pathlib import Path
import ctypes as C,ctypes.wintypes as W,sys,json,subprocess,time,re,hashlib,math
from PIL import ImageGrab,ImageStat
from prepare import ROOT,META,SHA,pe
bits=int(sys.argv[1]);rt=ROOT/'runtime';out=ROOT/f'native-{bits}';out.mkdir(exist_ok=True);profile=out/'profile';(profile/'config').mkdir(parents=True,exist_ok=True)
(profile/'config/option.cfg').write_text('OPENDEMO FALSE\nFONTHEIGHT 18\nLANGUAGE "FILE:ru.uitxt"\n');(out/'start.yfs').write_text((ROOT/'changes/su30sm-nozzle-vector/windows-start.yfs').read_text())
script='WAITFOR:GUI\nSLEEP:500\n'+'GUI:CLOSEMODAL\n'*4+'SLEEP:8000\nFILE:OPEN '+str(out/'start.yfs').replace('\\','/')+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\n'
poses=[('neutral-open',0,0,1,0),('up-open',15,15,1,0),('down-open',-15,-15,1,0),('differential',15,-15,1,0),('narrow',0,0,0,0),('up-narrow',15,15,0,0),('gear-open',0,0,.5,1),('gear-half',0,0,.5,.5)]
if bits==64:
 script+='FLIGHTCMD:TESTADVANCE .1\nBTNFUNC:PAUSESIMULATION\n'
 for name,a,b,opening,g in poses:
  script+=f'FLIGHTCMD:MODELPOSE {g} 0 0 0 0 0\nFLIGHTCMD:NOZZLEPOSE {a} {b} {opening}\nFLIGHTCMD:MODELCHECK\nBTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABAIM 0 -.5 -9\nFLIGHTCMD:LABVIEW 22 -3 30 0\n'+'BTNFUNC:VIEWZOOM\n'*26+f'REM SHOT_{name}\nSLEEP:1800\n'
 script+='FLIGHTCMD:MODELPOSE -1 -1 -2 -2 -2 -2\nFLIGHTCMD:NOZZLEPOSE 0 0 1\nBTNFUNC:PAUSESIMULATION\n'
else:script+='BTNFUNC:OUTSIDEPLAYERVIEW\n'+'BTNFUNC:VIEWZOOM\n'*20
script+='REM LIVE_READY\n'
if bits==64:script+=('FLIGHTCMD:MODELCHECK\nSLEEP:200\n'*300)
else:script+='SLEEP:65000\n'
script+='SLEEP:60000\n';(out/'run.script').write_text(script)
exe=rt/f'ysflight{bits}_gl1.exe';exe_data=exe.read_bytes();arch=pe(exe_data,bits);info=json.loads((ROOT/'work/built/build-info.json').read_text());assert SHA(exe_data)==info['exe_sha256'];handle=(out/'game.log').open('w');game=subprocess.Popen([str(exe),'-userdir',str(profile),'-configdir',str(profile/'config'),'-script',str(out/'run.script')],cwd=rt,stdout=handle,stderr=handle)
log=out/'game.log'
def wait(s,timeout=120):
 until=time.monotonic()+timeout
 while time.monotonic()<until:
  t=log.read_text(errors='replace')
  if s in t:return t
  if game.poll() is not None:raise RuntimeError('Game exited '+str(game.returncode)+'\n'+t[-1500:])
  time.sleep(.1)
 raise RuntimeError('Timeout '+s)
u=C.windll.user32;u.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)];u.IsWindowVisible.argtypes=[W.HWND];u.SetWindowLongW.argtypes=[W.HWND,C.c_int,C.c_long];u.MoveWindow.argtypes=[W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.BOOL];u.SetForegroundWindow.argtypes=[W.HWND]
frames=[]
def shot(name):
 u.SetForegroundWindow(window);im=ImageGrab.grab(bbox=(0,0,1024,768)).convert('RGB');assert max(ImageStat.Stat(im).stddev)>12;im.save(out/(name+'.png'));frames.append(name);print(bits,name,flush=True)
def key(vk,down):u.keybd_event(vk,0,0 if down else 2,0)
def tap(vk):key(vk,True);time.sleep(.04);key(vk,False)
def pulse(vk,seconds=.45):key(vk,True);time.sleep(seconds);key(vk,False);time.sleep(.65)
try:
 wait('Script>>SLEEP:8000');wins=[]
 @C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
 def enum(h,l):
  pid=W.DWORD();u.GetWindowThreadProcessId(h,C.byref(pid))
  if pid.value==game.pid and u.IsWindowVisible(h):wins.append(h)
  return True
 u.EnumWindows(enum,0);assert wins;window=wins[-1];u.SetWindowLongW(window,-16,0x90000000);u.MoveWindow(window,0,0,1024,768,True);u.SetForegroundWindow(window)
 if bits==64:
  for name,*_ in poses:wait('Script>>REM SHOT_'+name);time.sleep(.4);shot(name)
 wait('Script>>REM LIVE_READY');time.sleep(1)
 for i in range(22):tap(0x51);time.sleep(.025)
 time.sleep(5);shot('live-dry-narrow');tap(9);time.sleep(3.5);shot('live-afterburner-open')
 for vk,name in [(0x28,'pitch-up'),(0x26,'pitch-down'),(0x25,'roll-left'),(0x27,'roll-right'),(0x5A,'rudder-left'),(0x43,'rudder-right')]:pulse(vk);shot('live-'+name)
 tap(0x58);tap(9)
 for i in range(22):tap(0x41);time.sleep(.02)
 time.sleep(4);shot('live-idle');tap(0x47);time.sleep(6);shot('live-gear-down');tap(0x47);time.sleep(6);shot('live-gear-up')
 t=log.read_text(errors='replace');states=[dict(re.findall(r'(\w+)=(-?[0-9.]+)',s)) for s in t.split('Script>>REM LIVE_READY',1)[-1].splitlines() if s.startswith('MODELCHECK ')]
 if bits==64:
  assert len(states)>20 and all(s['active']=='1' for s in states)
  assert min(float(s['nozzle']) for s in states)<.20 and max(float(s['nozzle']) for s in states)>.90
  for k in ['tvLdeg','tvRdeg']:
   v=[float(s[k]) for s in states];assert min(v)<-.1 and max(v)>.1 and max(map(abs,v))<=15.001,(k,min(v),max(v))
  assert any(s['ab']=='1' for s in states)
  assert all(s['ab']!='1' or float(s['nozzle'])>=.69 for s in states),'Reheat before nozzle ready'
 assert SHA((rt/'aircraft/su30sm.dnm').read_bytes())==META['model_sha256'];assert SHA((rt/'aircraft/su30smcockpit.dnm').read_bytes())==META['cockpit_sha256']
 assert len({SHA((out/(n+'.png')).read_bytes()) for n in frames})>=6,'Static desktop/menu'
 result=dict(passed=True,native_windows=True,wine=False,bits=bits,exe_sha256=SHA(exe_data),model_sha256=META['model_sha256'],cockpit_sha256=META['cockpit_sha256'],frames=frames,states=states,scope='x64: diagnostic envelope plus real keyboard throttle/AB/three control axes/gear; x86: ordinary camera and real keyboard actions (no diagnostic commands)',**arch)
 (out/'results.json').write_text(json.dumps(result,indent=2))
finally:
 for vk in [0x28,0x26,0x25,0x27,0x5A,0x43,0x51,0x41]:key(vk,False)
 game.terminate();game.wait(timeout=20);handle.close()
