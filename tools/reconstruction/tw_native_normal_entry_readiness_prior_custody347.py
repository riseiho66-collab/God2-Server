"""Additive347 referenced-member custody; never rerun the successful capture."""
from pathlib import Path
import json,hashlib
O=Path(__file__).resolve().parent
A=O.parent
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    dst=O/'prior-sealed-members-verified.json'
    if dst.exists() or (O/'seal.json').exists(): raise RuntimeError('Preserve closure')
    refs=json.loads((O/'prior-member-inplace-references.json').read_text('utf-8'))
    groups=[A/'tw-native-visibility-state-and-source-311/native-visibility',
        A/'tw-native-petegg-selection-source-329']
    results=[]
    for base in groups:
        seal=base/'seal.json'; raw=seal.read_bytes(); obj=json.loads(raw)
        members={m['path']:m for m in obj['members']}; verified=[]
        for r in refs:
            p=Path(r['path'])
            if p.is_relative_to(base):
                name=p.relative_to(base).as_posix(); m=members[name]; b=p.read_bytes()
                assert len(b)==m['bytes'] and sha(b)==m['sha256']
                verified.append(dict(path=name,bytes=len(b),sha256=sha(b)))
        results.append(dict(seal_path=str(seal),seal_bytes=len(raw),seal_sha256=sha(raw),
            referenced_members_verified=verified,
            scope='Only individually referenced members, not a claim of whole package revalidation.'))
    q=A/'tw-native-visibility-state-and-source-311/native-visibility/qualified-spans.json'
    raw=q.read_bytes(); obj=json.loads(raw)
    results.append(dict(path=str(q),bytes=len(raw),sha256=sha(raw),
        relevant_entries=[r for r in obj if 'role_initializer' in str(r)] if isinstance(obj,list) else obj,
        correction_scope='311 REPORT explicitly restricts nonnull selected branch and no whole464910 audit. Old mechanical maps were not qualified whole468160 methods.'))
    dst.write_bytes((json.dumps(results,indent=2,ensure_ascii=False)+'\n').encode())
    print(json.dumps(dict(success=True,groups=len(groups),referenced_members=sum(len(r['referenced_members_verified']) for r in results[:2]))))
if __name__=='__main__': main()
