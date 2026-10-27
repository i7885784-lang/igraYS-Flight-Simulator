from pathlib import Path
import urllib.request,hashlib,json,zipfile,io,subprocess,concurrent.futures
repo=Path('/workspace/igraYS-Flight-Simulator');lab=Path(__file__).resolve().parent;commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip();base='https://raw.githubusercontent.com/i7885784-lang/igraYS-Flight-Simulator/ysflight-center-download/'
paths=['reports/fighters-fg-test-1/REPORT.md','reports/fighters-fg-test-1/INSPECTION.md','downloads/YSFlight_Fighters_FG_Test_1_32bit.zip','downloads/YSFlight_Fighters_FG_Test_1_Sources.zip']
for k in ['su27','mig29']:
 paths += [f'reports/fighters-fg-test-1/{k}/{fn}' for fn in ['front.png','top.png','side.png','orbit-135.png','gear.mp4','canopy.mp4','controls.mp4','brake.mp4','engine.mp4']]
def check(path):
 url=base+path
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'YSFlight-artifact-verification'}),timeout=90) as r:code=r.status;data=r.read()
 assert code==200 and data==(repo/path).read_bytes(),path
 crc=None
 if path.endswith('.zip'):
  with zipfile.ZipFile(io.BytesIO(data)) as z:assert z.testzip() is None;crc=True
 return {'path':path,'url':url,'HTTP':code,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'byte_identical':True,'ZIP_CRC':crc}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:results=list(ex.map(check,paths))
report={'passed':True,'verified_publication_commit':commit,'downloads':results}
(lab/'download-checks.json').write_text(json.dumps(report,indent=2));print('Verified',len(results),'published downloads: HTTP 200, identical bytes, both ZIP CRCs')
