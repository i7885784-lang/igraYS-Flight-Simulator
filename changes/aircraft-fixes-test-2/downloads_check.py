from pathlib import Path
import urllib.request,hashlib,json,zipfile,io,subprocess,concurrent.futures
repo=Path('/workspace/igraYS-Flight-Simulator');lab=Path(__file__).resolve().parent;commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip();base='https://raw.githubusercontent.com/i7885784-lang/igraYS-Flight-Simulator/ysflight-center-download/'
paths=['reports/aircraft-fixes-test-2/REPORT.md','downloads/YSFlight_Aircraft_Fixes_Test_2_32bit.zip','downloads/YSFlight_Aircraft_Fixes_Test_2_Sources.zip']
paths += ['reports/aircraft-fixes-test-2/'+p for p in ['su27/gear.mp4','mig29/gear.mp4','su27/brake.mp4','su57/canopy.mp4','su27/gear-140.png','mig29/gear-140.png','su27/brake-040.png','su27/tip-rail.png','mig29/intake.png','su57/cockpit-front.png','su57/pylons.png']]
def get(path):
 with urllib.request.urlopen(base+path,timeout=60) as r:status=r.status;b=r.read()
 assert status==200 and b==(repo/path).read_bytes(),path
 if path.endswith('.zip'):
  with zipfile.ZipFile(io.BytesIO(b)) as z:assert z.testzip() is None
 return {'url':base+path,'HTTP':status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'identical':True,'ZIP_CRC':True if path.endswith('.zip') else None}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:results=list(ex.map(get,paths))
(lab/'download-checks.json').write_text(json.dumps({'passed':True,'verified_publication_commit':commit,'downloads':results},indent=2));print('PASS: 14 downloads HTTP200 and byte-identical; ZIP CRCs passed')
