from pathlib import Path
import dnm
r=Path(__file__).resolve().parent.parent
p,ns=dnm.read(r/'runtime/aircraft/su30sm.dnm')
for name,lines in p.items():
 p[name]=[' '.join(line.split()[:4]) if line.startswith('V ') and ' R ' in line else line for line in lines]
dnm.write(r/'runtime/aircraft/su30sm.dnm',p,ns)
(r/'runtime/aircraft/su30sm_coarse.dnm').unlink(missing_ok=True)
