"""Additive static review custody; do not execute application/protocol code."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
R=Path('C:/Users/risei/Desktop/God2/God2-Server')
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
    p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise RuntimeError('Do not replace '+n)
    p.write_bytes(b if isinstance(b,bytes) else (json.dumps(b,indent=2)+'\n').encode())
refs=[]
for n in ['src/game/OwnedPartyDirectory.h','src/handlers/OwnedPartyDirectoryService.h']:
    b=(R/n).read_bytes();put('sources/'+n,b)
    refs.append(dict(path=str(R/n),bytes=len(b),sha256=sha(b),whole_source=True,role='Current published355 baseline before root implementation; static source only.'))
put('party-review-source-references.json',refs)
spans=[('party-C90-detail-and-C91-permission','src/core/Application.cpp',7190,7334),('party-final-old-permission-and-CAS','src/core/Application.cpp',7335,7360),('directory-watcher-detail-presentation','src/handlers/OwnedPartyDirectoryService.h',130,165),('directory-source-carriers','src/game/OwnedPartyDirectory.h',44,67),('same-callback-private-response-capture','src/net/Session.cpp',2704,2790)]
cuts=[]
for label,n,lo,hi in spans:
    b=(O/'sources'/n).read_bytes();lines=b.splitlines(keepends=True);cut=b''.join(lines[lo-1:hi])
    put('cuts/'+label+'.txt',cut)
    cuts.append(dict(label=label,source=n,first_line=lo,last_line=hi,bytes=len(cut),sha256=sha(cut),whole_method_claim=False))
put('party-review-cuts.json',cuts)
put('party-review-complete.json',dict(whole_additive_sources=len(refs),whole_source_bytes=sum(x['bytes'] for x in refs),additive_cuts=len(cuts),cut_bytes=sum(x['bytes'] for x in cuts),tracked_edits=False,root_proposal_review_only=True))
print((O/'party-review-complete.json').read_text())
