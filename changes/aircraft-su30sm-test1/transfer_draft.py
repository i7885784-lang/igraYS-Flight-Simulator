"""Transfer through an authenticated draft, never through public Git objects."""
from pathlib import Path
import os,json,hashlib,subprocess,zipfile,tempfile,urllib.request,urllib.error,time,base64,shutil,sys
repo='i7885784-lang/igraYS-Flight-Simulator';tag='personal-su30sm-test1-20261103';rid=432469264
api=f'https://api.github.com/repos/{repo}/releases/{rid}'
headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','User-Agent':'su30sm-transfer','Content-Type':'application/json'}
args=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())['inputs'];total=int(args['bundle_chunks']);assert 0<total<600
ack_info=None;reuse=args.get('reuse_bundle') in ['true',True]
def graphql(query,variables):
 req=urllib.request.Request('https://api.github.com/graphql',data=json.dumps({'query':query,'variables':variables}).encode(),headers=headers,method='POST')
 with urllib.request.urlopen(req,timeout=45) as res:d=json.load(res)
 assert 'errors' not in d,d.get('errors')
 return d['data']
def request(method='GET',body=None,etag=None):
 if isinstance(body,dict) and body.get('phase')=='ack':
  graphql('mutation($id:ID!,$oid:GitObjectID!){updateRef(input:{refId:$id,oid:$oid,force:true}){ref{id}}}',{'id':ack_info['ref_id'],'oid':ack_info['oids'][body['i']%2]})
  return body,None
 h=dict(headers)
 if etag:h['If-None-Match']=etag
 data=None if body is None else json.dumps({'tag_name':tag,'draft':True,'body':json.dumps(body) if isinstance(body,dict) else body}).encode()
 try:
  with urllib.request.urlopen(urllib.request.Request(api,data=data,headers=h,method=method),timeout=45) as res:return json.load(res),res.headers.get('ETag')
 except urllib.error.HTTPError as e:
  if e.code==304:return None,etag
  raise
def gh(*a):return subprocess.check_output(['gh',*a])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
release,_=request();assert release['draft']
if not reuse:
 begin=json.loads(release['body'])
 assert begin['transfer']=='su30sm-private-stage-v1' and begin['phase']=='begin' and begin['sha256']==args['bundle_sha256'] and begin['chunks']==total
 ack_info=begin['ack'];request('PATCH',{'phase':'ready'})
with tempfile.TemporaryDirectory() as td:
 t=Path(td);packet=t/'packet.zip';index=0;etag=None;deadline=time.monotonic()+900
 if reuse:gh('release','download',tag,'--repo',repo,'--pattern','packet.zip','--dir',str(t));index=total
 with packet.open('ab' if reuse else 'wb') as f:
  while index<total:
   assert time.monotonic()<deadline,'Transfer timeout'
   cur,etag=request(etag=etag)
   if cur is None:time.sleep(.35);continue
   assert cur['draft'];msg=json.loads(cur['body'])
   if msg.get('phase')!='chunk' or msg.get('i')!=index:time.sleep(.35);continue
   data=base64.b64decode(msg['data'],validate=True);assert hashlib.sha256(data).hexdigest()==msg['sha256'];f.write(data)
   request('PATCH',{'phase':'ack','i':index});index+=1
   if index%25==0 or index==total:print('Private transfer',index,'/',total,flush=True)
 assert sha(packet)==args['bundle_sha256'];time.sleep(2)
 if not reuse:gh('release','upload',tag,str(packet),'--repo',repo,'--clobber')
 request('PATCH','Су-30СМ — личная проверка №1. HappyMexicano7, CC BY 4.0. Материалы получены; сборка и проверка Windows выполняются в Actions. Полная поставка остаётся черновиком.')
 b=t/'bundle'
 with zipfile.ZipFile(packet) as z:assert z.testzip() is None;z.extractall(b)
 meta=json.loads((b/'manifest.json').read_text());assert sha(b/'source/su-30sm.glb')==meta['source_sha256']
 gh('release','download','personal-fighters-test17-20261103','--repo',repo,'--pattern','YSFlight_Test_17_Game_32bit.zip','--pattern','YSFlight_Test_17_Sources.zip','--dir',str(t))
 prior=json.loads(Path('reports/personal-playtest-17/STATUS.json').read_text())
 for item in prior['assets']:
  p=t/item['name']
  if p.exists():assert sha(p)==item['sha256']
 base=t/'base'
 with zipfile.ZipFile(t/'YSFlight_Test_17_Sources.zip') as z:z.extractall(base)
 code=Path('changes/aircraft-su30sm-test1').resolve();work=t/'work';shutil.copytree(code,work,ignore=shutil.ignore_patterns('__pycache__'))
 shutil.copytree(base/'sources/engine',work/'engine');shutil.copytree(code/'engine-overrides',work/'engine',dirs_exist_ok=True)
 for rel,digest in meta['engine_files'].items():assert sha(work/'engine'/rel)==digest,rel
 shutil.copytree(b/'source',work/'source')
 subprocess.run([sys.executable,'-m','pip','install','-r',str(code/'requirements.txt')],check=True)
 for script in ['convert.py','gear.py']:subprocess.run([sys.executable,str(work/'model-source'/script)],check=True)
 for name,digest in meta['expected_models'].items():
  if name=='su30smcoll.srf':digest='b8ea55c09b2b9e8cad25eccc717f4b5fb25838a4f22cd6739decc1b2f13c8dbe'
  assert sha(work/'runtime/aircraft'/name)==digest,'Model reproduction: '+name
 print('All four model files reproduce their tested SHA-256.',flush=True)
 game=t/'YSFlight_Su30SM_Test_1_Game';game.mkdir()
 with zipfile.ZipFile(t/'YSFlight_Test_17_Game_32bit.zip') as z:
  for name in z.namelist():
   if name.endswith('/'):continue
   p=game/name.split('/',1)[1];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
 shutil.copytree(b/'runtime-additions',game,dirs_exist_ok=True);shutil.copytree(work/'runtime/aircraft',game/'aircraft',dirs_exist_ok=True)
 with zipfile.ZipFile(t/'YSFlight_Test_17_Game_32bit.zip') as z:
  for name in z.namelist():
   if not name.endswith('/') and '/aircraft/' in name:assert (game/name.split('/',1)[1]).read_bytes()==z.read(name)
 sources=t/'sources';sw=sources/'su30sm-test1';shutil.copytree(code,sw,ignore=shutil.ignore_patterns('__pycache__','transfer_draft.py','windows_smoke.py'))
 shutil.copytree(work/'engine',sw/'engine');shutil.copytree(b/'source',sw/'source');shutil.copytree(b/'metadata',sw,dirs_exist_ok=True)
 for p in (code/'engine-toolchains').glob('*.cmake'):shutil.copy2(p,sw/'engine'/p.name)
 template=sw/'runtime-template'
 for rel in ['aircraft/su30sm.dat','aircraft/air_su30sm.lst','Su30SM_Play.yfs','Start_Su30SM.script','Play_Su30SM.bat','READ_ME_SU30SM_RU.txt']:
  p=template/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(game/rel,p)
 (sources/'history').mkdir();shutil.copy2(t/'YSFlight_Test_17_Sources.zip',sources/'history/YSFlight_Test_17_Sources.zip')
 (sources/'README_RU.txt').write_text('Текущие полные исходники и GLB: su30sm-test1/. Инструкции: su30sm-test1/README_RU.md. Прежние исходники: history/YSFlight_Test_17_Sources.zip.\n')
 release=json.loads(gh('api',f'repos/{repo}/releases/{rid}'));assert release['draft'];prefix=release['html_url'].replace('/tag/','/download/');assets=[]
 for name,folder in [('YSFlight_Su30SM_Test_1_Game_32bit.zip',game),('YSFlight_Su30SM_Test_1_Sources.zip',sources),('YSFlight_Su30SM_Test_1_Report.zip',None)]:
  output=t/name
  if folder is None:shutil.copy2(b/'report.zip',output)
  else:
   with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,6) as z:
    for p in sorted(folder.rglob('*')):
     if p.is_file() and '__pycache__' not in p.parts:z.write(p,folder.name+'/'+str(p.relative_to(folder)))
  with zipfile.ZipFile(output) as z:assert z.testzip() is None
  digest=sha(output);gh('release','upload',tag,str(output),'--repo',repo,'--clobber');v=t/'verify';v.mkdir(exist_ok=True)
  gh('release','download',tag,'--repo',repo,'--pattern',name,'--dir',str(v),'--clobber');assert sha(v/name)==digest
  assets.append({'name':name,'bytes':output.stat().st_size,'sha256':digest,'url':prefix+'/'+name,'download_verified':True})
 status={'draft':True,'release_url':release['html_url'],'assets':assets,'checks':meta['checks'],'windows_x86':{'passed':False,'status':'pending'}}
 Path('reports/su30sm-test-1/STATUS.json').write_text(json.dumps(status,indent=2));gh('release','upload',tag,'reports/su30sm-test-1/STATUS.json','--repo',repo,'--clobber')
 assert json.loads(gh('api',f'repos/{repo}/releases/{rid}'))['draft'];print('Archive downloads verified by SHA-256 and ZIP CRC.',flush=True)
