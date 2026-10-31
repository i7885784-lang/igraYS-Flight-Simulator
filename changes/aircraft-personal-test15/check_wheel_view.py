from pathlib import Path
import os,sys,json,subprocess
r=Path(__file__).resolve().parent
caps=[(f'wheel-{h}',h,-46,36,('1.04 .23 -.7' if h<180 else '-1.04 .23 -.7'),'0 0 0 0 0 0') for h in [90,135,225,270]]
env={**os.environ,'AIRCRAFT_CHECK':'MIG-29_FULCRUM','CAPS':json.dumps(caps),'CHECK_NAME':'mig29-wheel-'+sys.argv[1],'DIAGNOSTIC':'1'}
if sys.argv[1]=='before':env['GAME_RUNTIME']='/workspace/ysflight-dev/aircraft-test-14/runtime'
subprocess.run([sys.executable,str(r/'capture.py'),'inspect'],env=env,check=True)
