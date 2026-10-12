from pathlib import Path
import hashlib,json
I=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round353-normal-original-response-transport-implementation')
h=lambda b:hashlib.sha256(b).hexdigest()
assert not (I/'seal.json').exists()
refs=json.loads((I/'source-references.json').read_text())
for r in refs:
 b=Path(r['actual_path']).read_bytes();assert b==(I/r['retained']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256']
members=[]
for p in sorted(I.rglob('*')):
 if p.is_file():
  b=p.read_bytes();members.append({'path':p.relative_to(I).as_posix(),'bytes':len(b),'sha256':h(b)})
seal={'kind':'immutable-individual-member-seal','excludes':['seal.json'],'member_count':len(members),'member_bytes':sum(r['bytes'] for r in members),'members':members}
b=(json.dumps(seal,indent=2)+'\n').encode();(I/'seal.json').write_bytes(b)
read=json.loads((I/'seal.json').read_text());assert len(read['members'])==read['member_count']
assert sum(r['bytes'] for r in read['members'])==read['member_bytes']
for r in read['members']:
 q=(I/r['path']).read_bytes();assert len(q)==r['bytes'] and h(q)==r['sha256']
assert set(p.relative_to(I).as_posix() for p in I.rglob('*') if p.is_file())==set(r['path'] for r in read['members'])|{'seal.json'}
print(json.dumps({'verdict':'PASS','seal_sha256':h(b),'seal_bytes':len(b),'members':read['member_count'],'member_bytes':read['member_bytes'],'current_references':len(refs),'current_reference_bytes':sum(r['bytes'] for r in refs),'report_sha256':h((I/'REPORT.md').read_bytes())}))
