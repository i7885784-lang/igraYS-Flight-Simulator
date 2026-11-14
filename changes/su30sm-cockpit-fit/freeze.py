from pathlib import Path
import sys,json,zipfile
from apply import dnm,SHA
base,cpbase,candidate,out=map(Path,sys.argv[1:5]);p,ns=dnm.read(base);cp,cn=dnm.read(cpbase);p2,ns2=dnm.read(candidate/'su30sm.dnm');cp2,cn2=dnm.read(candidate/'su30smcockpit.dnm');assert ns==ns2 and cn==cn2;assert [k for k in p if p[k]!=p2[k]]==['Su30Interior.srf'];assert [k for k in cp if cp[k]!=cp2[k]]==['Su30Interior.srf'];assert p2['Su30Interior.srf']==cp2['Su30Interior.srf'];data=('\n'.join(p2['Su30Interior.srf'])+'\n').encode();out.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(out/'Su30Interior.srf.zip','w',zipfile.ZIP_DEFLATED) as z:z.writestr('Su30Interior.srf',data)
meta={'interior_sha256':SHA(data),'changed_packs':['Su30Interior.srf'],'all_nodes_unchanged':True,'models':{name:{'baseline_sha256':SHA(source.read_bytes()),'sha256':SHA((candidate/name).read_bytes())} for name,source in [('su30sm.dnm',base),('su30smcockpit.dnm',cpbase)]}};(out/'metadata.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))
