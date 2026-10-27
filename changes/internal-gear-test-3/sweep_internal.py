exec((__import__('pathlib').Path(__file__).resolve().parent/'audit_internal.py').read_text().split('report={}')[0])
sweeps={}
for kind in ['su27','mig29']:
 su=kind=='su27';root=lab/'model-source/upstream'/kind;ac=AC(root/('Su-27.ac' if su else 'mesh_airframe.ac'))
 for o in ac.objects:o['v']=(np.array(o['v'])+np.array([0,0,10 if su else 8.05])).tolist()
 env=reference(ac,su);packs,nodes=dnm.read(lab/'runtime/aircraft'/(kind+'.dnm'));meta=json.load(open(lab/'model-source/model-stats.json'))[kind]
 for n in nodes:
  name=dnm.name(n)
  if not name.startswith(('Gear_','AxleFork','UpperHingeLink','NoseDragBrace','NoseTorqueLink')):continue
  title='L' if 'Main_Left' in name or '_L_' in name or name.endswith('ForkL') or name.endswith('LinkL') else 'R' if 'Main_Right' in name or '_R_' in name or name.endswith('ForkR') or name.endswith('LinkR') else 'N'
  x0,x1,z0,z1=meta['bays'][title]['rect'];roof=meta['bays'][title]['interior_roof_cap'];v=np.array(dnm.mesh(packs[dnm.fil(n)]).v)
  worst=0;roofbad=0
  for state,s in enumerate(x.split()[1:] for x in n if x.startswith('STA ')):
   t=np.array(s[:3],float);h,p,b=np.array(s[3:6],float)*math.pi/32768;R=Rotation.from_euler('YXZ',[-h,-p,b]).as_matrix();q=v@R.T+t;lo,hi,dist=env.bounds(q)
   skin=(abs(q[:,1]-lo)<.04)&(q[:,1]<hi-.02);out=(q[:,0]<x0)|(q[:,0]>x1)|(q[:,2]<z0)|(q[:,2]>z1);worst=max(worst,int((skin&out).sum()))
   if state==0:roofbad=float(np.maximum(q[:,1]-np.minimum(hi-.012,roof),0).max())
  assert worst==0 and roofbad<.02,(kind,name,worst,roofbad)
  sweeps[kind+':'+name]={'poses':21,'skin_crossing_outside_aperture':worst,'stowed_roof_error_m':round(roofbad,5)}
(lab/'checks/sweep-audit.json').write_text(json.dumps({'passed':True,'assemblies':sweeps},indent=2))
print('PASS: 21 existing poses, apertures and internal roof clearance')
