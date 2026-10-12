"""Immutable individual-member custody, no target execution or prior reruns."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
p=O/'seal.json'
if p.exists():raise RuntimeError('Preserve sealed package')
members=[]
for file in sorted(O.rglob('*')):
    if file.is_file():
        raw=file.read_bytes();members.append(dict(path=file.relative_to(O).as_posix(),bytes=len(raw),sha256=sha(raw)))
seal=dict(scope='Round352 bounded native row-alias source; prefix writer OPEN; individual all nested members including failures/partials; excludes only root seal',members=members,member_count=len(members),member_bytes=sum(x['bytes'] for x in members),new_method_opcode_format_route_credits=0)
raw=(json.dumps(seal,indent=2)+'\n').encode();p.write_bytes(raw)
for member in members:
    b=(O/member['path']).read_bytes();assert len(b)==member['bytes'] and sha(b)==member['sha256']
helpers=[]
for name in ['discover_prefix_candidates352.py','discover_row_pointer_candidates352.py','capture_row_alias_source352_final.py','correct_scan_scope352.py','seal_row_alias_source352.py']:
    b=(O/name).read_bytes();assert b'\r' not in b;helpers.append(dict(name=name,bytes=len(b),sha256=sha(b)))
print(json.dumps(dict(seal_sha256=sha(raw),seal_bytes=len(raw),member_count=len(members),member_bytes=seal['member_bytes'],successful_lf_helpers=helpers),indent=2))
