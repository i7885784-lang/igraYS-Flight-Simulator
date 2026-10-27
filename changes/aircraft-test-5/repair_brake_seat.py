"""Apply only the brake-panel correction, preserving every gear/control state."""
from pathlib import Path
import sys,numpy as np,json,hashlib,math,warnings
from scipy.spatial.transform import Rotation
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent;sys.path.insert(0,str(root/'model-source'))
import dnm
from mesh import Mesh,node
from ac_reference import AC
from corrections import add_brake
rt=root/'runtime/aircraft';packs,nodes=dnm.read(rt/'su27.dnm');old={dnm.name(n):(n,packs[dnm.fil(n)]) for n in nodes};m=Mesh();ac=AC(root/'model-source/upstream/su27/Su-27.ac');o=next(o for o in ac.objects if o['name']=='HULL_Speedbrake_Outer');v=np.array(o['v'])+np.array([0,0,10])
for f in o['f']:m.face([v[i] for i in f],(119,151,175))
def double(m):
 for f,c,b in list(m.f):m.face([m.v[i] for i in f[::-1]],c,b)
def sta(R=np.eye(3),t=np.zeros(3),show=1):
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');h,p,b=Rotation.from_matrix(R).as_euler('YXZ')
 return ' '.join(map(str,[*np.round(t,7),round(-h*32768/math.pi),round(-p*32768/math.pi),round(b*32768/math.pi),show]))
def add(name,m,cla=99,states=None):
 fn=name+'.srf';packs[fn]=m.srf();n=node(name,fn,cla)
 if states:
  i=n.index('NST 1');j=n.index('POS 0 0 0 0 0 0 1');n[i:j]=['NST '+str(len(states))]+['STA '+s for s in states]
 nodes.append(n)
nodes=[n for n in nodes if dnm.name(n) not in ['DorsalBrake','CompactBrakeDrive0','CompactBrakeDrive1']]
info=add_brake(m,add,double,sta);preserved=[]
for n in nodes:
 name=dnm.name(n)
 if name in ['DorsalBrake','CompactBrakeDrive0','CompactBrakeDrive1']:continue
 assert n==old[name][0] and packs[dnm.fil(n)]==old[name][1];preserved.append(name)
for name in ['su27.dnm','su27_coarse.dnm']:dnm.write(rt/name,packs,nodes)
(root/'brake-seat-check.json').write_text(json.dumps({'source_panel_preserved':True,'old_length_factor':.71,'old_width_factor':1.18,'new_dimensions_m':np.ptp(v,axis=0).tolist(),'all_other_nodes_byte_preserved':preserved,'drive':info,'model_sha256':hashlib.sha256((rt/'su27.dnm').read_bytes()).hexdigest()},indent=2))
print('Brake seat repaired; other nodes preserved:',len(preserved))
