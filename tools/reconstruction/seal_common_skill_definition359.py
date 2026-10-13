from pathlib import Path
import json,hashlib
D=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round359-common-skill-definition-implementation')
H=lambda b:hashlib.sha256(b).hexdigest()
assert not (D/'seal.json').exists()
refs=json.loads((D/'source-references.json').read_text(encoding='utf-8'));assert len(refs)==12
for v in refs:
 b=Path(v['actual_path']).read_bytes();r=(D/v['retained']).resolve();assert r.is_relative_to(D.resolve())
 assert len(b)==v['bytes'] and H(b)==v['sha256'] and r.read_bytes()==b
# Add the sealer's once-success metadata before freezing every member.
meta=json.loads((D/'successful-LF-helper-metadata.json').read_text())
p=D/'seal_common_skill_definition359.py';b=p.read_bytes();assert b'\r\n' not in b and not b.startswith(b'\xef\xbb\xbf')
meta.append({'path':p.name,'bytes':len(b),'sha256':H(b),'successful_execution_count':1,'LF_no_BOM':True})
(D/'successful-LF-helper-metadata.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n')
members=[];seen=set();total=0
for p in sorted(D.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(D).as_posix();assert rel!='seal.json'
 assert p.resolve().is_relative_to(D.resolve());assert rel.casefold() not in seen;seen.add(rel.casefold())
 b=p.read_bytes();n=len(b);assert type(n)==int
 members.append({'path':rel,'bytes':n,'sha256':H(b)});total+=n
value={'schema':'god2-individual-member-seal-v1','status':'PASS','scope':'PHASE1 source-only common skill definition provider359; no product/SQL/codec/native/compiler/test execution','member_count':len(members),'total_bytes':total,'members':members}
(D/'seal.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
# Read back every individual member and derive totals, not declarations.
stored=json.loads((D/'seal.json').read_text());derived=0
for v in stored['members']:
 assert type(v['bytes'])==int
 p=(D/v['path']).resolve();assert p.is_relative_to(D.resolve());b=p.read_bytes()
 assert len(b)==v['bytes'] and H(b)==v['sha256'];derived+=len(b)
assert len(stored['members'])==stored['member_count'] and derived==stored['total_bytes']
for v in refs:
 b=Path(v['actual_path']).read_bytes();assert len(b)==v['bytes'] and H(b)==v['sha256']
print(json.dumps({'status':'PASS','members':len(members),'bytes':derived,'seal_bytes':(D/'seal.json').stat().st_size,'seal_sha256':H((D/'seal.json').read_bytes()),'source_count':len(refs),'source_bytes':sum(v['bytes'] for v in refs),'REPORT_sha256':H((D/'REPORT.md').read_bytes()),'helper_count':len(meta)}))

