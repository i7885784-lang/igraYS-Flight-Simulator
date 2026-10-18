from pathlib import Path
import shutil,zipfile,hashlib,json,struct
r=Path('/workspace/ysflight-work');out=Path('/workspace/outputs');base=r/'package-v7/YSFlight_UI_v7_32bit';p=r/'package-lock-test/YSFlight_Lock_Test_32bit'
assert not p.exists(),'Do not overwrite an existing package stage.'
shutil.copytree(base,p);shutil.copy2(p/'READ_ME_RU.txt',p/'READ_ME_v7_RU.txt');(p/'MANIFEST.sha256').unlink()
guide=b'\xef\xbb\xbf'+(r/'LOCK_TEST_READ_ME_RU.txt').read_text().replace('\r\n','\n').replace('\n','\r\n').encode('utf-8')
(p/'READ_ME_RU.txt').write_bytes(guide)
training=p/'practice_v7';training.mkdir()
shutil.copy2(r/'training-v7/practice/01_LOCK_TRAINING.yfs',training/'lock.yfs')
for src,dest in [('v71-ui-locked.png','1_locked.png'),('v71-ui-fired.png','2_fired.png')]:shutil.copy2(r/src,training/dest)
checks={}
with zipfile.ZipFile(out/'YSFlight_UI_v7_32bit.zip') as published:
 for old in base.rglob('*'):
  if not old.is_file():continue
  rel=old.relative_to(base).as_posix()
  if rel in ['READ_ME_RU.txt','MANIFEST.sha256']:continue
  assert old.read_bytes()==(p/rel).read_bytes()==published.read('YSFlight_UI_v7_32bit/'+rel),rel
 for name in ['ysflight32_gl1.exe','ysflight32_gl2.exe']:
  data=(p/name).read_bytes();pe=struct.unpack_from('<I',data,60)[0];assert struct.unpack_from('<H',data,pe+4)[0]==0x14c
  checks[name]=dict(sha256=hashlib.sha256(data).hexdigest(),identical_to_published_v7=True,architecture='PE32 i386')
for profile in ['keyboard','mouse','manual']:
 d=json.loads((r/f'v71-{profile}-check.json').read_text());assert d['passed'];checks[profile]=d
assert not any('FlightHistory' in f.relative_to(p).parts for f in p.rglob('*'))
(p/'MANIFEST.sha256').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.relative_to(p).as_posix()+'\n' for f in sorted(p.rglob('*')) if f.is_file()))
full=out/'YSFlight_Lock_Test_32bit.zip';small=out/'YSFlight_Lock_Training.zip'
with zipfile.ZipFile(full,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for f in sorted(p.rglob('*')):z.write(f,(Path(p.name)/f.relative_to(p)).as_posix())
with zipfile.ZipFile(small,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for f in sorted(training.iterdir()):z.write(f,'practice_v7/'+f.name)
 z.writestr('LOCK_TEST_READ_ME_RU.txt',guide)
for archive in [full,small]:
 archive.chmod(0o644)
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  assert len(z.namelist())==len(set(z.namelist()))
checks.update(all_original_files_preserved=True,no_test_profiles_or_history=True,source_and_executables_unchanged=True,gui_open_and_fly_verified=True)
(r/'lock-training-package-check.json').write_text(json.dumps(checks,indent=2))
sums=''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name+'\n' for f in [full,small]);(out/'SHA256SUMS_lock_training.txt').write_text(sums)
print('PASS unchanged v7 EXEs/assets/config, PE32, both control profiles, real Space key and normal file browser, ZIP CRC.')
print(sums);print('Bytes',full.stat().st_size,small.stat().st_size)
