"""Publish only the visual report and media; never packages or alters the game."""
from pathlib import Path
import json,hashlib,os,subprocess,tempfile,zipfile
REPO='i7885784-lang/igraYS-Flight-Simulator'
TAG='personal-su30sm-dark-channel-report-20261106'
r=Path('reports/su30sm-dark-channel')
def gh(*args):return subprocess.check_output(['gh',*args])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
release=json.loads(gh('api',f'repos/{REPO}/releases/'+os.environ['RELEASE_ID']))
assert release['draft'] and release['tag_name']==TAG
assert len(json.loads((r/'comparisons.json').read_text()))==42
assert len(list((r/'videos').glob('*.mp4')))==5
assert (r/'Su30SM_Report_RU.pdf').is_file()
with tempfile.TemporaryDirectory() as td:
 t=Path(td);z=t/'Su30SM_Report_Photos_Videos.zip'
 with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,6) as f:
  for p in sorted(r.rglob('*')):
   if p.is_file():f.write(p,p.relative_to(r))
 with zipfile.ZipFile(z) as f:assert f.testzip() is None
 paths=[z,r/'Su30SM_Report_RU.pdf',*sorted((r/'videos').glob('*.mp4'))]
 for p in paths:gh('release','upload',TAG,str(p),'--repo',REPO)
 verify=t/'verify';verify.mkdir()
 gh('release','download',TAG,'--repo',REPO,'--dir',str(verify))
 for p in paths:assert sha(p)==sha(verify/p.name)
 release=json.loads(gh('api',f'repos/{REPO}/releases/'+os.environ['RELEASE_ID']))
 status={'release_url':release['html_url'],'draft':release['draft'],'source_commit':os.environ['GITHUB_SHA'],'downloaded_and_sha256_verified':True,'game_included':False,'assets':[{'name':p.name,'sha256':sha(p),'url':next(a['browser_download_url'] for a in release['assets'] if a['name']==p.name)} for p in paths]}
 p=t/'DOWNLOADS.json';p.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n');gh('release','upload',TAG,str(p),'--repo',REPO);print(json.dumps(status,indent=2))
