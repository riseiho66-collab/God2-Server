from pathlib import Path
import hashlib,json
D=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013/round364-cn-command-common-definition-implementation');H=lambda b:hashlib.sha256(b).hexdigest()
assert not (D/'seal.json').exists();cap=json.loads((D/'capture-success.json').read_bytes());assert cap['status']=='PASS' and cap['successful_execution_count']==1
refs=json.loads((D/'source-references.json').read_bytes());assert isinstance(refs,list) and len(refs)==23
for r in refs:
 assert type(r['bytes']) is int and r['bytes']>=0;p=(D/r['retained']).resolve();assert p.is_relative_to(D.resolve());b=p.read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256'];assert Path(r['actual_path']).read_bytes()==b
ms=[];seen=set()
for p in sorted(D.rglob('*'),key=lambda p:p.as_posix().casefold()):
 if not p.is_file():continue
 assert not p.is_symlink();p=p.resolve();assert p.is_relative_to(D.resolve());rel=p.relative_to(D.resolve()).as_posix();assert rel.casefold() not in seen;seen.add(rel.casefold());b=p.read_bytes();ms.append({'path':rel,'bytes':len(b),'sha256':H(b)})
s={'status':'PASS_BOUNDED_SOURCE_ONLY','member_count':len(ms),'member_bytes':sum(m['bytes'] for m in ms),'source_reference_count':len(refs),'modified_existing_cpp_files':2,'new_cpp_files':0,'chronological_literal_edits':19,'members':ms};b=(json.dumps(s,indent=2)+'\n').encode();(D/'seal.json').write_bytes(b)
for m in ms:
 p=(D/m['path']).resolve();assert p.is_relative_to(D.resolve());v=p.read_bytes();assert type(m['bytes']) is int and len(v)==m['bytes'] and H(v)==m['sha256']
assert json.loads((D/'seal.json').read_bytes())==s
hs=[]
for n in ['capture_cn_command_common_definition364.py','seal_cn_command_common_definition364.py']:
 v=(D/n).read_bytes();assert b'\r' not in v and not v.startswith(b'\xef\xbb\xbf') and v.endswith(b'\n') and not v.endswith(b'\n\n');hs.append({'actual_path':(D.parent/n).as_posix(),'retained':n,'bytes':len(v),'sha256':H(v),'successful_execution_count':1})
r=(D/'REPORT.md').read_bytes();print(json.dumps({'status':'PASS','member_count':len(ms),'member_bytes':s['member_bytes'],'seal_bytes':len(b),'seal_sha256':H(b),'report_bytes':len(r),'report_sha256':H(r),'source_refs':len(refs),'source_bytes':sum(r['bytes'] for r in refs),'helpers':hs}))
