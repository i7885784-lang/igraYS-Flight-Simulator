"""Split the verified personal bundle without publishing the private release."""
from pathlib import Path
import subprocess,json,zipfile,hashlib,tempfile
repo='i7885784-lang/igraYS-Flight-Simulator';release='personal-fighters-test10-20261030'
def gh(*args):return subprocess.check_output(['gh',*args])
meta=json.loads(gh('api',f'repos/{repo}/releases/428680624'));assert meta['draft'] is True
with tempfile.TemporaryDirectory() as td:
 p=Path(td);gh('release','download',release,'--repo',repo,'--pattern','YSFlight_Test_10_All_In_One.zip','--dir',str(p));src=p/'YSFlight_Test_10_All_In_One.zip';assert hashlib.sha256(src.read_bytes()).hexdigest()=='aa901aaf4fb159ce5b0c2a0babf8a3e21156489218ad952d28327339c12cf4a4'
 results=[]
 with zipfile.ZipFile(src) as old:
  assert old.testzip() is None
  for name,game in [('YSFlight_Test_10_Game_32bit.zip',True),('YSFlight_Test_10_Report_Photos_Video.zip',False)]:
   dest=p/name
   with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
    for n in old.namelist():
     rel=n.removeprefix('YSFlight_Test_10/')
     if n.endswith('/'):continue
     if game and rel.startswith('Game/'):out.writestr('YSFlight_Test_10_Game/'+rel[5:],old.read(n))
     elif not game and not rel.startswith('Game/') and rel not in ['Play.bat','README_RU.txt','SOURCE_DOWNLOADS.txt']:out.writestr('YSFlight_Test_10_Report/'+rel,old.read(n))
    if not game:out.writestr('YSFlight_Test_10_Report/README_RU.txt','Отчёт без игры. Откройте REPORT.pdf; фотографии в Photos, видео в Video.\n'.encode('utf-8-sig'))
   with zipfile.ZipFile(dest) as z:assert z.testzip() is None
   gh('release','upload',release,str(dest),'--repo',repo)
   verify=p/'verify';verify.mkdir(exist_ok=True);gh('release','download',release,'--repo',repo,'--pattern',name,'--dir',str(verify))
   digest=hashlib.sha256(dest.read_bytes()).hexdigest();assert hashlib.sha256((verify/name).read_bytes()).hexdigest()==digest
   results.append({'name':name,'bytes':dest.stat().st_size,'sha256':digest,'download_verified':True,'url':meta['html_url'].replace('/tag/','/download/')+'/'+name})
 assert json.loads(gh('api',f'repos/{repo}/releases/428680624'))['draft'] is True
 Path('reports/personal-playtest-10/SPLIT_DOWNLOADS.json').write_text(json.dumps({'draft':True,'assets':results},indent=2)+'\n')
 print('PASS both separate archives uploaded and downloaded with matching hashes')
