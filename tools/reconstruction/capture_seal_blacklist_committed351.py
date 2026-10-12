"""One-shot source custody/inverse proof and seal only; no product/API/SQL execution."""
from pathlib import Path
import hashlib
import json
import difflib
import subprocess
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def emit(n,b):
 p=OUT/n
 if p.exists():raise RuntimeError('Refusing overwrite '+n)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def js(n,v):emit(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
if (OUT/'SEAL.json').exists():raise RuntimeError('Already sealed')
paths=['src/db/SqliteOwnedBlacklistRepository.h','src/db/SqliteOwnedBlacklistRepository.cpp',
       'src/handlers/OwnedBlacklistService.h','src/handlers/OwnedBlacklistService.cpp']
stages=[json.loads((OUT/n).read_bytes()) for n in
 ['exact-edits-and-inverse.json','owned-pointer-correction.json','fixed-change-fence-correction.json']]
files=[]
for p in paths:
 raw=(ROOT/p).read_bytes();before=(OUT/'before'/p).read_bytes()
 normalized=raw.decode().replace('\r\n','\n');inverse=normalized
 for stage in reversed(stages):
  for edit in reversed(stage['edits']):
   if edit['path']==p:
    count=edit.get('count',1)
    if inverse.count(edit['replacement'])!=count:raise RuntimeError('Inverse nonunique '+p)
    inverse=inverse.replace(edit['replacement'],edit['original'])
 ending='\r\n' if b'\r\n' in before else '\n'
 if inverse.replace('\n',ending).encode()!=before:raise RuntimeError('Full inverse not exact '+p)
 emit('final/'+p,raw)
 oldtext=before.decode().replace('\r\n','\n')
 diff=''.join(difflib.unified_diff(oldtext.splitlines(keepends=True),normalized.splitlines(keepends=True),
     fromfile='before/'+p,tofile='final/'+p)).encode()
 emit('diff/'+p+'.diff',diff)
 files.append({'path':p,'before_bytes':len(before),'before_sha256':sha(before),
     'final_bytes':len(raw),'final_sha256':sha(raw),'line_count':len(raw.splitlines()),
     'inverse_all_three_stages_byte_equal':True,'crlf_count':raw.count(b'\r\n'),'lf_count':raw.count(b'\n')})
js('implementation-note.json',{
 'scope':'Four authorized source files only: actual common blacklist transaction material transport, not new permission/allocator/schema/protocol authority.',
 'api':'Repo::CommittedChange is move-only/private ctor. before/after Snapshot immutable in preowned private shared Data, row/logical/changed constgetters and noalloc alias before_ptr/after_ptr. add_committed/remove_committed and service handle_committed return optional actual transaction result.',
 'actual_supplier':'Current same-connection account/character fullroots, CP950 names, current full rows, actual intended add/reactivate/remove and exact native A5/A4 from existing protocol projection. No caller receipt mintage, postcommit observation or new row issuer.',
 'precommit':'Read owning actual before without mutation, derive exact permitted one-row expected after, read complete actual staged rows and compare, allocate wire/fullSnapshots/row/sharedData/optional before COMMIT. Fixed staged_changes/autocommit fences after-write interval through SQL root observers and immediate preCOMMIT check.',
 'noop':'Existing active add and inactive remove retain original A5/A4 bytes and before==after, changedfalse; a rejected/no operation is null at typed API and original emptyvector at legacy service.',
 'adapters':'Existing repo add/remove privately move Row and legacy servicehandle privately moves the exact already-owned logical vector. No afterCOMMIT wire projection/fullsnapshotcopy/allocation in these extractions. Wire, quota, allocator, capturedidentity and schema statements unchanged.',
 'allocation_timing':'Before/after/wire/privateData allocation failures now occur beforeCOMMIT and roll back. This is an intentional safety change, not a claim that previous allocation-failure timing is unchanged.',
 'freshness':'Private result publishes only after its real single COMMIT; immutable material does not assert future DB/current Session/native cache/Written/ACK or full route. No callbacks retained inside result.',
 'review_limit':'The fixed change fence qualifies the selected preCOMMIT material interval; it is not a guarantee about arbitrary external SQLite COMMIT/finalize hooks, runtime behavior or future storage freshness.',
 'custody':'Initial successful generation plus owning-pointer and fixed-count corrective successors retained; exact reverse replacement of all three stages recovers original four source bytes. Original candidates/helpers remain unchanged.',
 'execution':'Only source edit/read/hash/diff/inverse/gitsource custody helpers; no target API/SQL/native/compiler/tests/build/runtime.',
 'native_format_credit':0,'whole_route_credit':0,'native_acceptance_credit':0})
js('final-source-manifest.json',{'head':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD']).decode().strip(),
 'files':files,'all_four_byte_inverse_to_before':True,
 'source_line_endings_preserved':True,'tracked_status_at_capture':subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain','--untracked-files=no']).decode(),
 'other_agents':'App/Session/Config/metadata changes, if present, are outside this package owned edit scope.'})
for f in files:
 if sha((ROOT/f['path']).read_bytes())!=f['final_sha256']:raise RuntimeError('Final source changed')
members=[]
for p in sorted(OUT.rglob('*')):
 if p.is_file():
  data=p.read_bytes();members.append({'name':p.relative_to(OUT).as_posix(),'bytes':len(data),'sha256':sha(data)})
js('SEAL.json',{'schema':'individual-member-sha256-v1','member_count':len(members),'total_bytes':sum(m['bytes'] for m in members),
 'head':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD']).decode().strip(),'native_complete_routes':0,'members':members})
for m in members:
 b=(OUT/m['name']).read_bytes()
 if len(b)!=m['bytes'] or sha(b)!=m['sha256']:raise RuntimeError('Sealed member readback mismatch')
seal=(OUT/'SEAL.json').read_bytes()
print(json.dumps({'member_count':len(members),'total_bytes':sum(m['bytes'] for m in members),'seal_bytes':len(seal),'seal_sha256':sha(seal),
 'files':files,'helpers':[{'name':p.name,'bytes':len(p.read_bytes()),'sha256':sha(p.read_bytes())}
                        for p in sorted(OUT.glob('*.py'))]}))
