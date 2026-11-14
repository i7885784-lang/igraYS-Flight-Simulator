from pathlib import Path
import sys,json,zipfile,subprocess
from apply import SHA,patch_bytes
root=Path.cwd();bits=int(sys.argv[1]);arch='x86' if bits==32 else 'x64';name=f'Su30SM_CockpitFit_Windows_{arch}.zip'
subprocess.run(['gh','release','download','su30sm-cockpit-fit-20261114','--repo','i7885784-lang/igraYS-Flight-Simulator','--pattern',name,'--dir','downloads'],check=True)
p=root/'downloads'/name;expected={'x86':'0c7cfcfedee6fc391216ea8915060c6209cb4b7011e3287d53ef475c2952cde6','x64':'a4a577a23da6ff7dded8e87cf02c41e789c829da453eb0fda5ce9d8308fa66fe'};assert SHA(p.read_bytes())==expected[arch]
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None;data=patch_bytes(z.read('runtime/aircraft/su30sm.dnm'));z.extractall(root)
(root/'runtime/aircraft/su30sm.dnm').write_bytes(data)
assert SHA((root/'runtime/aircraft/su30smcockpit.dnm').read_bytes())=='564308f1149862461dbc254dfb4372475a067ed0182eb61faf9d7345fa1807b9'
print('Prepared exact model and preserved cockpit',bits)
