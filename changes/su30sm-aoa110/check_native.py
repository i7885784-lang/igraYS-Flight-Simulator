"""Actual Windows keyboard flight; no pose/position injection."""
from pathlib import Path
import sys,ctypes as C,ctypes.wintypes as W,subprocess,time,re,json,shutil
from PIL import ImageGrab,ImageStat
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'changes/su30sm-high-alpha'))
from build_candidate import ROOT,STAGE,MODEL,COCKPIT,baseline,pe,SHA
bits=int(sys.argv[1]);rt=ROOT/'runtime';out=ROOT/f'native-{bits}';out.mkdir(exist_ok=True);built=ROOT/'work/built';info=json.loads((built/'build-info.json').read_text())
import zipfile
with zipfile.ZipFile(baseline(bits)) as z:assert z.testzip() is None;z.extractall(ROOT)
exe=rt/f'ysflight{bits}_gl1.exe';exe.write_bytes((built/exe.name).read_bytes());assert SHA(exe.read_bytes())==info['exe_sha256'];pe(exe.read_bytes(),bits)
assert SHA((rt/'aircraft/su30sm.dnm').read_bytes())==MODEL and SHA((rt/'aircraft/su30smcockpit.dnm').read_bytes())==COCKPIT
profile=out/'profile';(profile/'config').mkdir(parents=True,exist_ok=True);(profile/'config/option.cfg').write_text('OPENDEMO FALSE\nFONTHEIGHT 18\nLANGUAGE "FILE:ru.uitxt"\n')
fixture='''YFSVERSI 20180930
FIELDNAM AOMORI 0 0 0 0 0 0 FALSE LOADAIR:FALSE
INITPLYR AIR 1
CANCONTI TRUE
ENVIRONM DAY
EXTENSIO AIRSHOW_V8 CONFIG 0 0 0 16 0.2 0.35
AIRPLANE SU-30SM_CUSTOM TRUE
IDENTIFY 0
IDANDTAG 1 "HIGH_ALPHA_CHECK"
AIRPCMND UNLOADWP
AIRPCMND INITFUEL 50%
AIRPCMND ATTITUDE 0deg 0deg 0deg
AIRPCMND POSITION 48641.81m 2500m -11082.90m
AIRPCMND INITSPED 166.666667m/s
AIRPCMND CTLLDGEA FALSE
AIRPCMND CTLTHROT 0.4
AIRPCMND CTLABRNR FALSE
'''
if bits==32:fixture=fixture.replace('FIELDNAM AOMORI','FIELDNAM STRAIGHT_TEST')
(out/'start.yfs').write_text(fixture)
script='WAITFOR:GUI\nSLEEP:500\n'+'GUI:CLOSEMODAL\n'*4+'SLEEP:8000\nFILE:OPEN '+str(out/'start.yfs').replace('\\','/')+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\n'
if bits==64:script+='FLIGHTCMD:TESTADVANCE .1\nBTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABVIEW 90 5 125 0\n'+'BTNFUNC:VIEWZOOM\n'*26
else:script+='BTNFUNC:PAUSESIMULATION\nBTNFUNC:OUTSIDEPLAYERVIEW\n'+'BTNFUNC:VIEWZOOM\n'*18+'BTNFUNC:PAUSESIMULATION\n'
script+='REM LIVE_READY\n'
for i in range(240):script+='FLIGHTCMD:REPORT\n'+('FLIGHTCMD:MODELCHECK\n' if bits==64 else '')+'SLEEP:100\n'
script+='SLEEP:60000\n';(out/'run.script').write_text(script);log=out/'game.log';h=log.open('w');game=subprocess.Popen([str(exe),'-userdir',str(profile),'-configdir',str(profile/'config'),'-script',str(out/'run.script')],cwd=rt,stdout=h,stderr=h)
u=C.windll.user32;u.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)];u.IsWindowVisible.argtypes=[W.HWND];u.SetWindowLongW.argtypes=[W.HWND,C.c_int,C.c_long];u.MoveWindow.argtypes=[W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.BOOL];u.SetForegroundWindow.argtypes=[W.HWND]
def wait(needle,timeout=100):
 until=time.monotonic()+timeout
 while time.monotonic()<until:
  s=log.read_text(errors='replace')
  if needle in s:return s
  if game.poll() is not None:raise RuntimeError('Game exit '+str(game.returncode))
  time.sleep(.1)
 raise RuntimeError('Timeout '+needle+'\n'+log.read_text(errors='replace')[-1800:])
def key(k,down):u.keybd_event(k,0,0 if down else 2,0)
def toggle():
 u.SetForegroundWindow(window);time.sleep(.2);key(0x11,True);time.sleep(1.2 if bits==32 else .4);key(0x4C,True);time.sleep(1.2 if bits==32 else .5);key(0x4C,False);time.sleep(.1);key(0x11,False);time.sleep(.2)
def shot(n):pass # Numeric check only; no screenshots or video requested.
try:
 wait('Script>>SLEEP:8000');wins=[]
 @C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
 def enum(hwnd,param):
  pid=W.DWORD();u.GetWindowThreadProcessId(hwnd,C.byref(pid))
  if pid.value==game.pid and u.IsWindowVisible(hwnd):wins.append(hwnd)
  return True
 u.EnumWindows(enum,0);assert wins;window=wins[-1];u.SetWindowLongW(window,-16,0x90000000);u.MoveWindow(window,0,0,1024,768,True);u.SetForegroundWindow(window)
 wait('Script>>REM LIVE_READY');time.sleep(.3);shot('normal-default');toggle();wait('SU30_HIGH_ALPHA enabled=1');shot('limiter-enabled');time.sleep(.6);key(0x28,True)
 start=time.monotonic()
 for j in range(88):
  t=time.monotonic()-start
  if t>=8.0:key(0x28,False)
  if j%4==0:shot('flight-%02d'%j)
  time.sleep(max(0,start+(j+1)*.25-time.monotonic()))
 key(0x28,False);shot('recovered');toggle();wait('SU30_HIGH_ALPHA enabled=0');key(0x28,True);time.sleep(.4);key(0x28,False);time.sleep(1);shot('normal-restored')
 text=log.read_text(errors='replace');states=[dict(re.findall(r'(\w+)=(-?[0-9.]+)',s)) for s in text.splitlines() if s.startswith('MODELCHECK ')]
 if bits==64:
  high=[s for s in states if s['highAlpha']=='1'];assert high and all(s['active']=='1' for s in states)
  peak=max(float(s['aoaDeg']) for s in high)
  assert 95<peak<=110.5,('Positive limiter outside tolerance',peak)
  assert abs(float(high[-1]['aoaDeg']))<20,'No recovery'
  assert states[0]['highAlpha']=='0' and states[-1]['highAlpha']=='0'
 result=dict(passed=True,native_windows=True,bits=bits,exe_sha256=info['exe_sha256'],model_sha256=MODEL,cockpit_sha256=COCKPIT,states=states,scope='Actual full-stick limiter approach and release; x64 exact AOA telemetry, x86 keyboard activation and restoration. No video or screenshots.',**pe(exe.read_bytes(),bits));(out/'results.json').write_text(json.dumps(result,indent=2))
finally:
 for k in [0x28,0x11,0x4C]:key(k,False)
 game.terminate();game.wait(timeout=20);h.close()
