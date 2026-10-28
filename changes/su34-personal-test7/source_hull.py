"""Recreate the donor hull before gear carving, retaining all original exclusions.
Raw bone15 is not a clean fixed airframe: it contains baked stores and the
outer aileron strips. Reuse the pinned geometry conversion stage, not its rig.
"""
from pathlib import Path
import hashlib

def read_hull(helper,dnm):
 helper=Path(helper);code=helper.read_text();marker='# Initial source-derived rig exported below; fit/clearance validation is separate.'
 assert marker in code
 ns={'__file__':str(helper),'__name__':'source_hull_geometry_only'}
 exec(compile(code.split(marker)[0],str(helper),'exec'),ns)
 hull=ns['double'](ns['hull'])
 # The shipping SRF stores six decimals, as did the reviewed reference.
 return dnm.mesh(hull.srf())
