"""Immutable member-derived347 closure, static file reads only; LF source."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    dst=O/'seal.json'
    if dst.exists(): raise RuntimeError('Preserve sealed347')
    capture=json.loads((O/'capture-complete.json').read_text('utf-8'))
    assert capture['success'] and capture['code_bytes']==4664 and capture['data_bytes']==162
    assert (O/'REPORT.md').is_file() and (O/'prior-sealed-members-verified.json').is_file()
    rows=[]
    for p in sorted(O.rglob('*')):
        if p.is_file() and p!=dst:
            b=p.read_bytes()
            if p.suffix=='.py': assert b'\r' not in b,('LF helper',p.name)
            rows.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
    result=dict(scope='Bounded347 static native normal-entry readiness source; individual members; excludes only own root seal',
        members=rows,member_count=len(rows),member_bytes=sum(r['bytes'] for r in rows),
        no_native_execution=True,no_repository_mutation=True,
        new_methods=0,new_opcodes=0,new_formats=0,new_routes=0)
    raw=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    dst.write_bytes(raw)
    # Verify written closure and every member without rewriting/capture reruns.
    assert dst.read_bytes()==raw
    for r in rows:
        b=(O/r['path']).read_bytes(); assert len(b)==r['bytes'] and sha(b)==r['sha256']
    print(json.dumps(dict(success=True,seal_sha256=sha(raw),member_count=len(rows),
        member_bytes=sum(r['bytes'] for r in rows),
        helpers=[r for r in rows if r['path'].endswith('.py')])))
if __name__=='__main__': main()
