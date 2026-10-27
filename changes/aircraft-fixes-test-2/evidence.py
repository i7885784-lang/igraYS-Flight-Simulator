from pathlib import Path
import json,subprocess
lab=Path(__file__).resolve().parent;results={}
for folder,key,video in [('su27-release-gear','gear','gear'),('mig29-release-gear','gear','gear'),('su27-final-brake','spoiler','brake'),('su57-canopy','canopy','canopy')]:
 p=lab/'checks'/folder;j=json.loads((p/'results.json').read_text());s=j['states'];q=[float(v[key]) for v in s];assert j['passed'] and j['native_XTest_keyboard_events'] and all(v['active']=='1' for v in s)
 assert min(q)<.01 and max(q)>.99 and q[-1]<.01 and any(.05<v<.95 for v in q),(folder,min(q),max(q),q[-1])
 subprocess.run(['ffmpeg','-v','error','-i',str(p/(video+'.mp4')),'-f','null','-'],check=True,stdout=subprocess.DEVNULL)
 results[folder]={'passed':True,'min_max_last':[min(q),max(q),q[-1]],'intermediate_positions':True,'native_keys':j['native_XTest_keyboard_events'],'video_decoded':True}
for folder in ['su27-final-overview','mig29-intake-update','mig29-release-ground','su57-overview','preserved-su47']:assert json.loads((lab/'checks'/folder/'results.json').read_text())['passed']
(lab/'evidence-checks.json').write_text(json.dumps({'passed':True,'final_targeted_checks':results,'runtime':'Win64 diagnostic executable under Wine/Xvfb','common_views':'one final shared overview per revised aircraft; separate Su47 loading check'},indent=2));print('PASS: 4 live cycles, compact general/targeted checks, all videos decoded')
