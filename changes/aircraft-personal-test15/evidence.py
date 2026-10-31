from pathlib import Path
import os,sys,json,subprocess
r=Path(__file__).resolve().parent
# Re-use exact pre-fix close-camera definitions. Keep new videos compact.
for kind,ident in [('mig29','MIG-29_FULCRUM'),('su47','SU-47_BERKUT')]:
 if kind=='mig29':
  subprocess.run([sys.executable,str(r/'check_wheel_view.py'),'final'],env=os.environ,check=True)
  subprocess.run([sys.executable,str(r/'capture.py'),'gear'],env={**os.environ,'AIRCRAFT_CHECK':ident,'CHECK_NAME':'mig29-native-final-gear'},check=True)
 caps=[]
 aim='1.45 .10 -1.3' if kind=='mig29' else '1.35 -.25 1.7'
 for g in ([0,1] if kind=='mig29' else [1]):
  for h in [75,105,255,285]:
   a=aim.split();a[0]=str(float(a[0])*(-1 if h>180 else 1));caps.append((f'close-{g}-{h}',h,0,32,' '.join(a),f'{g} 0 0 0 0 0'))
 if kind=='su47':
  for f in [0,.25,1]:caps.append((f'hinge-{f}-140',140,35,42,'4.5 -.1 -4.8',f'0 0 {f} 0 0 0'))
 subprocess.run([sys.executable,str(r/'capture.py'),'ground'],env={**os.environ,'AIRCRAFT_CHECK':ident,'CHECK_NAME':kind+'-close-final','DIAGNOSTIC':'1','CAPS':json.dumps(caps)},check=True)
for label in ['before','final']:
 for kind,ident in [('su27','SU-27_FLANKER'),('su34','SU-34_FULLBACK'),('mig29','MIG-29_FULCRUM'),('su47','SU-47_BERKUT')]:
  caps=[('overview',135,9,100,'0 0 -1','1 0 0 0 0 0')];env={**os.environ,'AIRCRAFT_CHECK':ident,'CHECK_NAME':kind+'-normal-'+label,'DIAGNOSTIC':'0','CAPS':json.dumps(caps)}
  if label=='before':env['GAME_RUNTIME']='/workspace/ysflight-dev/aircraft-test-14/runtime'
  subprocess.run([sys.executable,str(r/'capture.py'),'ground'],env=env,check=True)
