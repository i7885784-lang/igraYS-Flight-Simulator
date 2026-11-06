"""Seal both intake air cavities; only the two artificial IntakeDuct packs change."""
from pathlib import Path
import sys,json,hashlib,math,numpy as np
import shapely
from shapely.geometry import LineString,Point,Polygon
from shapely.ops import unary_union,polygonize
r=Path(__file__).parent;sys.path.insert(0,str(r/'model-source'));from common import *
base=r/'baseline/su30sm.dnm';assert hashlib.sha256(base.read_bytes()).hexdigest()=='ea3d9ced56a637c5a81c75b4acd2641f35902397149e72b495cfebe5196f0a53'
p,ns=dnm.read(base);old={k:list(v) for k,v in p.items()};lu={dnm.name(n):n for n in ns};n=lu['Fuselage_0_4'];source=dnm.mesh(p[dnm.fil(n)]);R,t=transform(n,0);P=np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);v=np.array(source.v)@R.T+t+P;tri=np.array([v[[ids[0],ids[j],ids[j+1]]] for ids,c,b in source.f for j in range(1,len(ids)-1)]);sections=[];audit={};Z=np.linspace(.65,.12,12);raw={}
for z in Z:
 lines=[];candidates=tri[(tri[:,:,2].min(1)<z)&(tri[:,:,2].max(1)>z)]
 for q in candidates:
  pts=[]
  for a,b in zip(q,np.roll(q,-1,axis=0)):
   da,db=a[2]-z,b[2]-z
   if da*db<0:pts.append((a+(b-a)*da/(da-db))[:2])
  if len(pts)==2 and np.linalg.norm(pts[0]-pts[1])>1e-8:lines.append(LineString(np.round(pts,7)))
 raw[float(z)]=list(polygonize(unary_union(lines)))
for side in [-1,1]:
 centre=np.array([side*1.1,-.55]);polys=[];angles=[]
 for z in Z:
  matches=[q for q in raw[float(z)] if q.covers(Point(centre))];assert matches,('No enclosed AIR section',side,z)
  # Keep the individual air cell. Unioning all cells would fill solid shell and destroy the inner contour.
  air=min(matches,key=lambda q:q.area);safe=air.buffer(-.005,join_style=2);assert safe.geom_type=='Polygon' and not safe.interiors and safe.covers(Point(centre));polys.append(safe)
  for x,y in list(safe.exterior.coords)[:-1]:angles.append(math.atan2(y-centre[1],x-centre[0])%(2*math.pi))
 angles=np.unique(np.round(angles,12));rings=[]
 for z,poly in zip(Z,polys):
  ring=[]
  for theta in angles:
   d=np.array([math.cos(theta),math.sin(theta)]);hits=poly.boundary.intersection(LineString([centre,centre+3*d]));points=[np.array(q.coords[0]) for q in shapely.get_parts(hits) if q.geom_type=='Point' and (np.array(q.coords[0])-centre)@d>0];assert points
   xy=min(points,key=lambda q:np.linalg.norm(q-centre));ring.append([*xy,float(z)])
  ring=np.array(ring);approx=Polygon(ring[:,:2]);error=approx.symmetric_difference(poly).area;assert error<1e-8,('Non-star contour or missing corner',side,z,error)
  rings.append(ring);sections.append({'side':side,'z':float(z),'air_polygon_wkt':poly.wkt,'ring':ring.tolist(),'area_error_m2':error})
 m=Mesh();N=len(angles)
 for a,b in zip(rings,rings[1:]):
  for k in range(N):
   j=(k+1)%N
   for q in [np.array([a[k],a[j],b[j]]),np.array([a[k],b[j],b[k]])]:
    normal=np.cross(q[1]-q[0],q[2]-q[0]);target=np.r_[centre-q[:,:2].mean(0),0]
    if normal@target<0:q=q[::-1]
    m.face(q,(25,30,33),False)
 rear=Polygon(rings[-1][:,:2]);count=0
 for t in shapely.get_parts(shapely.constrained_delaunay_triangles(rear)):
  xy=np.array(t.exterior.coords)[:3];q=np.c_[xy,np.full(3,Z[-1])]
  if np.cross(q[1]-q[0],q[2]-q[0])[2]<0:q=q[::-1]
  if np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))<1e-12:continue
  m.face(q,(25,30,33),False);count+=1
 # Drop faces collapsed only by six-decimal SRF serialization.
 vv=np.round(m.v,6);m.f=[(ids,c,b) for ids,c,b in m.f if np.linalg.norm(np.cross(vv[ids[1]]-vv[ids[0]],vv[ids[2]]-vv[ids[0]]))>1e-12]
 name='IntakeDuct_'+str(side)+'.srf';p[name]=m.srf();audit[name]={'front_z_m':float(Z[0]),'rear_z_m':float(Z[-1]),'depth_m':float(Z[0]-Z[-1]),'section_count':len(Z),'common_angles_including_all_measured_corners':N,'inward_liner_offset_m':.005,'rear_closed_triangles':count,'faces':len(m.f),'matte_rgb':[25,30,33],'emissive':False,'actual_air_cell_not_union_of_solid_and_air':True}
changed=[k for k in p if p[k]!=old[k]];assert set(changed)=={'IntakeDuct_-1.srf','IntakeDuct_1.srf'}
out=r/'runtime/aircraft/su30sm.dnm';dnm.write(out,p,ns);report={'model_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'changed_packs':changed,'all_nodes_states_parents_exact':True,'all_other_packs_including_gear_and_original_engine_exact':True,'inserts':audit};(r/'repair-audit.json').write_text(json.dumps(report,indent=2));(r/'sections.json').write_text(json.dumps(sections,indent=2));print(json.dumps(report,indent=2))
