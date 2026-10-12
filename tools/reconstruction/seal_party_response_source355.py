from pathlib import Path
import hashlib,json
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'round355-party-detail-response-implementation';sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
write(D/'helpers'/Path(__file__).name,Path(__file__).read_bytes())
members=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  b=p.read_bytes();members.append(dict(path=p.relative_to(D).as_posix(),bytes=len(b),sha256=sha(b)))
seal=dict(member_count=len(members),member_bytes=sum(r['bytes'] for r in members),members=members)
write(D/'seal.json',(json.dumps(seal,indent=2)+'\n').encode())
for r in members:
 p=D/r['path'];b=p.read_bytes();assert p.resolve().is_relative_to(D.resolve()) and len(b)==r['bytes'] and sha(b)==r['sha256'] and type(r['bytes']) is int
print(json.dumps(dict(members=seal['member_count'],member_bytes=seal['member_bytes'],seal_sha256=sha((D/'seal.json').read_bytes()))))
