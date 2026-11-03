from pathlib import Path
import subprocess,tempfile,zipfile,json,time,hashlib,shutil
repo='i7885784-lang/igraYS-Flight-Simulator';tag='personal-su30sm-test3-20261103';evidence=Path('windows-evidence').resolve();evidence.mkdir(exist_ok=True)
def gh(*a):return subprocess.check_output(['gh',*a])
with tempfile.TemporaryDirectory() as td:
 t=Path(td);gh('release','download',tag,'--repo',repo,'--pattern','YSFlight_Su30SM_Test_3_Game_Win32_Win64.zip','--pattern','YSFlight_Su30SM_Test_3_Report.zip','--pattern','STATUS.json','--dir',str(t))
 status=json.loads((t/'STATUS.json').read_text());name='YSFlight_Su30SM_Test_3_Game_Win32_Win64.zip';assert hashlib.sha256((t/name).read_bytes()).hexdigest()==next(x['sha256'] for x in status['assets'] if x['name']==name)
 with zipfile.ZipFile(t/name) as z:z.extractall(t)
 game=t/'runtime';script=(game/'Start_Su30SM.script').read_text()+'\nBTNFUNC:LANDINGGEAR\nSLEEP:9000\nBTNFUNC:LANDINGGEAR\nSLEEP:9000\nBTNFUNC:COCKPITVIEW\nSLEEP:1500\nREM SU30_TEST3_WINDOWS32_COMPLETE\nSLEEP:60000\n';(game/'WindowsSmoke.script').write_text(script)
 profile=game/'user-su30';profile.mkdir(exist_ok=True);log=evidence/'windows-x86.log';start=time.monotonic()
 with log.open('w') as f:
  app=subprocess.Popen([str(game/'ysflight32_gl1.exe'),'-userdir',str(profile),'-configdir',str(game/'config-su30'),'-script','WindowsSmoke.script'],cwd=game,stdout=f,stderr=f)
  try:
   while time.monotonic()-start<150:
    text=log.read_text(errors='replace')
    if app.poll() is not None:raise RuntimeError('x86 exited '+str(app.returncode)+'\n'+text[-2000:])
    if 'Script>>REM SU30_TEST3_WINDOWS32_COMPLETE' in text:break
    time.sleep(1)
   else:raise RuntimeError('x86 timed out\n'+text[-2000:])
   ps='Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; $b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds; $i=New-Object System.Drawing.Bitmap($b.Width,$b.Height); $g=[System.Drawing.Graphics]::FromImage($i); $g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size); $i.Save("'+str(evidence/'windows-x86.png')+'"); $g.Dispose(); $i.Dispose()'
   subprocess.run(['powershell','-NoProfile','-Command',ps],check=True)
   status['windows_x86']={'passed':True,'platform':'native Windows runner','architecture':'PE32 i386','scope':'Su30SM flight loaded, two native gear commands, cockpit view after zoomed quick start, process alive','elapsed_seconds':round(time.monotonic()-start,1)}
   (evidence/'result.json').write_text(json.dumps(status['windows_x86'],indent=2))
  finally:
   app.terminate()
   try:app.wait(timeout=10)
   except subprocess.TimeoutExpired:app.kill()
 # Add actual Windows evidence to the delivered HTML report archive.
 report=t/'YSFlight_Su30SM_Test_3_Report.zip'
 with zipfile.ZipFile(report,'a',zipfile.ZIP_DEFLATED) as z:
  for p in evidence.iterdir():z.write(p,'su30sm-test-3/windows-evidence/'+p.name)
 gh('release','upload',tag,str(report),'--repo',repo,'--clobber')
 entry=next(x for x in status['assets'] if x['name']==report.name);entry['bytes']=report.stat().st_size;entry['sha256']=hashlib.sha256(report.read_bytes()).hexdigest();entry['download_verified']=False
 verify=t/'verify';verify.mkdir();gh('release','download',tag,'--repo',repo,'--pattern',report.name,'--dir',str(verify));assert hashlib.sha256((verify/report.name).read_bytes()).hexdigest()==entry['sha256'];entry['download_verified']=True
 (t/'STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2));gh('release','upload',tag,str(t/'STATUS.json'),'--repo',repo,'--clobber');shutil.copy2(t/'STATUS.json',evidence/'STATUS.json')
