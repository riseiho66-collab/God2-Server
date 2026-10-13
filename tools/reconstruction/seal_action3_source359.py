from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
assert (D/'capture-complete.json').exists() and not (D/'seal.json').exists()
members=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  b=p.read_bytes();members.append({'path':p.relative_to(D).as_posix(),'bytes':len(b),'sha256':sha(b)})
for m in members:
 b=(D/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
helpers=[]
for name in ['discover_action3_source359_partial.py','close_action3_source359_corrected.py','discover_delta_mask359.py','close_delta_mask359_corrected.py','capture_delta_primitive359_partial.py','capture_action3_custody359_paths_corrected.py','seal_action3_source359.py']:
 m=next(v for v in members if v['path']==name);b=(D/name).read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf');helpers.append(dict(m,successful_execution_count=1))
v={'round':359,'scope':'Static original CN83/action3 finite source boundary; three full bodies and one explicit partial; no tracked/native execution','member_count':int(len(members)),'member_bytes':int(sum(m['bytes'] for m in members)),'credits':{'global_method':0,'opcode':0,'format':0,'route':0},'successful_lf_helpers':helpers,'members':members}
b=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode();(D/'seal.json').write_bytes(b);assert (D/'seal.json').read_bytes()==b
for m in members:
 b=(D/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
print(json.dumps({'member_count':v['member_count'],'member_bytes':v['member_bytes'],'seal_bytes':(D/'seal.json').stat().st_size,'seal_sha256':sha((D/'seal.json').read_bytes()),'helpers':helpers}))
