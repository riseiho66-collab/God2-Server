"""SOURCE-only move of the same active mutation guard before all variants."""
from pathlib import Path
import hashlib,json,base64
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server');OUT=Path(__file__).resolve().parent
p=ROOT/'src/core/Application.cpp';b=p.read_bytes()
assert hashlib.sha256(b).hexdigest()=='6d465d4de6f05b8583b39a7165c2ef28beddd56bdfe3e45458b00491bc33917f'
data=b;hunks=[]
specs=[('''                            if(host->active) {
                                host->active->invalid=true;
                                if(host->binding)host->binding->invalidate_active();
                                throw std::logic_error("Owned mutation response facade reentered");
                            }
                            const auto initialization=session.normal_world_initialization();''','''                            const auto initialization=session.normal_world_initialization();'''),
('''                        if(!host || !host->live || !host->accepting)return {};
                        // Entire original batch before typed consumers/observers.''','''                        if(!host || !host->live || !host->accepting)return {};
                        if(host->active) {
                            host->active->invalid=true;
                            if(host->binding)host->binding->invalidate_active();
                            throw std::logic_error("Owned mutation response facade reentered");
                        }
                        // Entire original batch before typed consumers/observers.''')]
for old,new in specs:
    opts=list(dict.fromkeys([old.encode(),old.replace('\n','\r\n').encode()]))
    opts=[x for x in opts if data.count(x)==1];assert len(opts)==1
    needle=opts[0];a=new.replace('\n','\r\n').encode() if b'\r\n' in needle else new.encode();at=data.index(needle)
    data=data[:at]+a+data[at+len(needle):]
    hunks.append({'offset':at,'before_b64':base64.b64encode(needle).decode(),'after_b64':base64.b64encode(a).decode()})
inverse=data
for h in reversed(hunks):
    a=base64.b64decode(h['after_b64']);before=base64.b64decode(h['before_b64']);at=h['offset']
    assert inverse[at:at+len(a)]==a;inverse=inverse[:at]+before+inverse[at+len(a):]
assert inverse==b
dest=OUT/'frozen-Application.cpp';assert not dest.exists();dest.write_bytes(data);p.write_bytes(data)
r={'path':str(p),'before_bytes':len(b),'before_sha256':hashlib.sha256(b).hexdigest(),
    'after_bytes':len(data),'after_sha256':hashlib.sha256(data).hexdigest(),'exact_inverse':True,'hunks':hunks}
(OUT/'reentry-correction-manifest.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in r.items() if k!='hunks'}))
