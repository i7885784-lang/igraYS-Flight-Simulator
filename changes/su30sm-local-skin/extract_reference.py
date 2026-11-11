"""Optional provenance check: recover the bundled exact reference from stage4."""
from pathlib import Path
import sys,argparse,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'model-source'))
from common import dnm,Mesh,transform
parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
provenance=json.loads((ROOT/'source-data/provenance.json').read_text());digest=hashlib.sha256(args.source.read_bytes()).hexdigest();assert digest==provenance['source_sha256'],'Wrong reference stage'
p,ns=dnm.read(args.source);n=next(n for n in ns if dnm.name(n)=='Fuselage_0_4');m=dnm.mesh(p[dnm.fil(n)]);R,t=transform(n,0);t+=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);v=np.array(m.v)@R.T+t;out=Mesh();indices=[]
for fi,(ids,c,b) in enumerate(m.f):
 for j in range(1,len(ids)-1):
  q=v[[ids[0],ids[j],ids[j+1]]];normal=np.cross(q[1]-q[0],q[2]-q[0])
  if normal[1]>=-1e-10 or q[:,2].max()<-3.38 or q[:,2].min()>-.41:continue
  if any(q[:,0].max()>=lo and q[:,0].min()<=hi for lo,hi in [(-1.87,-1.03),(1.03,1.87)]):out.face(q,c,b);indices.append(fi)
assert indices==provenance['source_face_indices'];args.output_dir.mkdir(parents=True,exist_ok=True);target=args.output_dir/'original-hull.srf';target.write_text('\n'.join(out.srf())+'\n');assert hashlib.sha256(target.read_bytes()).hexdigest()==provenance['reference_srf_sha256'];print('Reference SHA and source indices match')
