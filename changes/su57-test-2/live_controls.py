from pathlib import Path
import subprocess,time,importlib.machinery,json,re
from PIL import ImageGrab
r=Path('/workspace/ysflight-work');lab=r/'su57-lab2';rt=lab/'runtime';out=lab/'captures/su57/after/live-controls';out.mkdir(parents=True,exist_ok=True);t=importlib.machinery.SourceFileLoader('controls_helper',str(r/'v8_5-tests.py')).load_module();profile=r/'su57-lab2-user'
fixture=(lab/'captures/su57/after/real-gear/pose.yfs').read_text().replace('1000m','3000m');pose=out/'pose.yfs';pose.write_text(fixture)
frames=[('elevator-up','Down', 'elevator',1),('elevator-down','Up','elevator',-1),('roll-left','Left','aileron',1),('roll-right','Right','aileron',-1),('rudder-left','z','rudder',1),('rudder-right','c','rudder',-1)]
script=t.prefix+'SLEEP:18000\nFILE:OPEN Z:'+str(pose)+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\nFLIGHTCMD:TESTADVANCE .1\nBTNFUNC:PAUSESIMULATION\nFLIGHTCMD:MODELPOSE -1 -1 -2 -2 -2 -2\nBTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABVIEW 30 15 95 0\n'+'BTNFUNC:VIEWZOOM\n'*26+'FLIGHTCMD:REPORT\nFLIGHTCMD:MODELCHECK\n'
for i,(name,key,axis,sg) in enumerate(frames):script+=f'BTNFUNC:ELEVATORNEUTRAL\nBTNFUNC:AILERONNEUTRAL\nBTNFUNC:RUDDERCENTER\nSLEEP:{5000+i}\nFLIGHTCMD:MODELCHECK\nSLEEP:{3000+i}\n'
for name,cmd in [('flaps','FLAPFULLDOWN'),('brake','SPOILERBRAKE')]:script+=f'BTNFUNC:{cmd}\nFLIGHTCMD:TESTADVANCE 2.5\nFLIGHTCMD:MODELCHECK\nSLEEP:{7000 if name=="flaps" else 7001}\n'
script+='SLEEP:19999\n';sf=out/'controls.script';sf.write_text(script);log=out/'controls.log'
with log.open('w') as f:game=subprocess.Popen([t.wine,str(rt/'exterior-lab64.exe'),'-userdir','Z:'+str(profile),'-configdir','Z:'+str(profile/'config'),'-script','Z:'+str(sf)],cwd=rt,env=t.env,stdout=f,stderr=f)
try:
 for k in range(80):
  try:info=t.window('resize');break
  except Exception:time.sleep(.15)
 for i,(name,key,axis,sg) in enumerate(frames):
  t.wait(log,f'Script>>SLEEP:{5000+i}',100)
  t.u.key('Pause');time.sleep(.25);t.u.command('keydown',key);time.sleep(.46);t.u.key('Pause');time.sleep(.15)
  t.wait(log,f'Script>>SLEEP:{3000+i}',30);time.sleep(.3);ImageGrab.grab(xdisplay=':99',bbox=(info['x'],info['y'],info['x']+info['width'],info['y']+info['height'])).save(out/(name+'.png'));t.u.command('keyup',key);print('INPUT',name,flush=True)
 for name,marker in [('flaps',7000),('brake',7001)]:
  t.wait(log,f'Script>>SLEEP:{marker}',40);time.sleep(.3);ImageGrab.grab(xdisplay=':99',bbox=(info['x'],info['y'],info['x']+info['width'],info['y']+info['height'])).save(out/(name+'.png'))
 t.wait(log,'Script>>SLEEP:19999',30)
finally:t.u.key('alt+F4');game.wait(timeout=20)
rows=[{k:float(v) for k,v in re.findall(r'(\w+)=(-?[0-9.]+)',line)} for line in log.read_text(errors='replace').splitlines() if line.startswith('MODELCHECK ')]
checks={'nine_checkpoints':len(rows)==9,'all_active':all(x['active']==1 for x in rows),'no_render_overrides':all(x['renderGear']==-1 and x['renderCanopy']==-1 for x in rows)}
for i,(name,key,axis,sg) in enumerate(frames):checks[name]=len(rows)>i+1 and rows[i+1][axis]*sg>.12
checks['flaps_full']=len(rows)>7 and rows[7]['flap']>.95;checks['brake_full']=len(rows)>8 and rows[8]['spoiler']>.95
result={'passed':all(checks.values()),'checks':checks,'samples':rows};(out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True);assert result['passed']
