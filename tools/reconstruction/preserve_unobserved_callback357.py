from pathlib import Path
import hashlib,json
R=Path('C:/Users/risei/Desktop/God2/God2-Server');D=Path(__file__).resolve().parent
f='src/net/Session.cpp';p=R/f;before=p.read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha(before)=='ca794155693d8fae086f171abec3e127546d0c09ba5e2b7c99d501aa4afe957a'
o=b'                        accepted=result.has_value() && !observation_scope.response_poisoned;'
n=b'                        accepted=result.has_value() && (!s.normal_callback_admission_capture || !observation_scope.response_poisoned);'
assert before.count(o)==1;b=before.replace(o,n,1);assert b.replace(n,o,1)==before and p.read_bytes()==before
p.write_bytes(b)
out=D/'corrected-Session.cpp';assert not out.exists();out.write_bytes(b)
(D/'scope-correction-receipt.json').write_bytes((json.dumps({'source':f,'before_bytes':len(before),'before_sha256':sha(before),'bytes':len(b),'sha256':sha(b),'before_hex':o.hex(),'after_hex':n.hex(),'inverse_equal':True,'scope':'Only newly observed admission callback applies scope-poison rejection; original generic/unarmed/raw/normal gates preserved'},indent=2)+'\n').encode())
print(json.dumps({'bytes':len(b),'sha256':sha(b),'inverse_equal':True}))
