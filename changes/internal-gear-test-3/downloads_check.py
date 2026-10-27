from pathlib import Path
import urllib.request,hashlib,json,zipfile,io,subprocess,concurrent.futures
repo=Path('/workspace/igraYS-Flight-Simulator');lab=Path(__file__).resolve().parent;commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip();base='https://raw.githubusercontent.com/i7885784-lang/igraYS-Flight-Simulator/ysflight-center-download/'
paths=['reports/internal-gear-test-3/REPORT.md','downloads/YSFlight_Internal_Gear_Test_3_32bit.zip','downloads/YSFlight_Internal_Gear_Test_3_Sources.zip','reports/internal-gear-test-3/su27-final-cycle/gear.mp4','reports/internal-gear-test-3/mig29-internal-cycle/gear.mp4','reports/internal-gear-test-3/su27-final-overview/bottom.png','reports/internal-gear-test-3/mig29-final-overview/bottom.png']
def get(path):
 with urllib.request.urlopen(base+path,timeout=60) as r:status=r.status;b=r.read()
 assert status==200 and b==(repo/path).read_bytes(),path
 if path.endswith('.zip'):
  with zipfile.ZipFile(io.BytesIO(b)) as z:assert z.testzip() is None
 return {'url':base+path,'HTTP':status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'identical':True,'ZIP_CRC':True if path.endswith('.zip') else None}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:results=list(ex.map(get,paths))
(lab/'download-checks.json').write_text(json.dumps({'passed':True,'verified_publication_commit':commit,'downloads':results},indent=2));print('PASS: 7 downloads HTTP200 and byte-identical; ZIP CRCs passed')
