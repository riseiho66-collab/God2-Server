from pathlib import Path
import hashlib,json
O=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round355-native-canonical-writer-source');h=lambda b:hashlib.sha256(b).hexdigest()
assert not (O/'seal.json').exists()
for x in json.loads((O/'native-inputs.json').read_text()):
 b=Path(x['path']).read_bytes();assert len(b)==x['bytes'] and h(b)==x['sha256']
rows=[]
for p in sorted(O.rglob('*')):
 if p.is_file():
  assert p.resolve().is_relative_to(O.resolve());b=p.read_bytes();rows.append({'path':p.relative_to(O).as_posix(),'bytes':len(b),'sha256':h(b)})
x={'kind':'immutable-individual-member-seal','member_count':len(rows),'member_bytes':sum(r['bytes'] for r in rows),'excludes':['seal.json'],'members':rows};b=(json.dumps(x,indent=2)+'\n').encode();(O/'seal.json').write_bytes(b)
y=json.loads((O/'seal.json').read_bytes());assert len(y['members'])==y['member_count'] and sum(r['bytes'] for r in y['members'])==y['member_bytes']
for r in y['members']:
 p=(O/r['path']).resolve();assert p.is_relative_to(O.resolve());t=p.read_bytes();assert len(t)==r['bytes'] and h(t)==r['sha256']
assert set(p.relative_to(O).as_posix() for p in O.rglob('*') if p.is_file())==set(r['path'] for r in y['members'])|{'seal.json'}
print(json.dumps({'verdict':'PASS','members':y['member_count'],'member_bytes':y['member_bytes'],'seal_bytes':len(b),'seal_sha256':h(b),'report_sha256':h((O/'REPORT.md').read_bytes())}))
