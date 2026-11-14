"""Apply the frozen five-pack patch, guarded by baseline/result hashes."""
from pathlib import Path
import sys,json,zipfile,tempfile,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin/model-source'));import dnm
SHA=lambda b:hashlib.sha256(b).hexdigest()
def split(ls):
 first=ls.index('F');i=first;faces=[]
 while i<len(ls) and ls[i]=='F':
  end=ls.index('E',i)+1;faces.append(ls[i:end]);i=end
 return ls[:first],faces,ls[i:]
def apply_delta(old,delta):
 assert SHA(('\n'.join(old)+'\n').encode())==delta['before_sha256'];prefix,faces,end=split(old);repl={int(k):v for k,v in delta['replacements'].items()};out=prefix+delta['append_vertices']+[s for i,block in enumerate(faces) for b in repl.get(i,[block]) for s in b]+end
 assert SHA(('\n'.join(out)+'\n').encode())==delta['after_sha256'];return out
def patch_bytes(data):
 folder=ROOT/'dist/su30sm-recessed-bay';meta=json.loads((folder/'metadata.json').read_text());assert SHA(data)==meta['baseline_sha256']
 with tempfile.TemporaryDirectory() as t:
  path=Path(t)/'model.dnm';path.write_bytes(data);p,ns=dnm.read(path);old={k:list(v) for k,v in p.items()}
  for e in meta['patches']:
   with zipfile.ZipFile(folder/e['zip']) as z:payload=z.read(e['member'])
   assert SHA(payload)==e.get('payload_sha256',e['sha256']);p[e['pack']]=apply_delta(p[e['pack']],json.loads(payload)) if e['type']=='face-delta' else payload.decode().splitlines()
  assert set(k for k in p if p[k]!=old[k])=={e['pack'] for e in meta['patches']};dnm.write(path,p,ns);result=path.read_bytes().replace(b'\r\n',b'\n')
 assert SHA(result)==meta['model_sha256'];return result
