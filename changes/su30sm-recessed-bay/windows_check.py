"""Native Windows PE32/PE32+ launch and actual desktop capture, no Wine."""
from pathlib import Path
import ctypes as C, ctypes.wintypes as W, os,time,subprocess,json,re,hashlib,struct,sys
from PIL import ImageGrab,ImageStat
bits=int(sys.argv[1]);root=Path.cwd();rt=root/'runtime';out=root/f'native-{bits}';out.mkdir(exist_ok=True);profile=out/'profile';(profile/'config').mkdir(parents=True,exist_ok=True)
(profile/'config/option.cfg').write_text('OPENDEMO FALSE\nFONTHEIGHT 18\nLANGUAGE "FILE:ru.uitxt"\n')
fixture=(root/'changes/su30sm-recessed-bay/windows-start.yfs').read_text();(out/'start.yfs').write_text(fixture)
views=[('open',165,-10,38,'0 -.3 -1.5',1),('near-front',175,-10,38,'0 -.3 -1.5',1),('opposite',195,-10,38,'0 -.3 -1.5',1),('closed',165,-10,38,'0 -.3 -1.5',0),('intermediate',165,-10,38,'0 -.3 -1.5',.5),('bottom',180,-89,80,'0 -.5 -1.4',0),('top',180,89,95,'0 -.5 -1.4',0)]
script='WAITFOR:GUI\nSLEEP:500\n'+'GUI:CLOSEMODAL\n'*4+'SLEEP:8000\nFILE:OPEN '+str(out/'start.yfs').replace('\\','/')+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\nFLIGHTCMD:TESTADVANCE .1\nBTNFUNC:PAUSESIMULATION\n'
for name,h,p,d,aim,g in views:
 script+=f'FLIGHTCMD:MODELPOSE {g} 0 0 0 0 0\nFLIGHTCMD:MODELCHECK\nBTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABAIM {aim}\nFLIGHTCMD:LABVIEW {h} {p} {d} 0\n'+'BTNFUNC:VIEWZOOM\n'*26+f'REM SHOT_{name}\nSLEEP:2400\n'
if bits==32:
 views=[('gear-up',),('transition-down',),('gear-down',),('transition-up',),('gear-up-final',),('rear-quarter',)]
 script='WAITFOR:GUI\nSLEEP:500\n'+'GUI:CLOSEMODAL\n'*4+'SLEEP:8000\nFILE:OPEN '+str(out/'start.yfs').replace('\\','/')+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\nBTNFUNC:OUTSIDEPLAYERVIEW\n'+'BTNFUNC:VIEWZOOM\n'*20+'REM SHOT_gear-up\nSLEEP:2000\nBTNFUNC:LANDINGGEAR\nSLEEP:800\nREM SHOT_transition-down\nSLEEP:6500\nREM SHOT_gear-down\nSLEEP:2200\nBTNFUNC:LANDINGGEAR\nSLEEP:800\nREM SHOT_transition-up\nSLEEP:6500\nREM SHOT_gear-up-final\nSLEEP:2200\nBTNFUNC:OUTSIDEPLAYERVIEW2\nREM SHOT_rear-quarter\nSLEEP:2200\n'
script+='SLEEP:60000\n';(out/'run.script').write_text(script)
exe=rt/f'ysflight{bits}_gl1.exe';b=exe.read_bytes();off=struct.unpack_from('<I',b,0x3c)[0];machine=struct.unpack_from('<H',b,off+4)[0];assert machine==(0x14c if bits==32 else 0x8664)
log=out/'game.log';handle=log.open('w');game=subprocess.Popen([str(exe),'-userdir',str(profile),'-configdir',str(profile/'config'),'-script',str(out/'run.script')],cwd=rt,stdout=handle,stderr=handle)
def wait(s,timeout=120):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  t=log.read_text(errors='replace')
  if s in t:return t
  if game.poll() is not None:raise RuntimeError(f'Game exited {game.returncode}\n'+t[-2000:])
  time.sleep(.1)
 raise RuntimeError('Timeout '+s+'\n'+log.read_text(errors='replace')[-2000:])
u=C.windll.user32;u.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)];u.IsWindowVisible.argtypes=[W.HWND];u.SetWindowLongW.argtypes=[W.HWND,C.c_int,C.c_long];u.MoveWindow.argtypes=[W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.BOOL];u.SetForegroundWindow.argtypes=[W.HWND]
try:
 wait('Script>>SLEEP:8000');wins=[]
 @C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
 def enum(h,l):
  pid=W.DWORD();u.GetWindowThreadProcessId(h,C.byref(pid))
  if pid.value==game.pid and u.IsWindowVisible(h):wins.append(h)
  return True
 u.EnumWindows(enum,0);assert wins,'No visible native game window';window=wins[-1];u.SetWindowLongW(window,-16,0x90000000);u.MoveWindow(window,0,0,1024,768,True);u.SetForegroundWindow(window)
 for name,*_ in views:
  wait('Script>>REM SHOT_'+name);time.sleep(.6);im=ImageGrab.grab(bbox=(0,0,1024,768),all_screens=False).convert('RGB');assert max(ImageStat.Stat(im).stddev)>12,'Blank desktop';im.save(out/(name+'.png'));print(bits,name,flush=True)
 states=[dict(re.findall(r'(\w+)=(-?[0-9.]+)',l)) for l in log.read_text(errors='replace').splitlines() if l.startswith('MODELCHECK ')];assert bits==32 or (len(states)==len(views) and all(s['active']=='1' for s in states))
 assert hashlib.sha256((rt/'aircraft/su30sm.dnm').read_bytes()).hexdigest()==json.loads((root/'dist/su30sm-recessed-bay/metadata.json').read_text())['model_sha256']
 assert len({hashlib.sha256((out/(v[0]+'.png')).read_bytes()).hexdigest() for v in views})>=4, 'Desktop stayed on startup/menu; screenshot verification failed'
 assert hashlib.sha256((rt/'aircraft/su30smcockpit.dnm').read_bytes()).hexdigest()=='564308f1149862461dbc254dfb4372475a067ed0182eb61faf9d7345fa1807b9'
 result={'passed':True,'native_windows':True,'wine':False,'bits':bits,'machine':hex(machine),'exe_sha256':hashlib.sha256(b).hexdigest(),'model_sha256':hashlib.sha256((rt/'aircraft/su30sm.dnm').read_bytes()).hexdigest(),'frames':[x[0] for x in views],'states':states,'scope':'Native Windows real game captures; x86 uses ordinary native gear buttons (diagnostic MODELPOSE/LABVIEW commands unavailable), x64 uses diagnostic camera poses.'};(out/'results.json').write_text(json.dumps(result,indent=2))
finally:
 game.terminate();game.wait(timeout=20);handle.close()
