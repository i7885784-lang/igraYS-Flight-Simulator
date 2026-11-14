"""Add two complete nozzle gimbals; all original SRF payloads remain exact."""
from pathlib import Path
import sys,hashlib,json,argparse
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin/model-source'))
from common import dnm,state,transform
from mesh import Mesh,node
PIVOTS=[np.array([1.19030109,-.50023219,-8.34445498]),np.array([-1.19030109,-.50023219,-8.34445498])]
BASE={'su30sm.dnm':'ee1f9324e1c4a46179efd2af2323e5cd0b599e19221e1d8e04910e3332071f27','su30smcockpit.dnm':'564308f1149862461dbc254dfb4372475a067ed0182eb61faf9d7345fa1807b9'}
sha=lambda b:hashlib.sha256(b).hexdigest()
def seal(center):
 m=Mesh();angles=np.linspace(0,2*np.pi,49);lat=np.deg2rad(np.linspace(-32,32,17))
 def q(a,b,r):return center+np.array([r*np.cos(b)*np.cos(a),r*np.cos(b)*np.sin(a),r*np.sin(b)])
 for radius,reverse,color in [(.532,False,(80,84,90)),(.524,True,(56,58,62))]:
  for j in range(len(lat)-1):
   for i in range(len(angles)-1):
    pts=[q(angles[i],lat[j],radius),q(angles[i+1],lat[j],radius),q(angles[i+1],lat[j+1],radius),q(angles[i],lat[j+1],radius)]
    m.face(pts[::-1] if reverse else pts,color)
 for phi,reverse in [(lat[0],True),(lat[-1],False)]:
  for i in range(len(angles)-1):
   pts=[q(angles[i],phi,.532),q(angles[i+1],phi,.532),q(angles[i+1],phi,.524),q(angles[i],phi,.524)]
   m.face(pts[::-1] if reverse else pts,(70,73,78))
 return m

def run(baseline,out):
 assert sha(baseline.read_bytes())==BASE[baseline.name]
 if baseline.name=='su30smcockpit.dnm':
  out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(baseline.read_bytes());print(out,'unchanged cockpit');return
 p,ns=dnm.read(baseline);original={k:list(v) for k,v in p.items()};before=[list(n) for n in ns];parents={s[4:].strip('"') for n in ns for s in n if s.startswith('CLD ')}
 selected_by_side=[set(),set()]
 for n in before:
  name=dnm.name(n)
  if dnm.cla(n)!=270 and not name.startswith(('Su30NozzleThroat_','Su30Plume_','Su30DryExhaust_')):continue
  pos=np.array(next(line[4:] for line in n if line.startswith('POS ')).split()[:3],float)
  if dnm.cla(n)==270:cx=pos[0]
  else:
   R,t=transform(n,0);v=np.array(dnm.mesh(p[dnm.fil(n)]).v)@R.T+t+pos;cx=(v[:,0].min()+v[:,0].max())*.5
  selected_by_side[0 if cx>0 else 1].add(name)
 rows=[]
 for side,pivot in enumerate(PIVOTS):
  sign=1 if side==0 else -1;names=[]
  for n in ns:
   name=dnm.name(n);selected=name in selected_by_side[side]
   if not selected:continue
   assert name not in parents;names.append(name)
   if name.startswith('Su30NozzleThroat_'):
    j=next(j for j,line in enumerate(n) if line.startswith('CLA '));n[j]='CLA '+str(284+int(name.rsplit('_',1)[1]))
   i=next(i for i,s in enumerate(n) if s.startswith('POS '));parts=n[i].split();pos=np.array(parts[1:4],float);n[i]='POS '+' '.join('%.12f'%x for x in pos-pivot)+' '+' '.join(parts[4:]);assert np.linalg.norm((np.array(n[i].split()[1:4],float)+pivot)-pos)<1e-10
  assert len(names)==35,len(names)
  name='Su30NozzleGimbal_'+str(side);fn=name+'.srf';p[fn]=['SURF','E'];n=node(name,fn,280+side)
  axis=np.array([np.cos(np.deg2rad(32)),sign*np.sin(np.deg2rad(32)),0]);angles=[0]+[x*.5 for x in range(1,31)]+[-x*.5 for x in range(1,31)]
  n=[s for s in n if not s.startswith(('NST ','STA ','POS ','NCH '))];i=n.index('REL DEP');n[i:i]=['NST 61']+[state(Rotation.from_rotvec(axis*np.deg2rad(a)).as_matrix()) for a in angles]+['POS '+' '.join('%.12f'%x for x in pivot)+' 0 0 0 1'];n.insert(-1,'NCH '+str(len(names)));n[-1:-1]=['CLD "'+name+'"' for name in names];ns.append(n)
  sealname='Su30NozzleJointSeal_'+str(side);p[sealname+'.srf']=seal(pivot).srf();ns.append(node(sealname,sealname+'.srf'))
  rows.append(dict(side=side,pivot=pivot.tolist(),children=names))
 assert all(p[k]==v for k,v in original.items());changed=[dnm.name(a) for a,b in zip(ns,before) if a!=b];assert len(changed)==70
 out.parent.mkdir(exist_ok=True,parents=True);tmp=out.with_suffix('.tmp.dnm');dnm.write(tmp,p,ns);tmp.write_bytes(tmp.read_bytes().replace(b'\r\n',b'\n'));tmp.replace(out)
 result=dict(baseline_sha256=sha(baseline.read_bytes()),model_sha256=sha(out.read_bytes()),original_packs_exact=len(original),modified_original_nodes=changed,new_nodes=[dnm.name(n) for n in ns[len(before):]],gimbals=rows,neutral_rest_position_error_m_below=1e-10,original_opening_states_and_axes_exact=True,cant_deg=32,limit_deg=15)
 out.with_suffix('.audit.json').write_text(json.dumps(result,indent=2));print(out,result['model_sha256'])
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--baseline',type=Path,required=True);a.add_argument('--output',type=Path,required=True);v=a.parse_args();run(v.baseline,v.output)
