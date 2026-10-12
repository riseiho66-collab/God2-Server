"""Additive final source closure; never overwrites the successful earlier cut."""
from pathlib import Path
import hashlib,json
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path(__file__).parent
PEER=OUT.parent/'round345-normal-entry-movement-implementation'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def emit(name,obj):
    assert not (OUT/name).exists()
    (OUT/name).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8',newline='\n')
old_path=PEER/'final-RecoveredMovementService.cpp'
old=old_path.read_bytes()
old_refs=json.loads((OUT/'dependency-references.json').read_text(encoding='utf-8'))
old_ref=next(ref for ref in old_refs if ref['source']=='src/handlers/RecoveredMovementService.cpp')
assert sha(old)==old_ref['source_sha256'] and len(old)==old_ref['source_bytes']
new=(ROOT/'src/handlers/RecoveredMovementService.cpp').read_bytes()
header=(ROOT/'src/handlers/RecoveredMovementService.h').read_bytes()
assert new==(PEER/'frozen-RecoveredMovementService.cpp').read_bytes()
assert header==(PEER/'frozen-RecoveredMovementService.h').read_bytes()
needle=b'#include <limits>\n'
assert old.count(needle)==1 and b'#include <string_view>' not in old
assert new==old.replace(needle,needle+b'#include <string_view>\n')
old_header=next(ref for ref in old_refs if ref['source']=='src/handlers/RecoveredMovementService.h')
assert len(header)==old_header['source_bytes'] and sha(header)==old_header['source_sha256']
lines=new.splitlines(keepends=True)
start=next(i for i,line in enumerate(lines) if b'RecoveredMovementService::move_committed_with_owned_material(' in line)
end=next(i+1 for i,line in enumerate(lines[start:],start) if line.rstrip()==b'}')
cut=b''.join(lines[start:end]);prior_cut=(OUT/old_ref['excerpt']).read_bytes()
assert cut==prior_cut
target=OUT/'final-typed-movement-method.txt'
assert not target.exists();target.write_bytes(cut)
emit('final-core-dependency-reference.json',{
    'old_candidate':{'path':str(old_path),'bytes':len(old),'sha256':sha(old)},
    'final_cpp':{'path':str(ROOT/'src/handlers/RecoveredMovementService.cpp'),'bytes':len(new),'sha256':sha(new)},
    'final_header':{'path':str(ROOT/'src/handlers/RecoveredMovementService.h'),'bytes':len(header),'sha256':sha(header)},
    'include_only_delta_bytes':len(new)-len(old),
    'complete_typed_method':{'first_line':start+1,'last_line':end,'bytes':len(cut),'sha256':sha(cut),
        'excerpt':'final-typed-movement-method.txt','equals_old_captured_method':True},
    'prior_successful_capture_not_rerun_or_changed':True,
    'native_API_SQL_compiler_execution':False})
manifest=json.loads((OUT/'source-manifest.json').read_text(encoding='utf-8'))
for ref in manifest:
    raw=(ROOT/ref['path']).read_bytes()
    assert len(raw)==ref['after_bytes'] and sha(raw)==ref['after_sha256']
emit('final-dependency-capture-success.json',{'status':'additive static dependency closure success',
      'helper_sha256':sha(Path(__file__).read_bytes()),'cpp_sha256':sha(new),'typed_method_sha256':sha(cut)})
print(json.dumps({'status':'additive static dependency closure success','cpp_bytes':len(new),'cpp_sha256':sha(new)}))
