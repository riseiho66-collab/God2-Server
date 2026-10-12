"""Individual-member hash/readback only; never runs target or source projection."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
def main():
    assert not (O/'seal.json').exists()
    rows=[]
    for p in sorted(O.rglob('*')):
        if p.is_file():
            b=p.read_bytes()
            if p.suffix=='.py':assert b'\r' not in b
            rows.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=H(b)))
    v=dict(scope='350 static actual41EA00 direct writes/widths; excludes only root seal',members=rows,member_count=len(rows),member_bytes=sum(r['bytes'] for r in rows),whole_code_bytes=487,padding_bytes=9,methods=0,opcodes=0,formats=0,routes=0)
    z=(json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode()
    with (O/'seal.json').open('xb') as f:f.write(z)
    assert (O/'seal.json').read_bytes()==z
    for r in rows:
        b=(O/r['path']).read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256']
    print(json.dumps(dict(success=True,seal_sha256=H(z),member_count=len(rows),member_bytes=v['member_bytes'],helpers=[r for r in rows if r['path'].endswith('.py')])))
if __name__=='__main__':main()
