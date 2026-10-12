from pathlib import Path
import hashlib,json
R=Path('C:/Users/risei/Desktop/God2/God2-Server')
D=Path(__file__).resolve().parent
f='src/game/OwnedPartyPreviewTransport.h'
p=R/f;b=p.read_bytes();before=b
assert hashlib.sha256(b).hexdigest()=='fdc249defa03612a84c002e500193394714288c018b871338faaeedbdd6858d2'
edits=[]
def replace(old,new):
    global b
    o=old.encode();n=new.encode();assert b.count(o)==1
    b=b.replace(o,n,1);edits.append({'before_hex':o.hex(),'after_hex':n.hex()})
replace('                flight_->retire(true);state_->erase(flight_);throw;\n',
        '                flight_->retire(flight_->committed);state_->erase(flight_);throw;\n')
replace('        flight->recipients.reserve(projections.size());\n',
        '        if(projections.size()>flight->sources.size())return std::nullopt;\n        flight->recipients.reserve(projections.size());\n')
replace('            bool failed=!f->submitted || !f->current(),queued=!failed;\n',
        '            bool failed=!f->submitted;\n            try {if(!f->current())failed=true;}catch(...) {failed=true;}\n            bool queued=!failed;\n')
inverse=b
for e in reversed(edits):
    n=bytes.fromhex(e['after_hex']);o=bytes.fromhex(e['before_hex']);assert inverse.count(n)==1;inverse=inverse.replace(n,o,1)
assert inverse==before and p.read_bytes()==before
p.write_bytes(b)
out=D/'contained-OwnedPartyPreviewTransport.h';assert not out.exists();out.write_bytes(b)
receipt={'scope':'Additive source correction: uncommitted submit error never closes; recipient bound before reserve; current-check exception fails exact committed flight without terminating Scheduler','before_bytes':len(before),'before_sha256':hashlib.sha256(before).hexdigest(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'inverse_equal':True,'edits':edits}
(D/'containment-receipt.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
print(json.dumps({k:v for k,v in receipt.items() if k!='edits'}))
