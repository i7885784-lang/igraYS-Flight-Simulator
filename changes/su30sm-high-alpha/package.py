"""Ship only the exact native-tested executable; all prior aircraft assets stay exact."""
from pathlib import Path
import sys,json,zipfile,shutil,subprocess
from build_candidate import ROOT,STAGE,MODEL,COCKPIT,FILES,baseline,source,pe,SHA
TAG='su30sm-high-alpha-20261115';REPO='i7885784-lang/igraYS-Flight-Simulator';RUN=43687813404;NATIVE_RUNS={32:43689098018,64:43687813404}
STAMP=(2026,11,15,0,0,0)
def put(z,n,b):
 i=zipfile.ZipInfo(n,STAMP);i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,b,compresslevel=6)
def run(out):
 out.mkdir(parents=True,exist_ok=True);report=ROOT/'reports/su30sm-high-alpha';report.mkdir(parents=True,exist_ok=True)
 e=ROOT/'dist/su30sm-high-alpha/evidence.zip';meta=json.loads((ROOT/'dist/su30sm-high-alpha/evidence.json').read_text());chunks=[]
 for part in meta['parts']:
  chunk=(ROOT/'dist/su30sm-high-alpha'/part['file']).read_bytes();assert SHA(chunk)==part['sha256'];chunks.append(chunk)
 e.write_bytes(b''.join(chunks));assert SHA(e.read_bytes())==meta['sha256']
 with zipfile.ZipFile(e) as z:assert z.testzip() is None;z.extractall(report)
 engine=source(ROOT/'work/source-package');subprocess.run([sys.executable,str(STAGE/'patch.py'),str(engine)],check=True);rows=[];models=None
 for bits,arch in [(32,'x86'),(64,'x64')]:
  built=ROOT/f'artifacts/build-{bits}';native=ROOT/f'artifacts/native-{bits}';info=json.loads((built/'build-info.json').read_text());test=json.loads((native/'results.json').read_text());exe=(built/f'ysflight{bits}_gl1.exe').read_bytes();pe(exe,bits)
  assert info['bits']==bits and SHA(exe)==info['exe_sha256']==test['exe_sha256']
  assert test['passed'] and test['native_windows'] and test['model_sha256']==MODEL and test['cockpit_sha256']==COCKPIT
  recording=json.loads((report/'recording-build.json').read_text());assert info['source_files']==recording['source_files']
  assert all(SHA((engine/p).read_bytes())==s for p,s in info['source_files'].items()) and set(FILES)==set(info['source_files'])
  nr=report/f'native-{bits}';nr.mkdir(exist_ok=True)
  for f in native.glob('*.png'):shutil.copyfile(f,nr/f.name)
  (nr/'results.json').write_text(json.dumps(test,indent=2));shutil.copyfile(built/'build-info.json',nr/'build-info.json')
  dest=out/f'Su30SM_HighAlpha_Windows_{arch}.zip'
  with zipfile.ZipFile(baseline(bits)) as old:
   assert old.testzip() is None;models={n:old.read('runtime/aircraft/'+n) for n in ['su30sm.dnm','su30smcockpit.dnm']};assert SHA(models['su30sm.dnm'])==MODEL and SHA(models['su30smcockpit.dnm'])==COCKPIT
   passport=json.loads(old.read('runtime/ARCHITECTURE.json'));new=dict(passport);new.update(exe_sha256=SHA(exe),engine_recompiled=True,native_windows_launch_verified=True,native_windows_run=f'https://github.com/{REPO}/actions/runs/{NATIVE_RUNS[bits]}',current_change='Optional manual high-alpha control Ctrl+L for SU-30SM_CUSTOM; all aircraft resource files exact; game approximation, not factory flight-control software',historical_passport=passport)
   repl={f'runtime/ysflight{bits}_gl1.exe':exe,'runtime/ARCHITECTURE.json':json.dumps(new,indent=2).encode(),'runtime/SOURCE_DOWNLOADS.txt':f'Complete corresponding modified sources and notices:\nhttps://github.com/{REPO}/releases/download/{TAG}/Su30SM_HighAlpha_FullSources.zip\nPrevious complete sources/history remain preserved in the VectorNozzles release.\n'.encode()}
   assert exe!=old.read(f'runtime/ysflight{bits}_gl1.exe')
   with zipfile.ZipFile(dest,'w') as z:
    for n in old.namelist():put(z,n,repl.get(n,old.read(n)))
    for n in repl:put(z,'runtime/rollback-high-alpha/'+n,old.read(n))
    put(z,'README_HIGH_ALPHA_RU.txt',('Су-30СМ: Ctrl+L отключает обычный ограничитель для ручного управления на больших углах атаки. По умолчанию режим выключен. Включать в воздухе ниже720км/ч; вернуть обычный режим можно при угле атаки меньше25°. Это игровая аппроксимация, не заводская СДУ. Для кобры вход около600км/ч, короткое взятие ручки на себя, затем нейтраль и восстановление скорости/горизонтального полёта. Сам факт отключения ограничителя не гарантирует успешный выход: не держать ручку бесконечно, следить за скоростью и высотой. Видео и ограничения в отчёте.\nОткат: закрыть игру и скопировать содержимое rollback-high-alpha/runtime обратно в runtime с заменой EXE/паспорта/источников. Модель не менялась. Предыдущие полные ZIP сохранены.\n').encode())
   with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None;kept=[n for n in old.namelist() if n not in repl];assert all(z.read(n)==old.read(n) for n in kept);assert not any('TASK_CONTEXT' in n for n in z.namelist())
   rows.append(dict(file=dest.name,bits=bits,sha256=SHA(dest.read_bytes()),bytes=dest.stat().st_size,exe_sha256=SHA(exe),model_sha256=MODEL,cockpit_sha256=COCKPIT,native_windows_verified=True,zip_crc_passed=True,unchanged_previous_entries=len(kept),native_run=NATIVE_RUNS[bits],**pe(exe,bits)))
 assert len({r['exe_sha256'] for r in rows})==2
 src=out/'Su30SM_HighAlpha_FullSources.zip'
 with zipfile.ZipFile(src,'w') as z:
  for f in sorted(engine.rglob('*')):
   if f.is_file():put(z,'engine/'+str(f.relative_to(engine)),f.read_bytes())
  for folder in ['changes/su30sm-high-alpha','changes/su30sm-nozzle-vector','changes/su30sm-local-skin/model-source','dist/su30sm-nozzle-vector']:
   for f in sorted((ROOT/folder).rglob('*')):
    if f.is_file() and '__pycache__' not in f.parts and f.name!='evidence.zip':put(z,str(f.relative_to(ROOT)),f.read_bytes())
  for n,b in models.items():put(z,'generated/'+n,b);put(z,'baseline/'+n,b)
  put(z,'README.md',(STAGE/'README.md').read_bytes());put(z,'REPORT_RU.md',(report/'REPORT_RU.md').read_bytes())
  for n in ['su30sm-high-alpha-native.yml','su30sm-high-alpha-native32.yml','su30sm-high-alpha-publish.yml']:put(z,'.github/workflows/'+n,(ROOT/'.github/workflows'/n).read_bytes())
 with zipfile.ZipFile(src) as z:assert z.testzip() is None
 reportzip=out/'Su30SM_HighAlpha_Report.zip'
 with zipfile.ZipFile(reportzip,'w') as z:
  for f in sorted(report.rglob('*')):
   if f.is_file():put(z,str(f.relative_to(report)),f.read_bytes())
 for f in report.glob('*.mp4'):shutil.copyfile(f,out/f.name)
 (out/'packages.json').write_text(json.dumps(rows,indent=2));(out/'SHA256SUMS.txt').write_text(''.join(SHA(f.read_bytes())+'  '+f.name+'\n' for f in sorted(out.iterdir()) if f.is_file() and f.name!='SHA256SUMS.txt'));print(json.dumps(rows,indent=2))
if __name__=='__main__':run(Path(sys.argv[1]))
