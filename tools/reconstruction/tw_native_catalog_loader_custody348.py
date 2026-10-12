"""348 bounded static-source individual-member seal; LF, no capture rerun."""
from pathlib import Path
import json,hashlib
O=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    p=O/'seal.json'
    if p.exists():raise RuntimeError('Preserve348')
    c=json.loads((O/'capture-complete.json').read_text('utf-8'))
    assert c['success'] and c['code_bytes']==2846 and c['data_bytes']==1238
    assert (O/'REPORT.md').is_file()
    members=[]
    for q in sorted(O.rglob('*')):
        if q.is_file() and q!=p:
            b=q.read_bytes()
            if q.suffix=='.py':assert b'\r' not in b
            members.append(dict(path=q.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
    result=dict(scope='348 static inline catalog/bank source boundary; excludes only own root seal',
        members=members,member_count=len(members),member_bytes=sum(x['bytes'] for x in members),
        new_methods=0,new_opcodes=0,new_formats=0,new_routes=0)
    raw=(json.dumps(result,indent=2,ensure_ascii=False)+'\n').encode();p.write_bytes(raw)
    assert p.read_bytes()==raw
    for x in members:
        b=(O/x['path']).read_bytes();assert len(b)==x['bytes'] and sha(b)==x['sha256']
    print(json.dumps(dict(success=True,seal_sha256=sha(raw),member_count=len(members),
        member_bytes=sum(x['bytes'] for x in members),helpers=[x for x in members if x['path'].endswith('.py')])))
if __name__=='__main__':main()
