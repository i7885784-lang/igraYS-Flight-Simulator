"""Build a personal Su-34 test; upload ONLY to an access-controlled draft release."""
from pathlib import Path
import os,sys,json,hashlib,tempfile,subprocess,zipfile,urllib.request,urllib.error,urllib.parse
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];OWNER='i7885784-lang/igraYS-Flight-Simulator';TOKEN=os.environ['GH_TOKEN'];RUN=os.environ['GITHUB_RUN_ID']
class SafeRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  result=super().redirect_request(req,fp,code,msg,headers,newurl)
  if result is not None and urllib.parse.urlparse(req.full_url).hostname!=urllib.parse.urlparse(newurl).hostname:
   result.remove_header('Authorization')
  return result
opener=urllib.request.build_opener(SafeRedirect())
def request(url,data=None,auth=True,accept='application/vnd.github+json',content_type=None,method=None):
 headers={'Accept':accept,'User-Agent':'YSFlight-personal-test-builder','X-GitHub-Api-Version':'2022-11-28'}
 if auth:headers['Authorization']='Bearer '+TOKEN
 if content_type:headers['Content-Type']=content_type
 return opener.open(urllib.request.Request(url,data=data,headers=headers,method=method),timeout=180)
def sha(data):return hashlib.sha256(data).hexdigest()
def geometry_digest(path):
 h=hashlib.sha256()
 for line in path.read_text().splitlines():
  if line.startswith('N ') or line.startswith('PCK '):continue
  bits=line.split()
  if bits and bits[0]=='V':line='V '+' '.join(f'{float(x):.5f}' for x in bits[1:])
  elif bits and bits[0]=='STA':line='STA '+' '.join(f'{float(x):.5f}' for x in bits[1:4])+' '+' '.join(bits[4:])
  h.update((line+'\n').encode())
 return h.hexdigest()
if __name__=='__main__':
 provenance=json.loads((HERE/'provenance.json').read_text());expected=json.loads((HERE/'expected-build.json').read_text());upstream=HERE/'upstream';upstream.mkdir(exist_ok=True)
 for name in ['su34.yft','su34_hi.yft']:
  rel='Plane-Pack/stream/'+name;record=next(f for f in provenance['files'] if f['path']==rel);url='https://raw.githubusercontent.com/DEVBenSon/FiveM-Plane-Pack/'+provenance['commit']+'/'+rel
  with request(url,auth=False,accept='application/octet-stream') as r:data=r.read()
  if sha(data)!=record['sha256']:raise RuntimeError('Pinned source hash mismatch: '+name)
  (upstream/name).write_bytes(data)
 # The YTD texture archive is never downloaded or parsed.
 result=subprocess.run([sys.executable,str(HERE/'model-source/build_model.py')],cwd=HERE,capture_output=True,text=True)
 if result.returncode:raise RuntimeError('Converter failed: '+result.stderr[-1600:])
 generated=HERE/'model-source/runtime/aircraft'
 if geometry_digest(generated/'su34.dnm')!=expected['geometry_digest']:raise RuntimeError('Converted geometry/states differ from the locally tested build; refusing upload')
 for name,digest in expected['other_output_sha256'].items():
  if sha((generated/name).read_bytes())!=digest:raise RuntimeError('Output differs from locally tested build: '+name)
 with tempfile.TemporaryDirectory(prefix='ysflight-private-') as tmp:
  tmp=Path(tmp);base=REPO/'downloads/YSFlight_Playtest_4_32bit.zip'
  with zipfile.ZipFile(base) as z:z.extractall(tmp)
  game=tmp/'YSFlight_Playtest_4_32bit';game.rename(tmp/'YSFlight_Playtest_4_Private_Su34_32bit');game=tmp/'YSFlight_Playtest_4_Private_Su34_32bit'
  for f in generated.glob('su34*'):(game/'aircraft'/f.name).write_bytes(f.read_bytes())
  with (game/'aircraft/aircraft.lst').open('a') as f:f.write('\naircraft/su34.dat aircraft/su34.dnm aircraft/su34coll.srf aircraft/su34cockpit.srf aircraft/su34_coarse.dnm\n')
  for name in ['Play_Su34.bat','Start_Su34.script','Su34_Play.yfs']:(game/name).write_bytes((HERE/name).read_bytes())
  (game/'licenses/su34-prototype-NOTICE.txt').write_bytes((HERE/'model-source/NOTICE.txt').read_bytes());(game/'licenses/CODEWALKER_LAYOUT_NOTICE.txt').write_bytes((HERE/'model-source/CODEWALKER_LAYOUT_NOTICE.txt').read_bytes())
  readme=game/'READ_ME_RU.txt';text=readme.read_text(encoding='utf-8');text=text.replace('Су-34 в этой публичной сборке отсутствует.', 'Личная копия: Су-34 включён.');readme.write_text(text+'\nЛичная копия с Су-34: Play_Su34.bat. Не публиковать. Разрешение на распространение/продажу геометрии не подтверждено.\n',encoding='utf-8')
  archive=tmp/'YSFlight_Playtest_4_Private_Su34_32bit.zip'
  with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,6) as z:
   for f in sorted(game.rglob('*')):
    if f.is_file():z.write(f,f.relative_to(tmp))
  sources=tmp/'YSFlight_Playtest_4_Private_Su34_Sources.zip'
  with zipfile.ZipFile(REPO/'downloads/YSFlight_Playtest_4_Sources.zip') as base_sources,zipfile.ZipFile(sources,'w',zipfile.ZIP_DEFLATED,6) as z:
   for n in base_sources.namelist():z.writestr(n,base_sources.read(n))
   for f in HERE.rglob('*'):
    rel=f.relative_to(HERE)
    if f.is_symlink() or not f.is_file() or any(p in ['runtime','__pycache__','.panel-cache'] for p in rel.parts) or f.name in ['envelope-reference.json','model-stats.json']:continue
    z.write(f,'su34-converter/'+rel.as_posix())
  for f in [archive,sources]:
   with zipfile.ZipFile(f) as z:
    if z.testzip() is not None:raise RuntimeError('ZIP CRC failed')
  body={'tag_name':'personal-playtest-4-'+RUN,'target_commitish':os.environ['GITHUB_SHA'],'name':'Личный тест №4: Су-27 + Су-34','draft':True,'prerelease':True,'body':'Личная тестовая копия. НЕ ПУБЛИКОВАТЬ: права на геометрию Су-34 не подтверждены. В составе только геометрия источника; текстуры, звуки и системы GTA не перенесены. Распаковать в новую папку, Play_Su27.bat / Play_Su34.bat. Сведения о проверках и ограничениях — reports/playtest-4 и reports/private-playtest-4. Настоящая Windows 10 x86 не проверялась.'}
  with request('https://api.github.com/repos/'+OWNER+'/releases',json.dumps(body).encode(),content_type='application/json') as r:release=json.load(r)
  if release['draft'] is not True:raise RuntimeError('Release is not a draft')
  try:
   with request(release['url'],auth=False) as r:code=r.status
  except urllib.error.HTTPError as e:code=e.code
  if code!=404:raise RuntimeError('Draft visibility is not private; refusing to upload geometry')
  status={'draft':True,'release_url':release['html_url'],'source_commit':os.environ['GITHUB_SHA'],'geometry_digest':expected['geometry_digest'],'assets':[]}
  for asset in [archive,sources]:
   payload=asset.read_bytes();url='https://uploads.github.com/repos/'+OWNER+'/releases/'+str(release['id'])+'/assets?name='+urllib.parse.quote(asset.name)
   with request(url,payload,content_type='application/zip') as r:uploaded=json.load(r)
   with request(uploaded['url']+'?verify='+RUN,accept='application/octet-stream') as r:downloaded=r.read()
   if sha(downloaded)!=sha(payload):raise RuntimeError('Authenticated download verification failed')
   try:
    with request(uploaded['url'],auth=False) as r:code=r.status
   except urllib.error.HTTPError as e:code=e.code
   try:
    with request(uploaded['browser_download_url'],auth=False,accept='application/octet-stream') as r:browser_code=r.status
   except urllib.error.HTTPError as e:browser_code=e.code
   if code!=404 or browser_code!=404:
    with request(uploaded['url'],method='DELETE') as r:pass
    raise RuntimeError('Asset was withdrawn because privacy could not be confirmed')
   status['assets'].append({'name':asset.name,'url':uploaded['browser_download_url'],'bytes':len(payload),'sha256':sha(payload),'authenticated_download_verified':True,'unauthenticated_http_status':code,'unauthenticated_browser_download_status':browser_code})
  output=REPO/'reports/private-playtest-4/STATUS.json';output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n');print('Private draft created and authenticated downloads verified; status file written.')
