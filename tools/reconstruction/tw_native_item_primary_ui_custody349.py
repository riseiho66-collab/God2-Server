"""Individual read/hash custody seal only, no target or projection execution."""
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
    v=dict(scope='349 static5068C0 actual caller/argument boundary; excludes only own seal',members=rows,member_count=len(rows),member_bytes=sum(r['bytes'] for r in rows),methods=0,opcodes=0,formats=0,routes=0,whole_code_bytes=112,selected_caller_bytes=87,data_bytes=0)
    b=(json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode()
    with (O/'seal.json').open('xb') as f:f.write(b)
    assert (O/'seal.json').read_bytes()==b
    for r in rows:
        z=(O/r['path']).read_bytes();assert len(z)==r['bytes'] and H(z)==r['sha256']
    print(json.dumps(dict(success=True,seal_sha256=H(b),member_count=len(rows),member_bytes=v['member_bytes'],helpers=[r for r in rows if r['path'].endswith('.py')])))
if __name__=='__main__':main()
