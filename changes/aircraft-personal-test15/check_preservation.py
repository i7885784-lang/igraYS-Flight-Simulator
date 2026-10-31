from pathlib import Path
import sys,json
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));import dnm
checks={}
for kind,skin in [('su27','Hull'),('su34','SourceAirframe'),('mig29','Hull'),('su47','Hull'),('su57','Su57Hull')]:
 bp,bns=dnm.read(r/'baseline'/f'{kind}.dnm');p,ns=dnm.read(r/'runtime/aircraft'/f'{kind}.dnm');lu={dnm.name(n):n for n in ns};bl={dnm.name(n):n for n in bns};assert p[dnm.fil(lu[skin])]==bp[dnm.fil(bl[skin])],kind
 changes=[]
 for n in bns:
  name=dnm.name(n);cl=dnm.cla(n);new=lu[name];mesh_change=bp[dnm.fil(n)]!=p[dnm.fil(new)];node_change=n!=new
  allowed_control=cl in (list(range(220,230))+[211,212] if kind in ['su27','mig29'] else range(240,252) if kind=='su34' else [])
  helpers=name.startswith('ConformalMainBayLiner') if kind=='su27' else name in ['MainBayOuterWalls','MainBayInnerLiner'] if kind=='mig29' else name in ['IntakeBacks','InnerFuselageSeal','OpaqueInternalHull'] if kind=='su47' else False
  assert not mesh_change or allowed_control or helpers,(kind,name,'unexpected mesh change')
  special_node=(kind=='su34' and name.startswith('OriginalSideDoor') and name.endswith('Wheel')) or (kind=='su47' and name.startswith('Slat'))
  assert not node_change or allowed_control or special_node,(kind,name,'unexpected node change')
  if mesh_change or node_change:changes.append(name)
  if allowed_control:
   a=dnm.mesh(bp[dnm.fil(n)]);b=dnm.mesh(p[dnm.fil(new)]);assert a.f==b.f,(kind,name,'material/topology changed')
 checks[kind]={'original_exterior_skin_exact':True,'old_nodes_all_retained':True,'changes':changes,'new_nodes':[dnm.name(n) for n in ns if dnm.name(n) not in bl]}
 if kind=='mig29':assert all(lu[dnm.name(n)]==n and p[dnm.fil(n)]==bp[dnm.fil(n)] for n in bns if dnm.cla(n)==210),'Existing main/nose rig changed'
(r/'preservation-checks.json').write_text(json.dumps({'passed':True,'models':checks},indent=2));print('PASS original exterior meshes, materials, gear and nozzle preservation')
