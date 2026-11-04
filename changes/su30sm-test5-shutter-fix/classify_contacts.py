from intersection_helpers import *
from model import Model
from collections import Counter
rows=json.loads((r/'validation.json').read_text())['animation']['contacts'];out=[]
for item in rows:
 g=item['g'];a=item['a'];b=item['b'];m.sample(g);res=fcl.CollisionResult();fcl.collide(m.objects[a],m.objects[b],fcl.CollisionRequest(num_max_contacts=3000,enable_contact=True),res);proper=[];touch=0
 for c in res.contacts:
  va,fa=m.meshes[a];vb,fb=m.meshes[b];R,t=m.poses[a];S,v=m.poses[b];A=va[fa[c.b1]]@R.T+t;B=vb[fb[c.b2]]@S.T+v;seg=segment(A,B)
  if not seg:continue
  aa,bb=np.array(seg);mid=(aa+bb)/2;L=np.linalg.norm(aa-bb);d=min(edge_distance(mid,A),edge_distance(mid,B))
  if L>1e-5 and d>1e-5:proper.append({'length':float(L),'interior':float(d),'segment':seg})
  else:touch+=1
 proper.sort(key=lambda p:p['interior'],reverse=True);out.append({**item,'fcl_contacts':len(res.contacts),'proper_count':len(proper),'max':proper[:1],'boundary_or_numeric':touch})
(r/'classified-contacts.json').write_text(json.dumps(out,indent=2))
for pair in sorted(set((x['a'],x['b']) for x in out)):
 rr=[x for x in out if (x['a'],x['b'])==pair];pr=[x for x in rr if x['proper_count']];print(pair,'proper poses',[x['g'] for x in pr],'worst',max((x['max'][0]['interior'] for x in pr),default=0),flush=True)
