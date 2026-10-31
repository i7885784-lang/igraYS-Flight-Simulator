from pathlib import Path
import subprocess,sys,json,os,shutil
r=Path(__file__).resolve().parent
for k in ['su27','su34']:
 (r/'baseline-runtime/aircraft').mkdir(parents=True,exist_ok=True);shutil.copy2(r/'baseline'/f'{k}.dnm',r/'baseline-runtime/aircraft'/f'{k}.dnm')
def run(script,extra={}):subprocess.run([sys.executable,str(r/script)],env={**os.environ,**extra},check=True)
for script in ['check_controls.py','check_preservation.py','audit_su34.py','audit_mig.py','check_return_lips.py','check_su_seams.py']:run(script)
for f in ['control-checks.json','preservation-checks.json','motion-audit.json','mig-motion-audit.json','return-lip-collision-checks.json']:assert json.loads((r/f).read_text())['passed'],f
run('check_su_seams.py',{'SEAM_RUNTIME':str(r/'baseline-runtime'),'SEAM_OUTPUT':'baseline-su-seam-collision-checks.json'})
a=json.loads((r/'baseline-su-seam-collision-checks.json').read_text());b=json.loads((r/'su-seam-collision-checks.json').read_text());key=lambda h:(h['g'],h['moving'],h['fixed']);assert b['su27']['passed'];assert {key(h) for h in b['su34']['hits']}<={key(h) for h in a['su34']['hits']};assert all(h['g']<=.0675 for h in b['su34']['hits']);(r/'seam-regression-checks.json').write_text(json.dumps({'passed':True,'su27_unintended_hits':0,'su34_closed_seam_contacts_before':len(a['su34']['hits']),'su34_closed_seam_contacts_after':len(b['su34']['hits']),'new_contact_events':0},indent=2))
run('check_closed_wheels.py',{'WHEEL_LABEL':'final'})
j=json.loads((r/'mig29-final-closed-wheel-check.json').read_text());assert all(v['visible_samples']==0 for v in j.values()),[(k,v['visible_samples']) for k,v in j.items() if v['visible_samples']]
print('ALL CHECKS PASSED')
