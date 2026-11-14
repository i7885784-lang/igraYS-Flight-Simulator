"""Apply the single frozen interior SRF identically to exterior and cockpit DNM."""
from pathlib import Path
import sys,json,zipfile,tempfile,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin/model-source'));import dnm
SHA=lambda b:hashlib.sha256(b).hexdigest()
def patch_bytes(data,before,after,srf):
 assert SHA(data)==before
 with tempfile.TemporaryDirectory() as t:
  f=Path(t)/'model.dnm';f.write_bytes(data);p,ns=dnm.read(f);old={k:list(v) for k,v in p.items()};p['Su30Interior.srf']=srf;assert [k for k in p if p[k]!=old[k]]==['Su30Interior.srf'];dnm.write(f,p,ns);result=f.read_bytes().replace(b'\r\n',b'\n')
 assert SHA(result)==after,(SHA(result),after);return result

def load_patch():
 folder=ROOT/'dist/su30sm-cockpit-fit';meta=json.loads((folder/'metadata.json').read_text())
 with zipfile.ZipFile(folder/'Su30Interior.srf.zip') as z:srf=z.read('Su30Interior.srf')
 assert SHA(srf)==meta['interior_sha256'];return meta,srf.decode().splitlines()

def models_from_zip(z):
 meta,srf=load_patch();return {name:patch_bytes(z.read('runtime/aircraft/'+name),entry['baseline_sha256'],entry['sha256'],srf) for name,entry in meta['models'].items()}
