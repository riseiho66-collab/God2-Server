from pathlib import Path
import hashlib,json
O=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round352-blacklist-submitted-chain-source-order-review')
assert not (O/'seal.json').exists()
h=lambda b:hashlib.sha256(b).hexdigest()
members=[]
for p in sorted(O.rglob('*')):
 if p.is_file():
  b=p.read_bytes();members.append({'path':p.relative_to(O).as_posix(),'bytes':len(b),'sha256':h(b)})
seal={'schema':'immutable-individual-member-seal-v1','scope':'ROUND352_HISTORICAL_SOURCE_ORDER_FOUNDATION_ONLY','member_count':len(members),'member_bytes':sum(x['bytes'] for x in members),'total_bytes':sum(x['bytes'] for x in members),'members':members,'excludes':['seal.json']}
b=(json.dumps(seal,ensure_ascii=False,indent=2)+'\n').encode();(O/'seal.json').write_bytes(b)
for r in members:
 b=(O/r['path']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256']
print(json.dumps({'member_count':len(members),'member_bytes':seal['member_bytes'],'seal_sha256':h((O/'seal.json').read_bytes()),'report_bytes':(O/'REPORT.md').stat().st_size,'report_sha256':h((O/'REPORT.md').read_bytes())}))
