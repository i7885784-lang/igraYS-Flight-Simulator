"""Separate genuine x86/x64 games; unchanged engine, exact model, complete source history."""
from pathlib import Path
import os,json,hashlib,zipfile,subprocess,shutil,tempfile,sys,struct
REPO='i7885784-lang/igraYS-Flight-Simulator';TAG='personal-su30sm-natural-intake-20261106';C=Path(__file__).resolve().parent;R=Path('reports/su30sm-natural-pass').resolve()
def gh(*a):return subprocess.check_output(['gh',*a])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def machine(p):
 b=p.read_bytes();return struct.unpack_from('<H',b,struct.unpack_from('<I',b,0x3c)[0]+4)[0]
def pack(root,p):
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,6) as z:
  for f in sorted(root.rglob('*')):
   if f.is_file() and '__pycache__' not in f.parts:z.write(f,root.name+'/'+f.relative_to(root).as_posix())
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
release=json.loads(gh('api',f'repos/{REPO}/releases/'+os.environ['RELEASE_ID']));assert release['draft'] and release['tag_name']==TAG
manifest=json.loads((C/'manifest.json').read_text());assert json.loads((R/'validation.json').read_text())['model_sha256']==manifest['model_sha256']
with tempfile.TemporaryDirectory() as td:
 t=Path(td);paths=[];architectures={};downloaded={}
 def obtain(report,suffix):
  status=json.loads(Path('reports',report,'STATUS.json').read_text());a=next(a for a in status['assets'] if a['name'].endswith(suffix));p=t/a['name'];gh('release','download',status['tag'],'--repo',REPO,'--pattern',a['name'],'--dir',str(t));assert sha(p)==a['sha256'];return p
 full=obtain('su30sm-bay-seams','_FullSources.zip')
 with zipfile.ZipFile(full) as z:z.extractall(t)
 source=t/'sources'
 assert (source/'su30sm-test3/engine/YSFLIGHT/src/vehicle/fsairplaneproperty.cpp').is_file() and (source/'su30sm-test4/source/su-30sm.glb').is_file()
 for old,folder in [('su30sm-intake-seal','Su30SM_IntakeSeal'),('su30sm-intake-depth','Su30SM_IntakeDepth')]:
  p=obtain(old,'_Model_Report.zip')
  with zipfile.ZipFile(p) as z:
   prefix=folder+'/source/'
   for n in z.namelist():
    if n.startswith(prefix) and not n.endswith('/'):
     f=source/old/n[len(prefix):];f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(n))
   if old=='su30sm-intake-depth':baseline=z.read(folder+'/aircraft/su30sm.dnm')
 work=source/'su30sm-natural-pass';shutil.copytree(C,work,ignore=shutil.ignore_patterns('__pycache__','runtime','geometry-cache'));(work/'baseline').mkdir(exist_ok=True);(work/'baseline/su30sm.dnm').write_bytes(baseline);assert sha(work/'baseline/su30sm.dnm')==manifest['baseline_sha256'];subprocess.run([sys.executable,str(work/'build.py')],check=True);model=work/'runtime/aircraft/su30sm.dnm';assert sha(model)==manifest['model_sha256']
 (source/'README_NATURAL_INTAKE_RU.txt').write_text('Текущая модель: su30sm-natural-pass/. baseline/ — точная ECEE для отката. python build.py воспроизводит новый DNM; repair.py заново измеряет19сечений. Движок не перекомпилирован: полные предыдущие снимки движка/GLB/лицензии и вся история сохранены в прежних папках. Дополнены предыдущие этапы intake-seal/intake-depth. Отчёт указывает оставшиеся дефекты; весь самолёт не объявлен идеальным.\n',encoding='utf-8-sig')
 for bits,cpu in [(32,0x14c),(64,0x8664)]:
  p=obtain('su30sm-bay-seams',f'_Windows_x{86 if bits==32 else 64}.zip');gameparent=t/f'game{bits}';gameparent.mkdir()
  with zipfile.ZipFile(p) as z:z.extractall(gameparent)
  game=gameparent/'runtime';old=sha(game/'aircraft/su30sm.dnm');shutil.copy2(model,game/'aircraft/su30sm.dnm')
  exes=list(game.glob('*.exe'));assert len(exes)==1 and machine(exes[0])==cpu
  for dll in (game/'plugin').glob('*.dll'):assert machine(dll)==cpu
  test=json.loads((R/f'native-windows-{bits}/results.json').read_text());assert test['passed'] and test['native_windows'] and test['machine']==hex(cpu) and test['exe_sha256']==sha(exes[0]) and test['model_sha256']==manifest['model_sha256']
  proof={'architecture':f'Windows {bits}-bit','machine':hex(cpu),'exe':exes[0].name,'exe_sha256':sha(exes[0]),'model_sha256':manifest['model_sha256'],'engine_recompiled':False,'native_windows_launch_verified':True,'native_windows_run':42234017006,'check_scope':test['scope']};architectures[str(bits)]=proof;(game/'ARCHITECTURE.json').write_text(json.dumps(proof,indent=2))
  (game/'rollback-natural-intake').mkdir();(game/'rollback-natural-intake/su30sm.dnm').write_bytes(baseline)
  (game/'SU30SM_NATURAL_INTAKE_README_RU.txt').write_text(f'Windows {bits}-bit. Распакуйте отдельно, запустите Play_Su30SM.bat.\nДвижок прежний, изменены только2IntakeDuct в модели. Работает обычный цикл G. Архитектура и реальный запуск Windows проверены; полная визуальная проверка общего ресурса выполнена вx64.\nОткат: при закрытой игре скопируйте rollback-natural-intake/su30sm.dnm вaircraft/su30sm.dnm. Это предыдущаяECEE, исходная№5 и старые архивы не перезаписаны.\nОстатки: старые фасеточные стыки ниш и4расчётных контакта звеньев стоек наg=.32/.325 не исправлены; подробнее отчёт.\n',encoding='utf-8-sig')
  for name in ['SU30SM_BAY_SEAMS_README_RU.txt']:(game/name).unlink(missing_ok=True)
  (game/'SOURCE_DOWNLOADS.txt').write_text(release['html_url'].replace('/tag/','/download/')+'/YSFlight_Su30SM_NaturalIntake_FullSources.zip\n')
  p=t/f'YSFlight_Su30SM_NaturalIntake_Windows_x{86 if bits==32 else 64}.zip';pack(game,p);paths.append(p)
 shutil.rmtree(work/'runtime')
 for root,name in [(source,'YSFlight_Su30SM_NaturalIntake_FullSources.zip'),(R,'Su30SM_NaturalIntake_Report_Photos_Videos.zip')]:
  p=t/name;pack(root,p);paths.append(p)
 paths.append(R/'Su30SM_NaturalIntake_Report_RU.pdf')
 for p in paths:gh('release','upload',TAG,str(p),'--repo',REPO)
 verify=t/'verified';verify.mkdir();gh('release','download',TAG,'--repo',REPO,'--dir',str(verify))
 for p in paths:
  assert sha(p)==sha(verify/p.name)
  if p.suffix=='.zip':
   with zipfile.ZipFile(verify/p.name) as z:assert z.testzip() is None
 release=json.loads(gh('api',f'repos/{REPO}/releases/'+os.environ['RELEASE_ID']));status={'release_id':release['id'],'draft':True,'tag':TAG,'release_url':release['html_url'],'source_commit':os.environ['GITHUB_SHA'],'model_sha256':manifest['model_sha256'],'baseline_sha256':manifest['baseline_sha256'],'architectures':architectures,'download_sha_crc_verified':True,'exact_model_rebuild_verified':True,'complete_previous_sources_preserved':True,'comparison_sets':33,'native_windows_run':42234017006,'remaining_defects':['old faceted/jagged door seams','four inherited torque-link contacts at g=.32/.325','no factory-certified complete geometry reconstruction'],'assets':[{'name':p.name,'size':p.stat().st_size,'sha256':sha(p),'url':next(a['browser_download_url'] for a in release['assets'] if a['name']==p.name)} for p in paths]};p=t/'STATUS.json';p.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n');gh('release','upload',TAG,str(p),'--repo',REPO);print(json.dumps(status,indent=2))
