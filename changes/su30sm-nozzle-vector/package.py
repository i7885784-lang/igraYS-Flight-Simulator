"""Package exact native-tested engines, complete corresponding sources, and rollback."""
from pathlib import Path
import sys,json,zipfile,hashlib,shutil,subprocess
from prepare import ROOT,STAGE,META,SHA,old_game,pe,source
TAG='su30sm-nozzle-vectoring-20261115';REPO='i7885784-lang/igraYS-Flight-Simulator';RUN=43676877534
STAMP=(2026,11,15,0,0,0)
def put(z,name,data):
 i=zipfile.ZipInfo(name,STAMP);i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,data,compresslevel=6)
def build(out):
 out.mkdir(parents=True,exist_ok=True);report=ROOT/'reports/su30sm-nozzle-vector';report.mkdir(exist_ok=True)
 evidence=ROOT/'dist/su30sm-nozzle-vector/evidence.zip';assert SHA(evidence.read_bytes())=='062a2e67be17f5bc11f23ce96772d5daf2d2e1060d48b324d2d3a12ff1d39446'
 with zipfile.ZipFile(evidence) as z:assert z.testzip() is None;z.extractall(report)
 engine=source(ROOT/'work/source-package');records=[];models={};baseline={};exes=[]
 for bits,arch in [(32,'x86'),(64,'x64')]:
  built=ROOT/f'artifacts/build-{bits}';native=ROOT/f'artifacts/native-{bits}';info=json.loads((built/'build-info.json').read_text());check=json.loads((native/'results.json').read_text())
  exe=(built/f'ysflight{bits}_gl1.exe').read_bytes();model=(built/'su30sm.dnm').read_bytes();pe(exe,bits)
  assert info['bits']==bits and info['exe_sha256']==SHA(exe) and SHA(model)==info['model_sha256']==META['model_sha256']
  assert check['passed'] and check['native_windows'] and check['bits']==bits and check['exe_sha256']==SHA(exe) and check['model_sha256']==META['model_sha256'] and check['cockpit_sha256']==META['cockpit_sha256']
  assert all(SHA((engine/p).read_bytes())==s for p,s in info['source_files'].items())
  destreport=report/f'native-{bits}';destreport.mkdir(exist_ok=True)
  for f in native.glob('*.png'):shutil.copyfile(f,destreport/f.name)
  check['actions_run_url']=f'https://github.com/{REPO}/actions/runs/{RUN}';(destreport/'results.json').write_text(json.dumps(check,indent=2));shutil.copyfile(built/'build-info.json',destreport/'build-info.json')
  previous=old_game(bits,ROOT/'work/previous');dest=out/f'Su30SM_VectorNozzles_Windows_{arch}.zip'
  with zipfile.ZipFile(previous) as zi:
   assert zi.testzip() is None
   oldexe=zi.read(f'runtime/ysflight{bits}_gl1.exe');pe(oldexe,bits);oldmodel=zi.read('runtime/aircraft/su30sm.dnm');cockpit=zi.read('runtime/aircraft/su30smcockpit.dnm')
   assert SHA(oldmodel)==META['baseline_model_sha256'] and SHA(cockpit)==META['cockpit_sha256'];assert exe!=oldexe
   baseline={'su30sm.dnm':oldmodel,'su30smcockpit.dnm':cockpit};models={'su30sm.dnm':model,'su30smcockpit.dnm':cockpit}
   passport=json.loads(zi.read('runtime/ARCHITECTURE.json'));newpassport=dict(passport);newpassport.update(exe_sha256=SHA(exe),model_sha256=SHA(model),cockpit_sha256=SHA(cockpit),engine_recompiled=True,native_windows_launch_verified=True,current_model_native_windows_launch_retested=True,native_windows_run=check['actions_run_url'],current_change='Su30SM vector nozzles: canted rigid gimbals, coordinated aperture and throat, thrust-force/moment control; game approximation, not factory FCS',historical_passport=passport)
   repl={f'runtime/ysflight{bits}_gl1.exe':exe,'runtime/aircraft/su30sm.dnm':model,'runtime/ARCHITECTURE.json':json.dumps(newpassport,indent=2).encode()}
   # Replace the existing source pointer, keeping its previous bytes in rollback.
   pointer=[n for n in zi.namelist() if n.endswith('SOURCE_DOWNLOADS.txt')]
   for n in pointer:repl[n]=f'Complete corresponding modified engine code, aircraft generator, dependencies and notices:\nhttps://github.com/{REPO}/releases/download/{TAG}/Su30SM_VectorNozzles_FullSources.zip\nHistorical original GLB/model and sources remain linked in README.md of FullSources.\n'.encode()
   with zipfile.ZipFile(dest,'w') as zo:
    for n in zi.namelist():put(zo,n,repl.get(n,zi.read(n)))
    for n in repl:put(zo,'runtime/rollback-vector-nozzles/'+n,zi.read(n))
    put(zo,'runtime/rollback-vector-nozzles/RESTORE_RU.txt','Закрыть игру. Скопировать ВСЁ содержимое вложенной папки runtime обратно в runtime игры; заменённый SOURCE_DOWNLOADS.txt также вернуть. EXE и su30sm.dnm восстанавливать вместе, иначе физика и вид сопел будут различаться. Прежние полные CockpitFit ZIP сохранены.\n'.encode())
    put(zo,'README_VECTOR_NOZZLES_RU.txt',f'Су-30СМ: управление соплами и раскрытием. Запуск прежним BAT. Проверен настоящий Windows {arch}, PE проверен, шасси/кабина/окраска сохранены. Схема управления физически согласована; это игровая аппроксимация, не заводская СДУ/FADEC. Видео, ограничения и исходники: https://github.com/{REPO}/releases/tag/{TAG}\nОткат: инструкция runtime/rollback-vector-nozzles/RESTORE_RU.txt.\n'.encode())
   with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    kept=[n for n in zi.namelist() if n not in repl];assert all(z.read(n)==zi.read(n) for n in kept)
    assert z.read('runtime/aircraft/su30smcockpit.dnm')==cockpit
    assert not any('TASK_CONTEXT' in n for n in z.namelist())
   records.append(dict(file=dest.name,sha256=SHA(dest.read_bytes()),bytes=dest.stat().st_size,bits=bits,exe_sha256=SHA(exe),model_sha256=SHA(model),cockpit_sha256=SHA(cockpit),native_windows_verified=True,native_run=RUN,unchanged_previous_entries=len(kept),zip_crc_passed=True,**pe(exe,bits)));exes.append(SHA(exe))
 assert exes[0]!=exes[1]
 sources=out/'Su30SM_VectorNozzles_FullSources.zip'
 with zipfile.ZipFile(sources,'w') as z:
  for f in sorted(engine.rglob('*')):
   if f.is_file():put(z,'engine/'+str(f.relative_to(engine)),f.read_bytes())
  for folder in ['changes/su30sm-nozzle-vector','changes/su30sm-local-skin/model-source','dist/su30sm-nozzle-vector']:
   for f in sorted((ROOT/folder).rglob('*')):
    if f.is_file() and '__pycache__' not in f.parts and f.name!='evidence.zip':put(z,str(f.relative_to(ROOT)),f.read_bytes())
  for folder,data in [('baseline',baseline),('generated',models)]:
   for n,b in data.items():put(z,folder+'/'+n,b)
  put(z,'README.md',(STAGE/'README.md').read_bytes());put(z,'REPORT_RU.md',(report/'REPORT_RU.md').read_bytes())
  for n in ['su30sm-nozzle-vector-native.yml','su30sm-nozzle-vector-publish.yml']:put(z,'.github/workflows/'+n,(ROOT/'.github/workflows'/n).read_bytes())
 with zipfile.ZipFile(sources) as z:assert z.testzip() is None
 visual=out/'Su30SM_VectorNozzles_Report.zip'
 with zipfile.ZipFile(visual,'w') as z:
  for f in sorted(report.rglob('*')):
   if f.is_file():put(z,str(f.relative_to(report)),f.read_bytes())
 for f in report.glob('*.mp4'):shutil.copyfile(f,out/f.name)
 (out/'packages.json').write_text(json.dumps(records,indent=2));files=sorted(f for f in out.iterdir() if f.is_file() and f.name!='SHA256SUMS.txt');(out/'SHA256SUMS.txt').write_text(''.join(SHA(f.read_bytes())+'  '+f.name+'\n' for f in files));print(json.dumps(records,indent=2))
if __name__=='__main__':build(Path(sys.argv[1]))
