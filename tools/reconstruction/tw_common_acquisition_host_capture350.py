"""One-shot source-byte custody only. No target import, API, SQL or codec execution."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT = Path(__file__).resolve().parent
PRIOR = OUT.parent / 'round347-initial-common-authority-source'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def emit(name, value):
    path = OUT / name
    if path.exists():
        raise RuntimeError('Refusing overwrite: ' + name)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    path.write_bytes(data)

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

spec = [
    ('src/db/NativeItemDefinitionObservation.h', [(1,44,'definition-observation-whole')]),
    ('src/db/NativeMapItemCatalog.h', [(1,43,'spi-display-catalog-whole')]),
    ('src/db/OwnedInventoryRepository.h', [(1,61,'common-inventory-contract-whole')]),
    ('src/db/SqliteOwnedInventoryRepository.h', [(1,80,'common-writer-contract-whole')]),
    ('src/db/SqliteOwnedInventoryRepository.cpp', [(120,168,'common-private-stage-whole'),(169,197,'common-replace-whole'),(198,245,'durable-observation-and-definition-whole'),(285,318,'common-schema-tail')]),
    ('src/db/SqliteOwnedEquipmentTransaction.h', [(1,140,'joint-contract-whole')]),
    ('src/db/SqliteOwnedEquipmentTransaction.cpp', [(36,90,'joint-replace-whole')]),
    ('src/db/SqliteRecoveredCharacterRepository.h', [(40,65,'town-public-result-and-db-identity')]),
    ('src/db/SqliteRecoveredCharacterRepository.cpp', [(200,232,'town-reward-whole')]),
    ('src/db/SqliteSupport.h', [(84,95,'transaction-class-whole')]),
    ('src/game/SharedTaiwanOwnedBagMoveSource.cpp', [(1,116,'existing-move-plan-and-original-reply'),(206,288,'normal-entry-owner-whole')]),
    ('src/game/TaiwanOwnedBagItemMaterial.h', [(1,40,'material-contract-whole')]),
    ('src/core/Application.cpp', [(630,641,'game-thread-prefix'),(941,951,'actual-repository-owner'),(1232,1240,'pending-town-owner'),(2323,2332,'disconnect-cleanup'),(2424,2437,'diagnostic-only-provision-context'),(5551,5689,'hosted-town-selected-branch-complete')]),
    ('src/handlers/DiagnosticQuestConversation.h', [(1,129,'conversation-contract-whole')]),
]

if (OUT/'source-references.json').exists():
    raise RuntimeError('Already captured; do not rerun')
head = git('rev-parse','HEAD').decode().strip()
refs=[]
cuts=[]
for rel, ranges in spec:
    data=(ROOT/rel).read_bytes()
    frozen=git('show',head+':'+rel)
    if data != frozen:
        raise RuntimeError('Current bytes are not snapshot HEAD: '+rel)
    lines=data.splitlines(keepends=True)
    refs.append({'path':rel,'head':head,'bytes':len(data),'sha256':sha(data),
                 'line_count':len(lines),'crlf_count':data.count(b'\r\n'),'lf_count':data.count(b'\n'),
                 'head_blob_byte_equal':True})
    for first,last,name in ranges:
        if not 1 <= first <= last <= len(lines):
            raise RuntimeError('Invalid source range: '+name)
        raw=b''.join(lines[first-1:last])
        rawpath=OUT/'cuts'/(name+'.source')
        textpath=OUT/'cuts'/(name+'.txt')
        if rawpath.exists() or textpath.exists():
            raise RuntimeError('Cut already exists: '+name)
        rawpath.parent.mkdir(exist_ok=True)
        rawpath.write_bytes(raw)
        text=(''.join(str(i)+': '+lines[i-1].decode('utf-8').rstrip('\r\n')+'\n'
                       for i in range(first,last+1))).encode('utf-8')
        textpath.write_bytes(text)
        cuts.append({'path':rel,'head':head,'first_line':first,'last_line':last,
                     'whole_method_or_class':name.endswith('whole'),
                     'raw_member':rawpath.relative_to(OUT).as_posix(),'bytes':len(raw),'sha256':sha(raw),
                     'annotated_member':textpath.relative_to(OUT).as_posix(),'annotated_sha256':sha(text)})
emit('source-references.json',{'snapshot_head':head,'sources':refs,'cuts':cuts,
     'execution_scope':'Source byte reads, SHA256 and git source custody only; no target/API/SQL execution.'})

priorseal=(PRIOR/'SEAL.json').read_bytes()
prior=json.loads(priorseal)
members=[]
for m in prior['members']:
    data=(PRIOR/m['name']).read_bytes()
    actual={'name':m['name'],'bytes':len(data),'sha256':sha(data)}
    if actual['bytes']!=m['bytes'] or actual['sha256']!=m['sha256']:
        raise RuntimeError('Prior347 individual member changed: '+m['name'])
    members.append(actual)
if len(members)!=prior['member_count'] or sum(m['bytes'] for m in members)!=prior['total_bytes']:
    raise RuntimeError('Prior347 aggregate mismatch')
emit('prior347-individual-verification.json',{'package':str(PRIOR),'seal_sha256':sha(priorseal),
     'member_count':len(members),'total_bytes':sum(m['bytes'] for m in members),'members':members,
     'scope':'Custody only; historical findings are not new route credit.'})
emit('shell-read-failure-receipt.json',{'phase':'Line-count discovery before source capture',
     'failed_operation':'PowerShell foreach statement piped directly to ConvertTo-Json',
     'exit_code':1,'error':'ParserError: An empty pipe element is not allowed.',
     'correction':'Bind foreach results to $rows then pipe $rows; source range counts read successfully.',
     'source_mutation':False,'target_execution':False,'evidence_derived_from_failure':False})
emit('capture-custody.json',{'initial_review_head':'a5e3a01603e77f9707efaaadcd37722dd7729eca',
     'capture_head':head,'end_head':git('rev-parse','HEAD').decode().strip(),
     'tracked_status':git('status','--porcelain','--untracked-files=no').decode(),
     'wording_correction':'Parent task said CUSTOM0143; 143 is SqliteOwnedInventoryRepository.cpp source line, not a CUSTOM identifier. Actual common storage is CUSTOM-0092 at header line13.',
     'read_only':True,'native_whole_route_credit':0,'implementation_proposed':False})
print(json.dumps({'head':head,'source_count':len(refs),'cut_count':len(cuts),'prior347_members':len(members)}))
