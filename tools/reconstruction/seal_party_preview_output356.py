from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
assert (D/'closed-final/capture-complete.json').exists() and not (D/'seal.json').exists()
members=[]
for p in sorted(D.rglob('*')):
    if p.is_file():
        b=p.read_bytes();members.append({'path':p.relative_to(D).as_posix(),'bytes':len(b),'sha256':sha(b)})
for m in members:
    b=(D/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256'],m['path']
v={'round':356,'scope':'Source-only implementation/custody; no product execution','member_count':len(members),'member_bytes':sum(m['bytes'] for m in members),'credits':{'method':0,'opcode':0,'format':0,'route':0},'members':members}
b=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8');(D/'seal.json').write_bytes(b);assert (D/'seal.json').read_bytes()==b
helpers=[]
for m in members:
    if m['path'].endswith('.py'):
        raw=(D/m['path']).read_bytes();assert b'\r' not in raw and not raw.startswith(b'\xef\xbb\xbf')
        helpers.append(m)
print(json.dumps({'member_count':len(members),'member_bytes':v['member_bytes'],'seal_bytes':len(b),'seal_sha256':sha(b),'helpers':helpers}))
