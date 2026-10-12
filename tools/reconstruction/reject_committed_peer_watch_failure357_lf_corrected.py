from pathlib import Path
import hashlib,json
R=Path('C:/Users/risei/Desktop/God2/God2-Server');D=Path(__file__).resolve().parent
p=R/'src/core/Application.cpp';b=p.read_bytes();sha=lambda v:hashlib.sha256(v).hexdigest()
assert sha(b)=='510cc4c330f96b846d94b11465d21d07010a49a9c9e61f42cb07a349681a8bee'
o=b'                                try{peer->close();}catch(...){}\n                                spdlog::warn("PARTY_DIRECTORY_WATCH_SUBMIT_FAILED reason={}",error.what());'
n=b'                                try{peer->close();}catch(...){}\n                                if(dispatch->committed_preview){dispatch->reject_admission();return false;}\n                                spdlog::warn("PARTY_DIRECTORY_WATCH_SUBMIT_FAILED reason={}",error.what());'
assert b.count(o)==1;a=b.replace(o,n,1);assert a.replace(n,o,1)==b and p.read_bytes()==b
q=D/'peer-watch-corrected-Application.cpp';assert not q.exists();p.write_bytes(a);q.write_bytes(a)
(D/'peer-watch-correction-receipt.json').write_bytes((json.dumps({'source':'src/core/Application.cpp','before_bytes':len(b),'before_sha256':sha(b),'bytes':len(a),'sha256':sha(a),'before_hex':o.hex(),'after_hex':n.hex(),'inverse_equal':True,'scope':'After original exact peer retirement only actual committed preview prefix fails shared callback receipt; original no-prefix warning and true return remain'},indent=2)+'\n').encode())
print(json.dumps({'bytes':len(a),'sha256':sha(a),'inverse_equal':True}))
