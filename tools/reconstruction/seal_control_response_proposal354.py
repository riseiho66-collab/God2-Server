from pathlib import Path
import hashlib,json
O=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round354-normal-control-response-custody-proposal');h=lambda b:hashlib.sha256(b).hexdigest()
assert not (O/'seal.json').exists()
for r in json.loads((O/'source-references.json').read_text()):
 b=(O/r['retained']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256'] and Path(r['actual_path']).read_bytes()==b
members=[]
for p in sorted(O.rglob('*')):
 if p.is_file():
  b=p.read_bytes();members.append({'path':p.relative_to(O).as_posix(),'bytes':len(b),'sha256':h(b)})
x={'member_count':len(members),'member_bytes':sum(m['bytes'] for m in members),'excludes':['seal.json'],'members':members};b=(json.dumps(x,indent=2)+'\n').encode();(O/'seal.json').write_bytes(b)
for r in json.loads(b)['members']:
 t=(O/r['path']).read_bytes();assert len(t)==r['bytes'] and h(t)==r['sha256']
print(json.dumps({'members':x['member_count'],'bytes':x['member_bytes'],'seal_sha256':h(b)}))
