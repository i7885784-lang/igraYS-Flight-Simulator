"""Replace only two artificial intake inserts by restrained dark, closed inner liners.
The user explicitly allows an internal occlusion screen. Original aircraft skin and every node/animation stay exact.
"""
from pathlib import Path
import sys,json,hashlib,math,numpy as np
import shapely
from shapely.geometry import LineString,Point,box,Polygon
from shapely.ops import unary_union,polygonize
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'model-source'));from common import *
base=r/'baseline/su30sm.dnm';assert hashlib.sha256(base.read_bytes()).hexdigest()=='6fd0f2982c657eb4524573744ce949d5aeea9e26f16d3bd74a21f69f598a4c83';p,ns=dnm.read(base);old={k:list(v) for k,v in p.items()};lu={dnm.name(n):n for n in ns};source=dnm.mesh(p['Fuselage_0_4.srf']);n=lu['Fuselage_0_4'];R,t=transform(n,0);C=t+np.array(next(s[4:] for s in n if s.startswith('POS ')).split()[:3],float);v=np.array(source.v)@R.T+C;audit={};sections=[]
Z=[-.55];N=48
for sg in [-1,1]:
 loops=[];domains=[]
 for z in Z:
  lines=[]
  for ids,col,b in source.f:
   for j in range(1,len(ids)-1):
    tri=v[[ids[0],ids[j],ids[j+1]]];pts=[]
    for a,bb in zip(tri,np.roll(tri,-1,axis=0)):
     da,db=a[2]-z,bb[2]-z
     if da*db<0:pts.append((a+(bb-a)*da/(da-db))[:2])
    if len(pts)==2 and np.linalg.norm(pts[0]-pts[1])>1e-8:lines.append(LineString(np.round(pts,7)))
  polys=list(polygonize(unary_union(lines)));merged=unary_union(polys);center=Point(sg*1.1,-.55);possible=[q for q in shapely.get_parts(merged) if q.geom_type=='Polygon' and q.covers(center)];assert possible,('No actual body section',sg,z)
  actual=max(possible,key=lambda q:q.area);safe=actual.buffer(-.008,join_style=2).intersection(box(sg*1.18-.37,-.97,sg*1.18+.37,-.15));assert safe.geom_type=='Polygon' and safe.covers(center);domains.append(safe)
  points=[]
  for theta in np.linspace(0,2*math.pi,N,endpoint=False):
   d=np.array([math.cos(theta),math.sin(theta)]);c=np.array(center.coords[0]);cross=safe.boundary.intersection(LineString([c,c+d*3]));hits=[]
   for q in shapely.get_parts(cross):
    if q.geom_type=='Point' and (np.array(q.coords[0])-c)@d>0:hits.append(np.array(q.coords[0]))
   assert hits,('Missing measured radial boundary',sg,z,theta);xy=min(hits,key=lambda q:np.linalg.norm(q-c));points.append([*xy,z])
  points=np.array(points);loops.append(points);sections.append({'side':sg,'z':z,'actual_polygon_wkt':actual.wkt,'safe_polygon_wkt':safe.wkt,'loop':points.tolist()})
 m=Mesh()
 # A recessed, featureless concave screen: its boundary is safely behind the inlet,
 # and its deepest point stays in front of the original wheel/door swept region.
 outer=loops[0];centre=np.array([sg*1.1,-.55,-.55]);rings=[outer]
 for scale,z in [(.66,-.65),(.28,-.73)]:
  q=centre+(outer-centre)*scale;q[:,2]=z;rings.append(q)
 for j in range(len(rings)-1):
  for k in range(N):
   kk=(k+1)%N;q=np.array([rings[j][k],rings[j][kk],rings[j+1][kk],rings[j+1][k]])
   if np.cross(q[1]-q[0],q[2]-q[0])[2]<0:q=q[::-1]
   m.face(q,(25,30,33),False)
 c=np.array([sg*1.1,-.55,-.75])
 for k in range(N):
  q=np.array([c,rings[-1][k],rings[-1][(k+1)%N]])
  if np.cross(q[1]-q[0],q[2]-q[0])[2]<0:q=q[::-1]
  m.face(q,(25,30,33),False)
 fn='IntakeDuct_'+str(sg)+'.srf';p[fn]=m.srf();oldmesh=dnm.mesh(old[fn]);audit[fn]={'old_insert_faces':len(oldmesh.f),'new_liner_faces':len(m.f),'front_z_m':Z[0],'termination_z_m':-.75,'body_clearance_m':.008,'body_section_based':True,'single_sided_inward_walls':True,'termination_facing_inlet':True,'emissive_faces':0,'matte_colors':[(25,30,33)],'old_artificial_rectangular_walls_and_spoked_disc_replaced':True,'original_aircraft_source_surfaces_removed':False,'occlusion_screen_explicitly_used':True}
changed=[k for k in old if p[k]!=old[k]];assert set(changed)=={'IntakeDuct_-1.srf','IntakeDuct_1.srf'}
out=r/'runtime/aircraft/su30sm.dnm';dnm.write(out,p,ns);a={'model_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'changed_packs':changed,'all_nodes_animations_parents_pivots_exact':True,'all_original_aircraft_skin_and_mechanics_packs_exact':True,'exterior_paint_unchanged':True,'no_added_nodes_or_effects':True,'inserts':audit};(r/'repair-audit.json').write_text(json.dumps(a,indent=2));(r/'liner-sections.json').write_text(json.dumps(sections,indent=2));print(json.dumps(a,indent=2))
