from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
assert (D/'capture-complete.json').exists() and not (D/'seal.json').exists()
members=[]
for p in sorted(D.rglob('*')):
    if p.is_file():
        b=p.read_bytes();members.append({'path':p.relative_to(D).as_posix(),'bytes':len(b),'sha256':sha(b)})
for m in members:
    b=(D/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
names=['apply_party_callback_admission357.py','preserve_unobserved_callback357.py','preserve_split_callback357_lf_corrected.py','reject_committed_watch_failure357.py','reject_committed_peer_watch_failure357_lf_corrected.py','capture_party_callback_admission357.py','seal_party_callback_admission357.py']
helpers=[]
for name in names:
    m=next(v for v in members if v['path']==name);b=(D/name).read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf');helpers.append(dict(m,successful_execution_count=1))
v={'round':357,'scope':'Actual whole-callback admission source implementation; no product execution','member_count':int(len(members)),'member_bytes':int(sum(m['bytes'] for m in members)),'credits':{'method':0,'opcode':0,'format':0,'route':0},'successful_lf_helpers':helpers,'members':members}
b=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode();(D/'seal.json').write_bytes(b);assert (D/'seal.json').read_bytes()==b
for m in members:
    b=(D/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
print(json.dumps({'member_count':v['member_count'],'member_bytes':v['member_bytes'],'seal_bytes':(D/'seal.json').stat().st_size,'seal_sha256':sha((D/'seal.json').read_bytes()),'successful_lf_helpers':helpers}))
