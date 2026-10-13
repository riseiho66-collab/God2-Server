from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
assert (D/'qualified-final/capture-complete.json').exists() and not (D/'seal.json').exists()
members=[]
for p in sorted(D.rglob('*')):
    if p.is_file():
        b=p.read_bytes();members.append({'path':p.relative_to(D).as_posix(),'bytes':len(b),'sha256':sha(b)})
for m in members:
    b=(D/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
names=['capture_party_lifecycle_proposal358_corrected.py','seal_party_lifecycle_proposal358.py'];helpers=[]
for name in names:
    m=next(v for v in members if v['path']==name);b=(D/name).read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf');helpers.append(dict(m,successful_execution_count=1))
v={'round':358,'scope':'READONLY actual party source lifecycle proposal; no tracked change or product execution','member_count':int(len(members)),'member_bytes':int(sum(m['bytes'] for m in members)),'qualified_stage':'qualified-final','credits':{'method':0,'opcode':0,'format':0,'route':0},'successful_lf_helpers':helpers,'members':members}
b=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode();(D/'seal.json').write_bytes(b);assert (D/'seal.json').read_bytes()==b
for m in members:
    b=(D/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
print(json.dumps({'member_count':v['member_count'],'member_bytes':v['member_bytes'],'seal_bytes':(D/'seal.json').stat().st_size,'seal_sha256':sha((D/'seal.json').read_bytes()),'helpers':helpers}))
