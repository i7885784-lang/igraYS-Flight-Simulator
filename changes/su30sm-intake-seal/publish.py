"""Deliver the exact model-only update with rollback, source patch and real visual evidence."""
from pathlib import Path
import os,json,hashlib,zipfile,tempfile,shutil,subprocess,sys
REPO='i7885784-lang/igraYS-Flight-Simulator';TAG='personal-su30sm-intake-seal-20261106';C=Path(__file__).resolve().parent;R=Path('reports/su30sm-intake-seal').resolve()
def gh(*a):return subprocess.check_output(['gh',*a])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pack(root,p):
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,6) as z:
  for f in sorted(root.rglob('*')):
   if f.is_file() and '__pycache__' not in f.parts:z.write(f,root.name+'/'+f.relative_to(root).as_posix())
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
release=json.loads(gh('api',f'repos/{REPO}/releases/'+os.environ['RELEASE_ID']));assert release['draft'] and release['tag_name']==TAG
manifest=json.loads((C/'manifest.json').read_text());assert json.loads((R/'validation.json').read_text())['model_sha256']==manifest['model_sha256'];assert len(json.loads((R/'comparisons.json').read_text()))==18
with tempfile.TemporaryDirectory() as td:
 t=Path(td);old=json.loads(Path('reports/su30sm-bay-seams/STATUS.json').read_text());a=next(a for a in old['assets'] if a['name'].endswith('_Windows_x64.zip'));gh('release','download',old['tag'],'--repo',REPO,'--pattern',a['name'],'--dir',str(t));p=t/a['name'];assert sha(p)==a['sha256']
 root=t/'Su30SM_IntakeSeal';source=root/'source';shutil.copytree(C,source,ignore=shutil.ignore_patterns('__pycache__'));(source/'baseline').mkdir(exist_ok=True)
 with zipfile.ZipFile(p) as z:(source/'baseline/su30sm.dnm').write_bytes(z.read('runtime/aircraft/su30sm.dnm'))
 assert sha(source/'baseline/su30sm.dnm')==manifest['baseline_sha256'];subprocess.run([sys.executable,str(source/'build.py')],check=True);assert sha(source/'runtime/aircraft/su30sm.dnm')==manifest['model_sha256']
 (root/'aircraft').mkdir();shutil.copy2(source/'runtime/aircraft/su30sm.dnm',root/'aircraft/su30sm.dnm');shutil.rmtree(source/'runtime');(root/'rollback').mkdir();shutil.copy2(source/'baseline/su30sm.dnm',root/'rollback/su30sm.dnm');shutil.copytree(R,root/'report')
 (root/'README_RU.txt').write_text('''Су-30СМ: точечное обновление воздухозаборников\n\nЭто обновление МОДЕЛИ, не полная сборка игры. Подходит к последней BaySeams-модели с SHA ea3d9ced56a637c5a81c75b4acd2641f35902397149e72b495cfebe5196f0a53.\nЗакройте игру, сохраните текущий runtime/aircraft/su30sm.dnm и замените его файлом aircraft/su30sm.dnm из этого архива. Для отката есть rollback/su30sm.dnm. Другие файлы игры не заменяются. Ресурс модели одинаков для x86/x64; EXE не включены и не менялись.\n\nОтчёт и все18сравнений: report/index.html; краткий текст: report/REPORT_RU.md; PDF и видео также в report. Исходники узкой правки: source/. Полные прежние движок/GLB/лицензии сохранены в предыдущих FullSources и истории репозитория.\n''',encoding='utf-8-sig')
 combined=t/'Su30SM_IntakeSeal_Model_Report.zip';report=t/'Su30SM_IntakeSeal_Photos_Video.zip';pack(root,combined);pack(R,report);paths=[combined,report,R/'Su30SM_IntakeSeal_Report_RU.pdf',R/'videos/intake-camera-sweep.mp4']
 for p in paths:gh('release','upload',TAG,str(p),'--repo',REPO)
 verify=t/'verified';verify.mkdir();gh('release','download',TAG,'--repo',REPO,'--dir',str(verify))
 for p in paths:
  assert sha(p)==sha(verify/p.name)
  if p.suffix=='.zip':
   with zipfile.ZipFile(verify/p.name) as z:assert z.testzip() is None
 release=json.loads(gh('api',f'repos/{REPO}/releases/'+os.environ['RELEASE_ID']));status={'release_id':release['id'],'draft':True,'release_url':release['html_url'],'tag':TAG,'source_commit':os.environ['GITHUB_SHA'],'model_sha256':manifest['model_sha256'],'baseline_sha256':manifest['baseline_sha256'],'model_only_no_executables':True,'download_sha_crc_verified':True,'exact_rebuild_verified':True,'assets':[{'name':p.name,'size':p.stat().st_size,'sha256':sha(p),'url':next(a['browser_download_url'] for a in release['assets'] if a['name']==p.name)} for p in paths]};p=t/'STATUS.json';p.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n');gh('release','upload',TAG,str(p),'--repo',REPO);print(json.dumps(status,indent=2))
