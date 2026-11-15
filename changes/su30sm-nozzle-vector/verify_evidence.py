"""Verify distinct real-input recordings, without rerunning identical flights."""
from pathlib import Path
import json,sys,hashlib
root=Path(__file__).resolve().parents[2];base=root/'work/lab/checks';out=root/'reports/su30sm-nozzle-vector';out.mkdir(exist_ok=True)
meta=json.loads((root/'dist/su30sm-nozzle-vector/metadata.json').read_text());result={}
for case in ['controls','engine']:
 p=base/('su30sm-nozzle-vector-final-'+case);d=json.loads((p/'results.json').read_text());assert d['passed'] and d['model_sha256']==meta['model_sha256'];ss=d['states'];row=dict(model_sha256=d['model_sha256'],sample_count=len(ss))
 for key in ['nozzle','tvLdeg','tvRdeg','speed']:
  vals=[float(s[key]) for s in ss];row[key]=[min(vals),max(vals)]
 assert max(abs(float(s[k])) for s in ss for k in ['tvLdeg','tvRdeg'])<=15.001
 if case=='controls':
  axes={}
  for axis in ['elevator','aileron','rudder']:
   checks=[]
   for sign in [-1,1]:
    candidates=[s for s in ss if float(s[axis])*sign>.4]
    assert candidates,(axis,sign)
    s=max(candidates,key=lambda s:abs(float(s[axis])))
    left,right=map(float,[s['tvLdeg'],s['tvRdeg']])
    if axis=='elevator':assert left*sign>0 and right*sign>0 and abs(left-right)<.01
    elif axis=='aileron':assert (left-right)*sign<0
    else:assert (left-right)*sign>0
    checks.append({k:s[k] for k in ['t',axis,'tvLdeg','tvRdeg']})
   axes[axis]=checks
  row['both_polarities_of_all_three_actual_controls']=axes
 else:
  assert row['nozzle'][0]<.07 and row['nozzle'][1]>.99
  ab=[s for s in ss if s['ab']=='1'];assert ab and all(float(s['nozzle'])>=.69 for s in ab)
  row['reheat_minimum_opening']=min(float(s['nozzle']) for s in ab)
  assert any(float(s['throttle'])<.01 for s in ss)
  assert any(float(s['throttle'])>.99 and s['ab']=='0' and float(s['nozzle'])<.1 for s in ss)
 row['video_sha256']=hashlib.sha256((p/(case+'.mp4')).read_bytes()).hexdigest();result[case]=row
result['scope']='Windows x64 EXE under Wine; actual XTest keyboard, no forced NOZZLEPOSE in these recordings. Native Windows results supplied separately. Control signs verified at observed inputs; exact factory schedules not inferred.'
(out/'local-evidence.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
