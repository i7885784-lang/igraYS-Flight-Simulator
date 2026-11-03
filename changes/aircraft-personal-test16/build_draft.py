from pathlib import Path
import tempfile,subprocess,zipfile,shutil,hashlib,json,os
repo='i7885784-lang/igraYS-Flight-Simulator';tag='personal-fighters-test16-20261103';rid=432263427
root=Path.cwd();code=root/'changes/aircraft-personal-test16';report=root/'reports/personal-playtest-16'
def gh(*args):return subprocess.check_output(['gh',*args])
def sha(b):return hashlib.sha256(b).hexdigest()
release=json.loads(gh('api',f'repos/{repo}/releases/{rid}'));assert release['draft'];prefix=release['html_url'].replace('/tag/','/download/')
expected=json.loads((report/'preservation.json').read_text())
with tempfile.TemporaryDirectory() as td:
 t=Path(td);gh('release','download','personal-fighters-test15-20261031','--repo',repo,'--pattern','YSFlight_Test_15_Game_32bit.zip','--pattern','YSFlight_Personal_Test_15_Sources.zip','--dir',str(t))
 known=json.loads((root/'reports/personal-playtest-15/STATUS.json').read_text())
 for a in known['assets']:
  p=t/a['name']
  if p.exists():assert sha(p.read_bytes())==a['sha256']
 with zipfile.ZipFile(t/'YSFlight_Personal_Test_15_Sources.zip') as z:z.extractall(t)
 src=t/'sources';work=src/'test16';shutil.copytree(code,work,ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(src/'test15/model-source',work/'model-source');(work/'baseline').mkdir()
 with zipfile.ZipFile(t/'YSFlight_Test_15_Game_32bit.zip') as z:
  for k in ['mig29','su57']:(work/'baseline'/f'{k}.dnm').write_bytes(z.read(f'YSFlight_Test_15_Game/aircraft/{k}.dnm'))
 subprocess.run(['python',str(work/'build_models.py')],check=True)
 model=(work/'runtime/aircraft/mig29.dnm').read_bytes();assert sha(model)==expected['mig_sha256'],sha(model)
 game=t/'YSFlight_Test_16_Game';game.mkdir()
 with zipfile.ZipFile(t/'YSFlight_Test_15_Game_32bit.zip') as z:
  for name in z.namelist():
   if name.endswith('/'):continue
   rel=name.split('/',1)[1];p=game/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(model if rel in expected['changed_files'] else z.read(name))
  for name in z.namelist():
   rel=name.split('/',1)[-1]
   if not name.endswith('/') and (rel.startswith('aircraft/') or rel.endswith('.exe')) and rel not in expected['changed_files']:assert (game/rel).read_bytes()==z.read(name)
 (game/'SOURCE_DOWNLOADS.txt').write_text('Complete corresponding sources:\n'+prefix+'/YSFlight_Test_16_Sources.zip\n')
 (game/'TEST_16_MANIFEST.json').write_text(json.dumps(expected,indent=2))
 (game/'READ_ME_RU.txt').write_text('Личный тест №16 от №15. МиГ-29: сопряжение стенки ниши и выступ торцевой заглушки. Запуск ysflight32_gl1.exe. G — шасси. Су-57 и остальные самолёты сохранены №15. Промежуточные створки Су-57 показаны только в отчёте.\n',encoding='utf-8-sig')
 shutil.rmtree(work/'runtime');(work/'TEST_16_MANIFEST.json').write_text(json.dumps(expected,indent=2));(src/'README_TEST16_RU.txt').write_text('Новые изменения в test16/. pip install -r test16/requirements.txt; python test16/build_models.py. Все исходники и авторство предыдущих версий сохранены. split_su57.py — только непринятый предпросмотр, в игру16 не входит.\n')
 assets=[]
 for name,folder in [('YSFlight_Test_16_Game_32bit.zip',game),('YSFlight_Test_16_Sources.zip',src),('YSFlight_Test_16_Report.zip',report)]:
  p=t/name
  with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,6) as z:
   for f in sorted(folder.rglob('*')):
    if f.is_file() and '__pycache__' not in f.parts:z.write(f,folder.name+'/'+str(f.relative_to(folder)))
  with zipfile.ZipFile(p) as z:assert z.testzip() is None
  gh('release','upload',tag,str(p),'--repo',repo)
  v=t/'verify';v.mkdir(exist_ok=True);gh('release','download',tag,'--repo',repo,'--pattern',name,'--dir',str(v));assert sha((v/name).read_bytes())==sha(p.read_bytes())
  assets.append({'name':name,'url':prefix+'/'+name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'download_verified':True})
 assert json.loads(gh('api',f'repos/{repo}/releases/{rid}'))['draft'];(report/'STATUS.json').write_text(json.dumps({'draft':True,'assets':assets},indent=2))
