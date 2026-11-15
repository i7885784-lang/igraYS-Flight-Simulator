from pathlib import Path
import sys,subprocess,json,hashlib,shutil,zipfile,urllib.request,struct
ROOT=Path(__file__).resolve().parents[2];STAGE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'changes/su30sm-nozzle-vector'));from prepare import source,pe,SHA
OLD={32:('x86','4a30f79a697f558979e3f1b1f8d23ede083c0c0769ff79e54d58bd10912637a4'),64:('x64','62f5d07fe623880dbb89862bec7e77e00643efd13bcca0b100b361ff03d69d52')}
MODEL='e869eb09b071299f570fe840e24cd964c925cd74d2ad68ecaf1fea6818f6ab55';COCKPIT='564308f1149862461dbc254dfb4372475a067ed0182eb61faf9d7345fa1807b9'
FILES=['YSFLIGHT/src/vehicle/fsairplaneproperty.cpp','YSFLIGHT/src/vehicle/fsairplaneproperty.h','YSFLIGHT/src/vehicle/su30_nozzles.h','YSFLIGHT/src/vehicle/su30_high_alpha.h','YSFLIGHT/src/core/fssimulation.cpp','YSFLIGHT/src/ui/fsrunloop.cpp','public/src/ysgebl/src/shellrender/ysvisual.cpp']
def baseline(bits):
 arch,sha=OLD[bits];dest=ROOT/'work/previous'/f'Su30SM_VectorNozzles_Windows_{arch}.zip';dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists():
  url='https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/su30sm-nozzle-vectoring-20261115/'+dest.name
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=120) as r,dest.open('wb') as f:shutil.copyfileobj(r,f)
 assert SHA(dest.read_bytes())==sha;return dest
if __name__=='__main__':
 bits=int(sys.argv[1]);work=ROOT/'work/high-alpha-build';work.mkdir(parents=True,exist_ok=True);engine=source(work);subprocess.run([sys.executable,str(STAGE/'patch.py'),str(engine)],check=True)
 subprocess.run(['g++','-std=c++11','-O2',str(STAGE/'test.cpp'),'-o',str(work/'test')],check=True);subprocess.run([str(work/'test')],check=True)
 build=work/f'build{bits}';subprocess.run(['bash',str(ROOT/'changes/su30sm-nozzle-vector/build.sh'),str(engine),str(bits),str(build)],check=True)
 dest=ROOT/'work/built';dest.mkdir(parents=True,exist_ok=True);exe=build/f'main/ysflight{bits}_gl1.exe';b=exe.read_bytes();arch=pe(b,bits);shutil.copyfile(exe,dest/exe.name)
 with zipfile.ZipFile(baseline(bits)) as z:
  main=z.read('runtime/aircraft/su30sm.dnm');assert SHA(main)==MODEL;assert SHA(z.read('runtime/aircraft/su30smcockpit.dnm'))==COCKPIT;(dest/'su30sm.dnm').write_bytes(main)
 info=dict(bits=bits,exe_sha256=SHA(b),model_sha256=MODEL,cockpit_sha256=COCKPIT,source_files={p:SHA((engine/p).read_bytes()) for p in FILES},**arch);(dest/'build-info.json').write_text(json.dumps(info,indent=2));print(json.dumps(info))
