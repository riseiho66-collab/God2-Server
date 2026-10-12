"""Additive SOURCE correction; preserve all early candidates unchanged."""
from pathlib import Path
import hashlib,json,base64
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server');OUT=Path(__file__).resolve().parent
specs=[('src/net/Session.h','4e871fcefb1f2cc06eb606f6cd2257e1e167e892bcfdc27c3843fe0d834e8b17',
    '''    // does not send/decode/reframe bytes. Double capture/reentry poisons it.''',
    '''    // No sending/reframing; existing complete-frame validation applies.
    // Double capture/reentry poisons the first token even if caught.'''),
    ('src/net/Session.cpp','c98aefa8fc8da0f64453eac0fc583e5640a409a2e1c346c344b509c460873ce4',
    '''            s.world_response_callback_capture.reset(); // Previous unhanded attempt retires Failed.
            std::vector<std::uint8_t> response;''',
    '''            s.world_response_callback_capture.reset(); // Previous unhanded attempt retires Failed.
            struct ResponseCaptureEnd {
                Impl& state;
                ~ResponseCaptureEnd(){state.world_response_callback_capture.reset();}
            } response_capture_end{s}; // Unhanded attempt fails on every exceptional unwind.
            std::vector<std::uint8_t> response;'''),
    ('src/core/Application.cpp','4c9b1d0901ae43be3454e2110507ae9f3abc358cb7b7f38d53d09b1288ed625e',
    '''                            auto response=service?service->handle(session,records):std::nullopt;
                            if(!draft->after)return response;''',
    '''                            auto response=service?service->handle(session,records):std::nullopt;
                            if(!local())throw std::runtime_error("Owned mutation response facade retired during callback");
                            if(!draft->after)return response;''')]
prepared=[];refs=[]
for rel,pin,old,new in specs:
    p=ROOT/rel;b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==pin
    opts=list(dict.fromkeys([old.encode(),old.replace('\n','\r\n').encode()]))
    opts=[x for x in opts if b.count(x)==1]
    assert len(opts)==1
    needle=opts[0];a=new.replace('\n','\r\n').encode() if b'\r\n' in needle else new.encode();at=b.index(needle)
    final=b[:at]+a+b[at+len(needle):]
    assert final[:at]+needle+final[at+len(a):]==b
    refs.append({'path':rel,'early_bytes':len(b),'early_sha256':pin,'final_bytes':len(final),
        'final_sha256':hashlib.sha256(final).hexdigest(),'offset':at,'exact_inverse':True,
        'before_b64':base64.b64encode(needle).decode(),'after_b64':base64.b64encode(a).decode()})
    prepared.append((p,final))
for p,b in prepared:
    name='final-'+p.name
    assert not (OUT/name).exists()
    (OUT/name).write_bytes(b);p.write_bytes(b)
(OUT/'correction-manifest.json').write_text(json.dumps({'scope':'accurate header comment, unhanded capture unwind, final facade poison','changes':refs},indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps([{k:v for k,v in r.items() if k not in ('before_b64','after_b64')} for r in refs]))
