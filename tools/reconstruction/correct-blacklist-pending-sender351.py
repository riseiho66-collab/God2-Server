from pathlib import Path
import json,hashlib
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012')
D=A/'round351-blacklist-live-owner-host-implementation'
p=Path('C:/Users/risei/Desktop/God2/God2-Server/src/core/Application.cpp')
b=p.read_bytes()
old=b'                                    const auto source=blacklist_replays.at(session.id()); // Own exact map inputs before SQL.\n'
assert b.count(old)==1
new=old+b'''                                    if(source.live_pending) {
                                        // An actual incoming delta has not settled; do not commit a competing sender operation.
                                        auto& now=blacklist_replays.at(session.id());now.live_disabled=true;
                                        retire_blacklist_output(now);session.close();return {};
                                    }
'''
v=b.replace(old,new,1);assert v.replace(new,old,1)==b
with (D/'Application.before-pending-sender-correction.cpp').open('xb') as f:f.write(b)
with (D/'Application.pending-sender-corrected.cpp').open('xb') as f:f.write(v)
with (D/'pending-sender-correction.json').open('x',encoding='utf-8',newline='\n') as f:
 json.dump(dict(before_bytes=len(b),before_sha256=hashlib.sha256(b).hexdigest(),after_bytes=len(v),after_sha256=hashlib.sha256(v).hexdigest(),inverse_exact=True,old=old.decode(),new=new.decode()),f,indent=2);f.write('\n')
assert p.read_bytes()==b;p.write_bytes(v)
print(json.dumps(dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest(),inverse_exact=True)))
