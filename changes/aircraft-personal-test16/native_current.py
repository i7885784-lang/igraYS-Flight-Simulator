import os,sys,json,subprocess
from pathlib import Path
r=Path(__file__).resolve().parent
for k,ident in [('su57','SU-57_FELON'),('mig29','MIG-29_FULCRUM')]:
 if k=='su57':caps=[('doors-open',150,-55,68,'0 -.3 -1.5','1 0 0 0 0 0'),('doors-half',150,-55,68,'0 -.3 -1.5','.5 0 0 0 0 0'),('doors-closed',150,-55,68,'0 -.3 -1.5','0 0 0 0 0 0')]
 else:caps=[(f'closed-{h}-{pitch}',h,pitch,32,f'{sign*1.45} .1 -1.3','0 0 0 0 0 0') for h,pitch,sign in [(75,0,1),(105,-35,1),(255,0,-1),(285,-35,-1),(90,-80,1)]]+[(f'open-{h}',h,0,32,f'{sign*1.45} .1 -1.3','1 0 0 0 0 0') for h,sign in [(75,1),(255,-1)]]
 subprocess.run([sys.executable,str(r/'capture.py'),'inspect'],env={**os.environ,'AIRCRAFT_CHECK':ident,'CHECK_NAME':k+'-flight-review','DIAGNOSTIC':'0','CAPS':json.dumps(caps)},check=True)
