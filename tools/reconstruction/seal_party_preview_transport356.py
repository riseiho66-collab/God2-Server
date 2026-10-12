from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
assert not (D/'seal.json').exists()
assert (D/'complete-final/capture-complete.json').exists()
members=[]
for p in sorted(D.rglob('*')):
    if p.is_file():
        b=p.read_bytes();members.append({'path':p.relative_to(D).as_posix(),'bytes':len(b),'sha256':sha(b)})
for m in members:
    b=(D/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
out={'round':356,'scope':'READONLY source plan with additive preserved capture failures; no tracked mutation or target execution','member_count':len(members),'member_bytes':sum(m['bytes'] for m in members),'credits':{'method':0,'opcode':0,'format':0,'route':0},'members':members}
b=(json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode('utf-8');(D/'seal.json').write_bytes(b)
assert (D/'seal.json').read_bytes()==b
print(json.dumps({'seal_sha256':sha(b),'seal_bytes':len(b),'member_count':len(members),'member_bytes':out['member_bytes'],'helpers':[{'path':m['path'],'bytes':m['bytes'],'sha256':m['sha256']} for m in members if m['path'] in ['capture_party_preview_transport356_success.py','seal_party_preview_transport356.py']]}))
