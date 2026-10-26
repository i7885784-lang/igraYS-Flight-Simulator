"""Package the unchanged baseline resources with freshly built Win32 binaries."""
from pathlib import Path
import zipfile,hashlib,struct,json,subprocess,shutil
d=Path('/workspace/ysflight-dev');r=Path('/workspace/igraYS-Flight-Simulator')
s=d/'YSFlight_Su57_Test_2_Engine_Source';out=d/'evidence';out.mkdir(exist_ok=True)
target=out/'YSFlight_Su57_Test_2_Environment_Check_32bit.zip'
prefix='YSFlight_Su57_Test_2_Environment_Check_32bit/'
replacement={
 'ysflight32_gl1.exe':s/'build32/main/ysflight32_gl1.exe',
 'plugin/sndYsflight32.dll':s/'build32/sounddll/win32/libsndYsflight32.dll',
 'plugin/voiceYsflight32.dll':s/'build32/voicedll/generic/libvoiceYsflight32.dll'}
checks={};imports={};system={'comdlg32.dll','gdi32.dll','glu32.dll','imm32.dll','kernel32.dll','msvcrt.dll','opengl32.dll','shell32.dll','user32.dll','winmm.dll','wsock32.dll','dsound.dll','advapi32.dll','ole32.dll','oleaut32.dll','winspool.drv'}
for name,p in replacement.items():
 b=p.read_bytes();pe=struct.unpack_from('<I',b,0x3c)[0]
 assert b[pe:pe+4]==b'PE\0\0' and struct.unpack_from('<H',b,pe+4)[0]==0x14c
 if name.endswith('.exe'):
  assert struct.unpack_from('<H',b,pe+24+68)[0]==2
  assert b'MODELCHECK t=' not in b and b'ARMAMENTCHECK time=' not in b
 text=subprocess.check_output(['i686-w64-mingw32-objdump','-p',str(p)],text=True)
 dlls=[a.split('DLL Name: ')[1].strip() for a in text.splitlines() if 'DLL Name: ' in a];imports[name]=dlls
 assert all(a.lower() in system for a in dlls),dlls
with zipfile.ZipFile(r/'downloads/YSFlight_Su57_Test_2_32bit.zip') as base,zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,6) as z:
 for item in base.infolist():
  rel=item.filename.split('/',1)[1]
  if rel: z.writestr(prefix+rel,replacement[rel].read_bytes() if rel in replacement else base.read(item))
with zipfile.ZipFile(target) as z,zipfile.ZipFile(r/'downloads/YSFlight_Su57_Test_2_32bit.zip') as base:
 assert z.testzip() is None
 count=0
 for item in base.infolist():
  rel=item.filename.split('/',1)[1]
  if rel and rel not in replacement:assert z.read(prefix+rel)==base.read(item);count+=1
 assert len([n for n in z.namelist() if n.lower().endswith('.exe')])==1
 for model in ['su27','mig29','su57']:
  assert any(('aircraft/'+model+'.dat aircraft/'+model+'.dnm').encode() in z.read(n) for n in z.namelist() if n.endswith('aircraft/aircraft.lst'))
checks={'passed':True,'archive_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'unchanged_baseline_entries':count,'replaced_files':{n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in replacement.items()},'imports':imports,'target':'PE32 i386 GUI, no diagnostic commands','native_windows_10_x86_run':False}
(out/'package-checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
# Check extraction into an independent directory with all three models/resources intact.
extract=d/'package-extracted';extract.mkdir(exist_ok=True)
with zipfile.ZipFile(target) as z:z.extractall(extract)
