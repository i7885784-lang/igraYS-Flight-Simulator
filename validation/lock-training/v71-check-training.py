from pathlib import Path
import subprocess,importlib.machinery,time,re,json
r=Path('/workspace/ysflight-work');u=importlib.machinery.SourceFileLoader('u',str(r/'v4-gui-action.py')).load_module()
try:u.command('search','--name','YS FLIGHT','windowfocus','--sync');u.key('alt+F4')
except subprocess.CalledProcessError:pass
subprocess.run(['python',str(r/'v7-launch.py'),'v71-training-script.txt'],check=True)
p=r/'v7-v71-training-script.txt.log'
def rows():
 return [{k:float(v) for k,v in re.findall(r'(\w+)=(-?[\d.]+)',x)} for x in p.read_text(errors='replace').splitlines() if x.startswith('V7REPORT ')]
def wait(n):
 deadline=time.monotonic()+30
 while time.monotonic()<deadline:
  data=rows()
  if len(data)>=n:return data
  time.sleep(.05)
 raise AssertionError(('timeout',n,rows()))
def press():
 u.command('keydown','space');time.sleep(.25);u.command('keyup','space')
a=wait(1);u.command('search','--name','YS FLIGHT','windowfocus','--sync');u.click(500,400);press();u.screenshot('v71-acquiring.png')
a=wait(3);assert a[0]['ready']==0 and a[1]['ready']==0 and a[1]['aim9']==2,a
assert a[2]['ready']==1 and a[2]['aim9']==2 and a[2]['lock']==3,a
u.screenshot('v71-locked.png');press()
a=wait(5);assert a[3]['aim9']==1 and a[4]['aim9']==1,a
u.key('Pause');u.screenshot('v71-fired.png')
(r/'v71-training-check.json').write_text(json.dumps(dict(passed=True,normal_space_key=True,no_script_button_injection=True,initial_missile_preselected=True,reports=a),indent=2))
print('PASS normal Space key blocked before acquisition, fires AIM-9 after 3 s, native scenario selected missile without pressing 2.',flush=True)
