"""Recreate uncut Su-34 geometry from the preserved YFT converter in the full sources ZIP."""
from pathlib import Path
import sys,hashlib
r=Path(__file__).resolve().parent;legacy=r.parent/'test7-su34/model-source/legacy_build_model.py'
if not legacy.is_file():raise SystemExit('Use the full private source archive: test7-su34/model-source and upstream/su34_hi.yft are required.')
sys.path.insert(0,str(legacy.parent));import dnm
marker='# Initial source-derived rig exported below; fit/clearance validation is separate.'
code=legacy.read_text();assert marker in code;scope={'__file__':str(legacy),'__name__':'original_geometry_only'};exec(compile(code.split(marker)[0],str(legacy),'exec'),scope)
m=dnm.mesh(scope['double'](scope['hull']).srf());data='\n'.join(m.srf())+'\n';(r/'uncut-su34.srf').write_text(data);print('source reference',hashlib.sha256(data.encode()).hexdigest())
