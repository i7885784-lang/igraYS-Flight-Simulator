from pathlib import Path
import subprocess,time,importlib.machinery,json,re,sys
from PIL import ImageGrab
r=Path('/workspace/ysflight-work');lab=r/'su57-lab2';p=lab/'runtime';t=importlib.machinery.SourceFileLoader('helpcycle',str(r/'v8_5-tests.py')).load_module();profile=r/'su57-lab2-user';model=sys.argv[1];kind=sys.argv[2];out=lab/'captures'/model/'after'/('real-'+kind);out.mkdir(parents=True,exist_ok=True)
ident={'su27':'SU-27_FLANKER','mig29':'MIG-29_FULCRUM','su57':'SU-57_FELON'}[model];h=(2.18 if model=='su57' else (1.9 if model=='su27' else 1.7)) if kind=='canopy' else 1000
fixture=f'''YFSVERSI 20180930
FIELDNAM STRAIGHT_TEST 0 0 0 0 0 0 FALSE LOADAIR:FALSE
INITPLYR AIR 1
CANCONTI TRUE
ENVIRONM DAY
EXTENSIO AIRSHOW_V8 CONFIG 0 0 0 16 0.2 0.35
AIRPLANE {ident} TRUE
IDENTIFY 0
IDANDTAG 1 "ANIMATION_TEST"
AIRPCMND UNLOADWP
AIRPCMND INITFUEL 50%
AIRPCMND ATTITUDE 0deg 0deg 0deg
AIRPCMND POSITION 0m {h}m 0m
AIRPCMND INITSPED {0 if kind=='canopy' else 180}m/s
AIRPCMND CTLLDGEA {'TRUE' if kind=='canopy' else 'FALSE'}
AIRPCMND CTLTHROT {0 if kind=='canopy' else .55}
AIRPCMND CTLABRNR FALSE
'''
if kind=='canopy':fixture=fixture.replace('FIELDNAM STRAIGHT_TEST','FIELDNAM AOMORI').replace(f'POSITION 0m {h}m 0m',f'POSITION 48641.81m {h}m -11082.90m')
pose=out/'pose.yfs';pose.write_text(fixture)
script=t.prefix+'SLEEP:18000\nFILE:OPEN Z:'+str(pose)+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\nFLIGHTCMD:TESTADVANCE .1\nBTNFUNC:PAUSESIMULATION\nFLIGHTCMD:MODELPOSE -1 -1 -2 -2 -2 -2\nBTNFUNC:COCKPITVIEW\n'+('FLIGHTCMD:LABVIEW 100 7 95 0\n' if kind=='canopy' else 'FLIGHTCMD:LABVIEW 40 -14 90 0\n')+'BTNFUNC:VIEWZOOM\n'*26+'FLIGHTCMD:SU27CHECK\nFLIGHTCMD:MODELCHECK\n'
frames=[]
for direction in ['out','back']:
 script+=('SLEEP:3200\n' if direction=='out' else 'SLEEP:3300\n') if kind=='canopy' else 'BTNFUNC:LANDINGGEAR\nSLEEP:400\n'
 for i in range(4):
  marker=1100+len(frames);name=direction+'-'+str(i+1);frames.append((marker,name));script+=f'FLIGHTCMD:TESTADVANCE {.625 if kind=="canopy" else .5}\nFLIGHTCMD:SU27CHECK\nFLIGHTCMD:MODELCHECK\nSLEEP:{marker}\n'
if kind=='gear':script+='BTNFUNC:FLAPFULLDOWN\nSLEEP:400\nFLIGHTCMD:TESTADVANCE 3\nFLIGHTCMD:SU27CHECK\nFLIGHTCMD:MODELCHECK\n'
script+='SLEEP:19999\n';file=out/'cycle.script';file.write_text(script);log=out/'cycle.log'
with log.open('w') as f:game=subprocess.Popen([t.wine,str(p/'exterior-lab64.exe'),'-userdir','Z:'+str(profile),'-configdir','Z:'+str(profile/'config'),'-script','Z:'+str(file)],cwd=p,env=t.env,stdout=f,stderr=f)
def action():
 t.u.command('keydown','alt');time.sleep(.15);t.u.command('keydown','5');time.sleep(.35);t.u.command('keyup','5');time.sleep(.15);t.u.command('keyup','alt')
try:
 for k in range(60):
  try:info=t.window('resize');break
  except Exception:time.sleep(.15)
 for marker,name in frames:
  if kind=='canopy' and name in ['out-1','back-1']:
   t.wait(log,'Script>>SLEEP:'+('3200' if name=='out-1' else '3300'),100);action()
  t.wait(log,f'Script>>SLEEP:{marker}',100);time.sleep(.3);ImageGrab.grab(xdisplay=':99',bbox=(info['x'],info['y'],info['x']+info['width'],info['y']+info['height'])).save(out/(name+'.png'))
 t.wait(log,'Script>>SLEEP:19999',100)
finally:t.u.key('alt+F4');game.wait(timeout=20)
rows=[{k:float(v) for k,v in re.findall(r'(\w+)=(-?[0-9.]+)',line)} for line in log.read_text(errors='replace').splitlines() if line.startswith('MODELCHECK ')]
key='canopy' if kind=='canopy' else 'gear';vals=[row[key] for row in rows[:9]];expected=[0,.25,.5,.75,1,.75,.5,.25,0]
checks=dict(aircraft_active=all(x.get('active',1)==1 for x in rows),nine_states=len(vals)==9,real_states_no_render_override=all(x['renderGear']==-1 and x['renderCanopy']==-1 for x in rows),smooth_out_and_back=len(vals)==9 and max(abs(a-b) for a,b in zip(vals,expected))<.035)
if kind=='gear':checks['flap_input_moves_flaps']=rows[-1]['flap']>.95
result=dict(passed=all(checks.values()),checks=checks,values=vals,samples=rows);(out/'results.json').write_text(json.dumps(result,indent=2));print(model,kind,json.dumps(result),flush=True)
assert result['passed']
