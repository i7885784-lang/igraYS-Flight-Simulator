from pathlib import Path
import sys,hashlib,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'su30sm-natural-pass/model-source'))
import dnm
src,dst=map(Path,sys.argv[1:3]);before=src.read_bytes();assert hashlib.sha256(before).hexdigest()=='c71a27b0897b01f28528e4975f3abf1770e577223925b16684bcdf0d2ec823b0'
p,n=dnm.read(src);targets={dnm.fil(x) for x in n if dnm.name(x) in ['GearWell_Left','GearWell_Right','GearWell_Nose']};assert len(targets)==3
# Preserve every original line except C records in precisely three packed SRFs.
lines=before.decode().splitlines(keepends=True);i=2;counts={}
while i<len(lines) and lines[i].startswith('PCK '):
 _,name,count=lines[i].split();count=int(count)
 if name in targets:
  counts[name]=0
  for k in range(i+1,i+1+count):
   if lines[k].startswith('C '):lines[k]='C 0 0 0'+ ('\r\n' if lines[k].endswith('\r\n') else '\n');counts[name]+=1
 i+=count+1
assert set(counts)==targets and all(counts.values());dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(''.join(lines).encode());q,nn=dnm.read(dst);assert nn==n
for name in p:
 assert [x for x in p[name] if not (name in targets and x.startswith('C '))]==[x for x in q[name] if not (name in targets and x.startswith('C '))]
a={'baseline_sha256':hashlib.sha256(before).hexdigest(),'model_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'changed_color_records':counts,'rgb':[0,0,0],'all_other_lines_exact':True,'geometry_normals_indices_nodes_animations_exact':True};dst.with_suffix('.json').write_text(json.dumps(a,indent=2));print(json.dumps(a,indent=2))
