from pathlib import Path
import subprocess,time,importlib.machinery,json
from PIL import ImageGrab
lab=Path(__file__).resolve().parent;r=lab.parent;rt=lab/'runtime';out=lab/'orbit';out.mkdir(exist_ok=True);t=importlib.machinery.SourceFileLoader('orbit_helpers',str(r/'v8_5-tests.py')).load_module();profile=r/'su57-lab2-user';pose=lab/'captures/su57/after/views/pose.yfs'
frames=[(f'upper-{i:02}',i*10,20) for i in range(36)]+[(f'lower-{i:02}',i*30,-20) for i in range(12)]
script=t.prefix+'SLEEP:18000\nFILE:OPEN Z:'+str(pose)+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\nFLIGHTCMD:TESTADVANCE .1\nBTNFUNC:PAUSESIMULATION\n'
for i,(name,hdg,pitch) in enumerate(frames):
 script+=f'BTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABVIEW {hdg} {pitch} 115 0\n'
 if i==0:script+='BTNFUNC:VIEWZOOM\n'*26
 script+=f'SLEEP:{1300+i}\n'
script+='FLIGHTCMD:MODELCHECK\nSLEEP:19999\n';sf=out/'orbit.script';sf.write_text(script);log=out/'orbit.log'
with log.open('w') as f:game=subprocess.Popen([t.wine,str(rt/'exterior-lab64.exe'),'-userdir','Z:'+str(profile),'-configdir','Z:'+str(profile/'config'),'-script','Z:'+str(sf)],cwd=rt,env=t.env,stdout=f,stderr=f)
try:
 for k in range(80):
  try:info=t.window('resize');break
  except Exception:time.sleep(.15)
 for i,(name,hdg,pitch) in enumerate(frames):
  t.wait(log,f'Script>>SLEEP:{1300+i}',120);time.sleep(.28);ImageGrab.grab(xdisplay=':99',bbox=(info['x'],info['y'],info['x']+info['width'],info['y']+info['height'])).save(out/(name+'.png'));print('ORBIT',name,flush=True)
 t.wait(log,'Script>>SLEEP:19999',30)
finally:t.u.key('alt+F4');game.wait(timeout=20)
subprocess.run(['ffmpeg','-y','-v','error','-framerate','3','-i',str(out/'upper-%02d.png'),'-frames:v','36','-c:v','libx264','-r','30','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'orbit-360.mp4')],check=True)
(out/'results.json').write_text(json.dumps({'passed':True,'upper_views':36,'lower_views':12,'heading_step_deg':10,'source':'native paused game camera frames, not image generation'},indent=2))
