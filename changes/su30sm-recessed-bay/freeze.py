"""Freeze the verified five-pack change, storing F4 as a small exact face delta."""
from pathlib import Path
import sys,json,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'changes/su30sm-local-skin/model-source'));import dnm
sha=lambda b:hashlib.sha256(b).hexdigest()
def split(ls):
 first=ls.index('F');i=first;faces=[]
 while i<len(ls) and ls[i]=='F':
  end=ls.index('E',i)+1;faces.append(ls[i:end]);i=end
 return ls[:first],faces,ls[i:]
def apply_delta(old,delta):
 assert sha(('\n'.join(old)+'\n').encode())==delta['before_sha256'];prefix,faces,end=split(old);replacements={int(k):v for k,v in delta['replacements'].items()};out=prefix+delta['append_vertices']+[s for i,block in enumerate(faces) for b in replacements.get(i,[block]) for s in b]+end
 assert sha(('\n'.join(out)+'\n').encode())==delta['after_sha256'];return out

def freeze(base,model,auditfile,out):
 out.mkdir(parents=True,exist_ok=True);a,an=dnm.read(base);b,bn=dnm.read(model);assert an==bn;audit=json.loads(auditfile.read_text());rows=[]
 for name,ls in b.items():
  if ls==a[name]:continue
  data=('\n'.join(ls)+'\n').encode();entry={'pack':name,'sha256':sha(data),'bytes':len(data)}
  if name=='Fuselage_0_4.srf':
   p0,f0,e0=split(a[name]);p1,f1,e1=split(ls);assert p1[:len(p0)]==p0 and e0==e1;nv0=sum(s.startswith('V ') for s in p0);newblocks=[bl for bl in f1 if min(map(int,next(s[2:] for s in bl if s.startswith('V ')).split()))>=nv0];repl={}
   for row in audit['internal_body_cut']['source_face_changes']:
    start,end=row['new_vertex_start'],row['new_vertex_end'];repl[str(row['source_face'])]=[bl for bl in newblocks if start<=min(map(int,next(s[2:] for s in bl if s.startswith('V ')).split()))<end]
   delta={'before_sha256':sha(('\n'.join(a[name])+'\n').encode()),'after_sha256':sha(data),'append_vertices':p1[len(p0):],'replacements':repl};assert apply_delta(a[name],delta)==ls;member='Fuselage_0_4.face-delta.json';payload=json.dumps(delta,separators=(',',':')).encode();entry.update(type='face-delta',payload_sha256=sha(payload))
  else:member=name;payload=data;entry['type']='srf'
  f=out/(member+'.zip');zi=zipfile.ZipInfo(member,(2026,11,14,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED
  with zipfile.ZipFile(f,'w') as z:z.writestr(zi,payload,compresslevel=9)
  entry.update(zip=f.name,member=member,zip_bytes=f.stat().st_size);rows.append(entry)
 meta={'baseline_sha256':sha(base.read_bytes()),'model_sha256':sha(model.read_bytes()),'patches':rows,'visual_check':'See reports/su30sm-recessed-bay/REPORT_RU.md for model-specific native Windows and Wine evidence'};(out/'metadata.json').write_text(json.dumps(meta,indent=2));print(json.dumps(rows,indent=2))
if __name__=='__main__':freeze(*map(Path,sys.argv[1:]))
