"""Final source custody and exact byte comparison only; no target execution."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
R=Path('C:/Users/risei/Desktop/God2/God2-Server')
H=lambda b:hashlib.sha256(b).hexdigest()
def js(n,v):
    with (O/n).open('xb') as f:f.write((json.dumps(v,indent=2)+'\n').encode())
def main():
    receipt=json.loads((O/'apply-receipt.json').read_bytes());rows=[]
    for r in receipt['files']:
        name=r['name'];old=(O/('before-'+name)).read_bytes();b=(R/'src/net'/name).read_bytes()
        assert H(b)==r['after_sha256'] and H(old)==r['before_sha256']
        inv=b
        for c in reversed(r['changes']):
            a=bytes.fromhex(c['new']);z=bytes.fromhex(c['old']);assert inv.count(a)==c.get('count',1);inv=inv.replace(a,z)
        assert inv==old
        with (O/('final-'+name)).open('xb') as f:f.write(b)
        rows.append(dict(path=str(R/'src/net'/name),retained='final-'+name,bytes=len(b),sha256=H(b),crlf=b.count(b'\r\n'),lf=b.count(b'\n'),exact_inverse=True))
    old=(O/'before-Session.cpp').read_bytes();new=(O/'final-Session.cpp').read_bytes()
    spans=[]
    def unchanged(label,first,last):
        a=first.encode();z=last.encode();x=old[old.index(a):old.index(z,old.index(a))];y=new[new.index(a):new.index(z,new.index(a))];assert x==y
        spans.append(dict(name=label,before_start=old.index(a),after_start=new.index(a),bytes=len(x),sha256=H(x)))
    unchanged('old unobserved and observed sender APIs','void Session::send_world_records(std::vector','bool Session::world_records_write_current(')
    unchanged('whole frozen generic logical sender','void Session::send_world_records_impl(','void Session::bind_world_delivery_identity(')
    unchanged('old queue and async write implementation','    void enqueue(Packet packet,','    void close() {')
    unchanged('original exact callback response world-records processing','        game_busy=true;\n        asio::post(game,[self=owner.shared_from_this(),records=','    void enqueue(Packet packet,')
    js('frozen-byte-equality.json',spans)
    js('final-manifest.json',dict(files=rows,scope='Only two authorized Session files; all outside replacement spans exact inverse; no compile/tests/runtime/native/API/CRT/VM/SQL or report invocation'))
    print(json.dumps(dict(success=True,files=rows,unchanged_spans=spans)))
if __name__=='__main__':main()
