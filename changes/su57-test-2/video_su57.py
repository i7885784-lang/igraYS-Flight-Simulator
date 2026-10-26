from pathlib import Path
import subprocess,time,importlib.machinery,json,re,sys
r=Path('/workspace/ysflight-work');lab=r/'su57-lab2';rt=lab/'runtime';out=lab/'videos';out.mkdir(exist_ok=True);profile=r/'su57-lab2-user';t=importlib.machinery.SourceFileLoader('su57_video_helpers',str(r/'v8_5-tests.py')).load_module();results={}
results=json.loads((out/'checks.json').read_text())['native_end_states'] if (out/'checks.json').exists() else {}
for kind in (sys.argv[1:] or ['gear','canopy','controls']):
 pose=lab/f'captures/su57/after/real-{"canopy" if kind=="canopy" else "gear"}/pose.yfs';fixture=pose.read_text()
 if kind=='controls':fixture=fixture.replace('1000m','3000m')
 pf=out/(kind+'.yfs');pf.write_text(fixture)
 view='100 8 82' if kind=='canopy' else ('35 -12 90' if kind=='gear' else '30 15 95')
 script=t.prefix+'SLEEP:18000\nFILE:OPEN Z:'+str(pf)+'\nGUI:CLICK mainDlg flyNow\nWAITFOR:FLYING\nFLIGHTCMD:MODELPOSE -1 -1 -2 -2 -2 -2\nBTNFUNC:COCKPITVIEW\nFLIGHTCMD:LABVIEW '+view+' 0\n'+'BTNFUNC:VIEWZOOM\n'*26+'SLEEP:26000\nFLIGHTCMD:MODELCHECK\nSLEEP:19999\n';sf=out/(kind+'.script');sf.write_text(script);log=out/(kind+'.log')
 with log.open('w') as f:game=subprocess.Popen([t.wine,str(rt/'exterior-lab64.exe'),'-userdir','Z:'+str(profile),'-configdir','Z:'+str(profile/'config'),'-script','Z:'+str(sf)],cwd=rt,env=t.env,stdout=f,stderr=f)
 try:
  for k in range(80):
   try:info=t.window('resize');break
   except Exception:time.sleep(.15)
  t.wait(log,'Script>>SLEEP:26000',100)
  duration=12 if kind=='controls' else 10
  ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','x11grab','-video_size','1280x800','-framerate','20','-i',f":99.0+{info['x']},{info['y']}",'-t',str(duration),'-an','-c:v','libx264','-preset','ultrafast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(out/(kind+'.mp4'))],env=t.env)
  time.sleep(.5)
  if kind=='gear':t.u.key('g');time.sleep(4);t.u.key('g')
  elif kind=='canopy':
   def toggle():t.u.command('keydown','alt');t.u.key('5');t.u.command('keyup','alt')
   toggle();time.sleep(4);toggle()
  else:
   for key in ['Down','Up','Left','Right','z','c']:
    t.u.command('keydown',key);time.sleep(.40);t.u.command('keyup',key);time.sleep(.55)
   t.u.key('b');time.sleep(2);t.u.key('b')
  ff.wait(timeout=25);t.wait(log,'Script>>SLEEP:19999',40)
 finally:t.u.key('alt+F4');game.wait(timeout=20)
 rows=[{k:float(v) for k,v in re.findall(r'(\w+)=(-?[0-9.]+)',line)} for line in log.read_text(errors='replace').splitlines() if line.startswith('MODELCHECK ')]
 assert rows and rows[-1]['active']==1 and rows[-1]['renderGear']==-1 and rows[-1]['renderCanopy']==-1
 if kind in ['gear','canopy']:assert rows[-1][kind]<.01
 subprocess.run(['ffmpeg','-v','error','-i',str(out/(kind+'.mp4')),'-f','null','-'],check=True);results[kind]=rows[-1];print('VIDEO VERIFIED',kind,flush=True)
(out/'checks.json').write_text(json.dumps({'passed':True,'native_end_states':results},indent=2))
