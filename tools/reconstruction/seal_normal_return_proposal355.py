"""Seal retained source proposal and additive party review individually."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
D=O/'seal.json'
def sha(b):return hashlib.sha256(b).hexdigest()
if D.exists():raise RuntimeError('Immutable existing seal')
rows=[]
for p in sorted(O.rglob('*')):
    if p.is_file():
        b=p.read_bytes();rows.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
helpers=[]
for n in ['capture_normal_return_proposal355.py','capture_party_source_review355.py','seal_normal_return_proposal355.py']:
    b=(O/n).read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf')
    helpers.append(dict(name=n,bytes=len(b),sha256=sha(b)))
v=dict(round=355,scope='Static-source proposal plus additive root-requested party permission review; no tracked edits',member_count=len(rows),member_bytes=sum(x['bytes'] for x in rows),credits=dict(method=0,opcode=0,format=0,route=0),members=rows)
b=(json.dumps(v,indent=2)+'\n').encode()
with D.open('xb') as f:f.write(b)
seal=json.loads(D.read_bytes())
for x in seal['members']:
    raw=(O/x['path']).read_bytes();assert len(raw)==x['bytes'] and sha(raw)==x['sha256'],x['path']
assert seal['member_count']==len(seal['members']) and seal['member_bytes']==sum(x['bytes'] for x in seal['members'])
print(json.dumps(dict(seal=str(D),seal_bytes=len(b),seal_sha256=sha(b),member_count=seal['member_count'],member_bytes=seal['member_bytes'],successful_lf_helpers=helpers),indent=2))
