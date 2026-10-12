from pathlib import Path
import hashlib,json
I=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round354-client-options-original-response-implementation');h=lambda b:hashlib.sha256(b).hexdigest()
assert not (I/'seal.json').exists()
refs=json.loads((I/'source-references.json').read_text());deps=json.loads((I/'dependency-source-references.json').read_text())
for r in refs+deps:
 b=Path(r['actual_path']).read_bytes();assert b==(I/r['retained']).read_bytes() and len(b)==r['bytes'] and h(b)==r['sha256']
members=[]
for p in sorted(I.rglob('*')):
 if p.is_file():
  b=p.read_bytes();members.append({'path':p.relative_to(I).as_posix(),'bytes':len(b),'sha256':h(b)})
x={'kind':'immutable-individual-member-seal','excludes':['seal.json'],'member_count':len(members),'member_bytes':sum(r['bytes'] for r in members),'members':members};b=(json.dumps(x,indent=2)+'\n').encode();(I/'seal.json').write_bytes(b)
y=json.loads((I/'seal.json').read_bytes());assert y['member_count']==len(y['members']) and y['member_bytes']==sum(r['bytes'] for r in y['members'])
for r in y['members']:
 t=(I/r['path']).read_bytes();assert len(t)==r['bytes'] and h(t)==r['sha256']
assert set(p.relative_to(I).as_posix() for p in I.rglob('*') if p.is_file())==set(r['path'] for r in y['members'])|{'seal.json'}
print(json.dumps({'verdict':'PASS','members':y['member_count'],'member_bytes':y['member_bytes'],'seal_bytes':len(b),'seal_sha256':h(b),'current_refs':len(refs),'current_bytes':sum(r['bytes'] for r in refs),'report_sha256':h((I/'REPORT.md').read_bytes())}))
