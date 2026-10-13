from pathlib import Path
import json,hashlib
D=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round360-common-owner-skill-definition-implementation')
H=lambda b:hashlib.sha256(b).hexdigest()
assert not (D/'seal.json').exists()
refs=json.loads((D/'source-references.json').read_text(encoding='utf-8'));assert len(refs)==6
for v in refs:
 b=Path(v['actual_path']).read_bytes();p=(D/v['retained']).resolve()
 assert p.is_relative_to(D.resolve()) and p.read_bytes()==b and len(b)==v['bytes'] and H(b)==v['sha256']
meta=json.loads((D/'successful-LF-helper-metadata.json').read_text())
p=D/'seal_common_owner_skill_definition360.py';b=p.read_bytes()
assert b.endswith(b'\n') and not b.endswith(b'\n\n') and b'\r\n' not in b and not b.startswith(b'\xef\xbb\xbf')
meta.append({'path':p.name,'actual_executed_path':str(p).replace('\\','/'),'bytes':len(b),'sha256':H(b),'successful_execution_count':1,'LF_no_BOM':True,'single_final_LF':True})
(D/'successful-LF-helper-metadata.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n')
members=[];seen=set();total=0
for p in sorted(D.rglob('*')):
 if not p.is_file():continue
 path=p.relative_to(D).as_posix();assert path!='seal.json'
 assert p.resolve().is_relative_to(D.resolve()) and path.casefold() not in seen;seen.add(path.casefold())
 b=p.read_bytes();n=len(b);assert type(n)==int
 members.append({'path':path,'bytes':n,'sha256':H(b)});total+=n
value={'schema':'god2-individual-member-seal-v1','status':'PASS','scope':'PHASE1 static common owner-skill data integration360; no product/native/API/parser/codec/SQL/build/test execution','member_count':len(members),'total_bytes':total,'members':members}
(D/'seal.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
v=json.loads((D/'seal.json').read_text());derived=0
for m in v['members']:
 assert type(m['bytes'])==int and m['bytes']>=0
 p=(D/m['path']).resolve();assert p.is_relative_to(D.resolve());b=p.read_bytes()
 assert len(b)==m['bytes'] and H(b)==m['sha256'];derived+=len(b)
assert len(v['members'])==v['member_count'] and derived==v['total_bytes']
for v in refs:
 b=Path(v['actual_path']).read_bytes();assert len(b)==v['bytes'] and H(b)==v['sha256']
print(json.dumps({'status':'PASS','member_count':len(members),'member_bytes':derived,'seal_bytes':(D/'seal.json').stat().st_size,'seal_sha256':H((D/'seal.json').read_bytes()),'source_count':6,'source_bytes':sum(v['bytes'] for v in refs),'REPORT_bytes':(D/'REPORT.md').stat().st_size,'REPORT_sha256':H((D/'REPORT.md').read_bytes()),'final_public_helpers':[v for v in meta if v['path'] in ['capture_common_owner_skill_definition360_v2.py','seal_common_owner_skill_definition360.py']]}))
