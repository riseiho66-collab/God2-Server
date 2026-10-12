from pathlib import Path
import json,hashlib,subprocess
S=Path('C:/Users/risei/Desktop/God2/God2-Server');A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013');D=A/'round355-party-detail-response-implementation'
HEAD='b934e539e9d0cb279e2d6b58678afdb7b555dcf9';sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def js(p,v):write(p,(json.dumps(v,indent=2)+'\n').encode())
edits=json.loads((D/'literal-edits-and-inverse.json').read_bytes());rows=[]
for rel in edits['modified_paths']:
 b=(S/rel).read_bytes();inverse=b
 for e in reversed(edits['edits']):
  if e['path']==rel:
   old=e['before'].encode();new=e['after'].encode();assert inverse.count(new)==1
   inverse=inverse.replace(new,old)
 assert inverse==(D/'before-v2'/rel).read_bytes()==(D/'before'/rel).read_bytes()==subprocess.check_output(['git','show',HEAD+':'+rel],cwd=S)
 write(D/'current'/rel,b);rows.append(dict(actual_path=(S/rel).as_posix(),retained='current/'+rel,bytes=len(b),sha256=sha(b),exact_inverse_HEAD=HEAD))
js(D/'source-references.json',rows)
deps=['src/net/Session.h','src/net/Session.cpp','src/core/Config.h','src/core/Config.cpp','src/game/NativeParty.h','src/protocol/TaiwanNativePartyMenu.h','docs/custom-designs.json']
frozen=[]
for rel in deps:
 b=(S/rel).read_bytes();assert b==subprocess.check_output(['git','show',HEAD+':'+rel],cwd=S)
 write(D/'frozen'/rel,b);frozen.append(dict(actual_path=(S/rel).as_posix(),retained='frozen/'+rel,bytes=len(b),sha256=sha(b)))
js(D/'frozen-dependency-references.json',frozen)
for name in ['capture_party_response_source355.py','prepare-party-helper-v2-source355.py']:write(D/'helpers'/name,(A/name).read_bytes())
print(json.dumps(dict(current_sources=len(rows),current_bytes=sum(r['bytes'] for r in rows),frozen_sources=len(frozen),frozen_bytes=sum(r['bytes'] for r in frozen),three_exact_inverses=True)))
