"""Recreate the complete patched engine code and exact accepted aircraft model."""
from pathlib import Path
import sys,json,hashlib,zipfile,io,subprocess,urllib.request,shutil,struct
ROOT=Path(__file__).resolve().parents[2];STAGE=Path(__file__).resolve().parent
META=json.loads((ROOT/'dist/su30sm-nozzle-vector/metadata.json').read_text());SHA=lambda b:hashlib.sha256(b).hexdigest()
def old_game(bits,dest):
 e=META['previous_archives'][str(bits)];p=dest/e['file'];dest.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  url='https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/su30sm-cockpit-fit-20261114/'+p.name
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=120) as r,p.open('wb') as f:shutil.copyfileobj(r,f)
 assert SHA(p.read_bytes())==e['sha256'];return p

def source(work):
 parts=[]
 for e in META['engine_source_parts']:
  b=(ROOT/'dist/su30sm-nozzle-vector'/e['file']).read_bytes();assert SHA(b)==e['sha256'];parts.append(b)
 b=b''.join(parts);assert SHA(b)==META['engine_source_sha256']
 with zipfile.ZipFile(io.BytesIO(b)) as z:assert z.testzip() is None;z.extractall(work)
 engine=work/'engine';subprocess.run([sys.executable,str(STAGE/'patch_engine.py'),str(engine)],check=True);return engine

def models(prior,work):
 baseline=work/'baseline';baseline.mkdir(parents=True,exist_ok=True);out=work/'generated';out.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(prior) as z:
  for name in ['su30sm.dnm','su30smcockpit.dnm']:(baseline/name).write_bytes(z.read('runtime/aircraft/'+name))
 assert SHA((baseline/'su30sm.dnm').read_bytes())==META['baseline_model_sha256'];assert SHA((baseline/'su30smcockpit.dnm').read_bytes())==META['cockpit_sha256']
 subprocess.run([sys.executable,str(STAGE/'model.py'),'--baseline',str(baseline/'su30sm.dnm'),'--output',str(out/'su30sm.dnm')],check=True)
 assert SHA((out/'su30sm.dnm').read_bytes())==META['model_sha256'];shutil.copyfile(baseline/'su30smcockpit.dnm',out/'su30smcockpit.dnm');return out

def pe(data,bits):
 off=struct.unpack_from('<I',data,0x3c)[0];assert data[off:off+4]==b'PE\0\0';machine=struct.unpack_from('<H',data,off+4)[0];magic=struct.unpack_from('<H',data,off+24)[0];assert (machine,magic)==((0x14c,0x10b) if bits==32 else (0x8664,0x20b));return dict(machine=hex(machine),optional_header=hex(magic))
if __name__=='__main__':
 bits=int(sys.argv[1]);work=ROOT/'work/vector-build';work.mkdir(parents=True,exist_ok=True);engine=source(work);prior=old_game(bits,ROOT/'work/previous');generated=models(prior,work)
 subprocess.run(['g++','-std=c++11','-O2',str(STAGE/'test_nozzles.cpp'),'-o',str(work/'test_nozzles')],check=True);subprocess.run([str(work/'test_nozzles')],check=True)
 build=work/f'build{bits}';subprocess.run(['bash',str(STAGE/'build.sh'),str(engine),str(bits),str(build)],check=True)
 dest=ROOT/'work/built';dest.mkdir(parents=True,exist_ok=True);exe=build/f'main/ysflight{bits}_gl1.exe';data=exe.read_bytes();arch=pe(data,bits);shutil.copyfile(exe,dest/exe.name);shutil.copyfile(generated/'su30sm.dnm',dest/'su30sm.dnm');shutil.copyfile(generated/'su30sm.audit.json',dest/'model-audit.json')
 paths=['YSFLIGHT/src/vehicle/fsairplaneproperty.cpp','YSFLIGHT/src/vehicle/fsairplaneproperty.h','YSFLIGHT/src/vehicle/su30_nozzles.h','YSFLIGHT/src/ui/fsrunloop.cpp','public/src/ysgebl/src/shellrender/ysvisual.cpp']
 info=dict(bits=bits,exe_sha256=SHA(data),model_sha256=META['model_sha256'],engine_source_sha256=META['engine_source_sha256'],source_files={p:SHA((engine/p).read_bytes()) for p in paths},compiler=subprocess.check_output(['x86_64-w64-mingw32-g++-posix' if bits==64 else 'i686-w64-mingw32-g++-posix','--version'],text=True).splitlines()[0],**arch)
 (dest/'build-info.json').write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))
