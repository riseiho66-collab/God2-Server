"""Immutable member-derived static-source seal, with individual readback."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
D=O/'seal.json'
def sha(b):return hashlib.sha256(b).hexdigest()
if D.exists():raise RuntimeError('Do not overwrite seal')
members=[]
for p in sorted(O.rglob('*')):
    if p.is_file():
        b=p.read_bytes()
        members.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
helpers=[]
for n in ['capture_canonical_save_restore354.py','seal_canonical_save_restore354.py']:
    b=(O/n).read_bytes()
    assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf')
    helpers.append(dict(name=n,bytes=len(b),sha256=sha(b)))
assert (O/'REPORT.md').is_file() and (O/'capture-complete.json').is_file()
s=dict(schema='individual-member-sha256-source-seal-v1',round=354,member_count=len(members),member_bytes=sum(x['bytes'] for x in members),credits=dict(method=0,opcode=0,format=0,route=0),members=members)
b=(json.dumps(s,indent=2)+'\n').encode()
with D.open('xb') as f:f.write(b)
v=json.loads(D.read_bytes())
for x in v['members']:
    a=(O/x['path']).read_bytes()
    assert len(a)==x['bytes'] and sha(a)==x['sha256'],x['path']
assert v['member_count']==len(v['members']) and v['member_bytes']==sum(x['bytes'] for x in v['members'])
print(json.dumps(dict(seal=str(D),seal_bytes=len(b),seal_sha256=sha(b),member_count=v['member_count'],member_bytes=v['member_bytes'],successful_lf_helpers=helpers),indent=2))
