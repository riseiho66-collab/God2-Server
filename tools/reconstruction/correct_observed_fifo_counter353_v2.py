from pathlib import Path
import json,hashlib
S=Path('C:/Users/risei/Desktop/God2/God2-Server');O=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round353-normal-original-response-transport-implementation');rel='src/net/Session.cpp';p=S/rel;b=p.read_bytes();h=lambda v:hashlib.sha256(v).hexdigest()
assert len(b)==233672 and h(b)=='50614412e93a756d8016e95ef74a81a369d3c5c554ddedc54365c36fea6845da'
text='                                    s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});\n                                    s.writes.back().observed_response=response_write;\n                                    auto pending=NormalWorldResponseStatus::Pending;'
newtext=text.replace('s.write_bytes+=bytes->size();s.writes.push_back({bytes,{}});','s.writes.push_back({bytes,{}});s.write_bytes+=bytes->size();')
choices=[(text.replace('\n',nl).encode(),newtext.replace('\n',nl).encode()) for nl in ['\n','\r\n']];matches=[(a,z) for a,z in choices if b.count(a)==1];assert len(matches)==1;old,new=matches[0]
v=b.replace(old,new);assert v.replace(new,old)==b
p.write_bytes(v);d=O/'fifo-counter-corrected'/rel;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(v)
(O/'fifo-counter-correction.json').write_text(json.dumps({'path':rel,'before_bytes':len(b),'before_sha256':h(b),'after_bytes':len(v),'after_sha256':h(v),'old':old.decode(),'new':new.decode(),'count':1,'inverse_exact':True,'legacy_else_unchanged':True,'reason':'Only observed branch pushes before debiting counter; failed allocation must not debit'},indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'bytes':len(v),'sha256':h(v),'legacy_else_unchanged':True}))
