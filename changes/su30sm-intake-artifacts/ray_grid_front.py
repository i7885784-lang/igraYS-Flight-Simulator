from pathlib import Path
import sys,numpy as np,collections,json
r=Path(__file__).parent;sys.path.insert(0,str(r));from model import Model
m=Model(r/'baseline/su30sm.dnm');m.sample(1);targets={}
for name,(v,f) in m.meshes.items():
 if name.startswith(('Su30Plume','Su30Dry')):continue
 R,t=m.poses[name];q=(v@R.T+t)[f]
 if q[:,:,2].max()< -3.14 or q[:,:,2].min()> 0.01 or q[:,:,1].min()>.1:continue
 targets[name]=q
out={}
for sign in [-1,1]:
 rows=[]
 for dx in np.linspace(-.27,.27,7):
  for dy in np.linspace(-.29,.29,7):
   O=np.array([sign*1.18+dx,-.54+dy,0.0]);D=np.array([0.,0,-1]);hits=[]
   for name,q in targets.items():
    a=q[:,0];e=q[:,1]-a;j=q[:,2]-a;h=np.cross(D,j);det=np.einsum('ij,ij->i',e,h);ok=abs(det)>1e-12;inv=np.divide(1,det,out=np.zeros_like(det),where=ok);s=O-a;u=np.einsum('ij,ij->i',s,h)*inv;Q=np.cross(s,e);b=Q@D*inv;dist=np.einsum('ij,ij->i',j,Q)*inv;ids=np.flatnonzero(ok&(u>=0)&(b>=0)&(u+b<=1)&(dist>=0)&(dist<3.14))
    if len(ids):
     i=ids[np.argmin(dist[ids])];hits.append((float(dist[i]),name,int(i)))
   if hits:
    hit=min(hits);rows.append({'x':round(float(O[0]),4),'y':round(float(O[1]),4),'first_node':hit[1],'hit_z':round(-hit[0],5),'tri_index':hit[2]})
 out[str(sign)]={'first_hit_counts':dict(collections.Counter(t['first_node'] for t in rows)),'rays':rows};print(sign,out[str(sign)]['first_hit_counts'])
(r/'ray-grid-front-before.json').write_text(json.dumps(out,indent=2))
