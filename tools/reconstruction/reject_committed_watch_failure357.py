from pathlib import Path
import hashlib,json
R=Path('C:/Users/risei/Desktop/God2/God2-Server');D=Path(__file__).resolve().parent
p=R/'src/core/Application.cpp';b=p.read_bytes();sha=lambda v:hashlib.sha256(v).hexdigest()
assert sha(b)=='f37cfe11a8050087d798b74fabfb0c0d8821af2e3a8e615af871b2569e2212c1'
o=b'try{(void)reconcile(nullptr,&session,&wire);}catch(const std::exception& error){spdlog::warn("PARTY_DIRECTORY_WATCH_REFRESH_FAILED reason={}",error.what());}'
n=b'try{(void)reconcile(nullptr,&session,&wire);}catch(const std::exception& error){if(dispatch->committed_preview){dispatch->reject_admission();return {};}spdlog::warn("PARTY_DIRECTORY_WATCH_REFRESH_FAILED reason={}",error.what());}'
assert b.count(o)==1;a=b.replace(o,n,1);assert a.replace(n,o,1)==b and p.read_bytes()==b
q=D/'watch-corrected-Application.cpp';assert not q.exists();p.write_bytes(a);q.write_bytes(a)
(D/'watch-correction-receipt.json').write_bytes((json.dumps({'source':'src/core/Application.cpp','before_bytes':len(b),'before_sha256':sha(b),'bytes':len(a),'sha256':sha(a),'before_hex':o.hex(),'after_hex':n.hex(),'inverse_equal':True,'scope':'Caught watch refresh failure rejects exact shared callback only after actual committed preview prefix; original no-prefix warning retained'},indent=2)+'\n').encode())
print(json.dumps({'bytes':len(a),'sha256':sha(a),'inverse_equal':True}))
