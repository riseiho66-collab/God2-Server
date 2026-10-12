from pathlib import Path
import json,hashlib
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012');D=A/'round351-blacklist-live-owner-host-implementation'
p=Path('C:/Users/risei/Desktop/God2/God2-Server/src/core/Application.cpp');b=p.read_bytes();v=b;edits=[]
for old,new in [
 ('                                    if(!change || !source_current())return {};\n','                                    if(!source_current())return {};\n                                    if(!change){++i;continue;} // Preserve old valid rejection: empty reply, continue records.\n'),
 ('                        ready(session); // Mark only after the genuine ready hook succeeds.\n                        if(!session.closing() && session.account_id && session.character_id)',
  '                        ready(session); // Mark only after the genuine ready hook succeeds.\n                        if(lifetime->load() && !session.closing() && session.account_id && session.character_id)')]:
 old=old.encode();new=new.encode();assert v.count(old)==1;v=v.replace(old,new,1);edits.append((old,new))
inverse=v
for old,new in reversed(edits):assert inverse.count(new)==1;inverse=inverse.replace(new,old,1)
assert inverse==b
with (D/'Application.before-reject-ready-correction.cpp').open('xb') as f:f.write(b)
with (D/'Application.reject-ready-corrected.cpp').open('xb') as f:f.write(v)
with (D/'reject-ready-correction.json').open('x',encoding='utf-8',newline='\n') as f:
 json.dump(dict(before_bytes=len(b),before_sha256=hashlib.sha256(b).hexdigest(),after_bytes=len(v),after_sha256=hashlib.sha256(v).hexdigest(),inverse_exact=True,edits=[dict(old=o.decode(),new=n.decode()) for o,n in edits]),f,indent=2);f.write('\n')
assert p.read_bytes()==b;p.write_bytes(v)
print(json.dumps(dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest(),inverse_exact=True)))
