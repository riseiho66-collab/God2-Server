"""One-shot current source proposal custody only; no product/API/SQL/native execution."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server')
OUT=Path(__file__).resolve().parent
def sha(data):return hashlib.sha256(data).hexdigest()
def emit(name,data):
    p=OUT/name
    if p.exists():raise RuntimeError('Refusing overwrite '+name)
    p.parent.mkdir(exist_ok=True,parents=True)
    p.write_bytes(data)
def js(name,value):emit(name,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
if (OUT/'SEAL.json').exists():raise RuntimeError('Already sealed')
head=git('rev-parse','HEAD').decode().strip()
spec=[
 ('src/db/SqliteOwnedBlacklistRepository.h',[(1,41,'repository-contract-whole')]),
 ('src/db/SqliteOwnedBlacklistRepository.cpp',[(1,195,'repository-whole')]),
 ('src/handlers/OwnedBlacklistService.h',[(1,20,'service-contract-whole')]),
 ('src/handlers/OwnedBlacklistService.cpp',[(1,33,'service-whole')]),
 ('src/protocol/TaiwanNativeBlacklist.h',[(1,56,'native-shape-contract-whole')]),
 ('src/core/Application.cpp',[(927,938,'real-replay-state'),(2259,2266,'disconnect-custody'),(6631,6739,'hosted-blacklist-wrapper-whole')]),
 ('src/net/Session.h',[(125,145,'private-normal-initialization-contract'),(345,378,'existing-world-sender-contract')]),
 ('src/net/Session.cpp',[(150,180,'normal-entry-private-data'),(2372,2394,'existing-senders-and-tls-limit'),(2424,2453,'private-receipt-callback-current'),(2454,2505,'peer-current-and-original-enqueue-whole'),(3219,3258,'private0083-enqueue-whole')]),
 ('docs/custom-designs.json',[(3731,3768,'existing-custom0096-authority-scope')]),
 ('docs/GOAL_ACCEPTANCE.md',[(1,34,'current-goal-acceptance')]),
]
refs=[];cuts=[]
for rel,ranges in spec:
 data=(ROOT/rel).read_bytes()
 if data!=git('show',head+':'+rel):raise RuntimeError('Uncommitted input '+rel)
 lines=data.splitlines(keepends=True)
 refs.append({'path':rel,'head':head,'bytes':len(data),'sha256':sha(data),'line_count':len(lines),'head_blob_byte_equal':True})
 for lo,hi,name in ranges:
  if not 1<=lo<=hi<=len(lines):raise RuntimeError('Invalid range '+name+' '+str(len(lines)))
  raw=b''.join(lines[lo-1:hi]);member='cuts/'+name+'.source'
  emit(member,raw)
  text=''.join(str(i)+': '+lines[i-1].decode('utf-8').rstrip('\r\n')+'\n' for i in range(lo,hi+1)).encode()
  emit('cuts/'+name+'.txt',text)
  cuts.append({'source':rel,'first_line':lo,'last_line':hi,'member':member,'bytes':len(raw),'sha256':sha(raw)})
ledgerpath='artifacts/integration/packet-connections-20261006/packet-route-ledger.json'
ledgerbytes=(ROOT/ledgerpath).read_bytes();ledger=json.loads(ledgerbytes)
selected=[g for g in ledger['reviewed_world_source_groups'] if 'blacklist' in g.get('name','').lower()]
js('ledger-selected-route.json',{'path':ledgerpath,'bytes':len(ledgerbytes),'sha256':sha(ledgerbytes),
 'world_unconnected_gameplay_opcodes':ledger['world_unconnected_gameplay_opcodes'],
 'unconnected_count':len(ledger['world_unconnected_gameplay_opcodes']),
 'pending_world_source_group_count':len(ledger['pending_world_source_groups']),
 'selected_reviewed_group':selected,'claim':'Denominators retained; selected delta is one existing scoped variant, not completion of all contacts or new opcode.'})
proposal={
 'selection':'Existing hosted TW C89 add / C8A remove, CUSTOM-0096 common captured-name blacklist; one currently OPEN concurrent same-owner live propagation variant.',
 'genuine_supplier':'SqliteOwnedBlacklistRepository owns common account/character roots and exact CP950 profile/name, one unique target, immutable captured bytes, positive global contact-row allocator, active/tombstone rows and quota. add/remove retain actual row material before one COMMIT. These are genuine existing storage authority, unlike definition observations or caller-created grants.',
 'exact_protocol':'C89 logical17 and C8A logical5 requests; actual replies S A5 logical21 captured row/name and S A4 logical5 row removal. Initial exploratory message incorrectly called outputs S89/S8A; corrected to A5/A4 before this proposal, no evidence/code derived from the typo.',
 'current_call':'Application6687 calls actual service after current Session/phase/complete replay checks;6689 appends original logical response in the requesting callback response. Servicehandle returns post-COMMIT row-derived native logical bytes. Replay source Snapshot includes full rowset and supported flag.',
 'proposal_not_implementation':[
  'Add a used typed service/repository result for the actual add/remove invocation retaining complete actual before Snapshot, exact after Snapshot and original A5/A4 logical response. Reuse actual already-read rows and exact actual row result; construct owned material before COMMIT where necessary. No post-COMMIT observation masquerades as mutation receipt.',
  'Preserve legacy add/remove/handle API adapters and sender framed-response bytes, idempotent/rejected behavior, custom quotas and allocator. No new acquisition/rename/self-name/chat-filter policy or native format.',
  'In existing confined Main wrapper, capture optional private NormalWorldInitialization only during each candidate recipient own genuine world-records Tick callback; require actual entry Written and pure current_on_game, TW God2CharacterConnection, same exact account+character, retained exact Session incarnation, stable phase/battle, completed supported replay.',
  'For one actual successful sender mutation, recipients must have complete pinned Snapshot exactly equal to the actual mutation before Snapshot. Transfer exact original A5/A4 logical bytes only to such current ready peers, and update their locally projected whole Snapshot to actual after material. Preserve requesting response queue and exclude sender from fanout. Never treat queue submission as Written/ACK/client-cache adoption.',
  'Incomplete, source-mismatched, unsupported CP950, CN/fixture, unready, stale receipt or transitioned peers get no live delta. Existing replay and source-mismatch failclose/reconnect behavior stays selected; no new pending barrier/replay/reset/timing policy.',
  'Add a narrowly typed Session enqueue using the existing private NormalWorldInitialization plus actual captured phase/battle. Reuse original world-frame encoding/FIFO/budget path; before queue publication on strand recheck exact private initialization Data/Entry, mode, accepted world tail, retired/closing state and captured epoch. Existing generic sender remains unchanged.',
  'Do not use send_world_records_observed for another Session: its TLS requires the actual callback owner. Do not borrow PRIVATE0083 world_generation or bind a fake common delivery identity. Existing generic send_world_records lacks the necessary queued identity guard.'
 ],
 'recipient_identity':'Exact immutable CP950 captured-name bytes are identity/cache material, not display translation. No OpenCC, locale conversion or Unicode folding. TW-only receipt-qualified peers share existing native shape; CN is excluded pending separate native proof.',
 'affected_source_files':['src/db/SqliteOwnedBlacklistRepository.h','src/db/SqliteOwnedBlacklistRepository.cpp','src/handlers/OwnedBlacklistService.h','src/handlers/OwnedBlacklistService.cpp','src/core/Application.cpp','src/net/Session.h','src/net/Session.cpp'],
 'actual_private_handle':'Session::NormalWorldInitialization private Entry/Data and normal_world_initialization_current_on_game are available; neither is a lease or grant. No existing safe cross-Session queued normal-receipt sender exists, so that typed enqueue is the concrete necessary transport delta.',
 'async_custody_design':[
  'Private Session normal-entry OutputHandle is created only from the recipient own actual Tick callback and its private initialization. Shared owning handle captures actual TW mode/account/character/phase/battle; Main stop/disconnect and Session close/reinitialize/transfer revoke it. No public arbitrary owner/callback mintage.',
  'Typed enqueue returns private Pending/Queued/Failed observation. Strand compares exact private initialization identity, entry, revoked/retired state, captured epoch, accepted world tail and closing immediately before insertion; same original FIFO/framing/budget path. Queued is actual insertion only, not Written or native ACK.',
  'Game-confined Main retains exact before/after and immutable original A5/A4 material while Pending. It publishes the after submitted-source Snapshot only when actual Queued is observed, never disguising Pending/Failed as current client state. Each recipient own Tick polls the attempt before new selection.',
  'Minimal variant requires idle eligible peers. A subsequent actual same-owner mutation while a peer push is Pending revokes/closes that peer for existing reconnect durable replay rather than silently missing a delta, replaying a mutation or asserting pending chain freshness. Failure also poisons/revokes/closes that recipient; sender original response/COMMIT is preserved.',
  'Retain strong recipient handles collected before calls; do not hold map iterators/references across observers or callbacks. Use existing confined dispatch reentry poison. After each call recheck retained exact Session/handle, source and epoch. Stop revokes all handles before service/map release.'
 ],
 'failure_semantics':'A mutation remains durable after COMMIT. Delivery failure cannot roll back or rerun it; sender original behavior retained. Recipient target guards prevent stale epoch delivery; connection failure recovers from existing durable inactive-first replay. No native ACK or all-peer atomic delivery claimed.',
 'implementation_status':'SOURCE PROPOSAL ONLY, awaiting root approval/baseline; no tracked edits.',
 'remaining':'Original server permissions/quotas/rename lifecycle, CN wire, recipients lacking private normal entry, incomplete/mismatched replay, pending attempt chaining/all-peer lossless concurrency and native acceptance remain OPEN. Minimal idle-ready branch is a concrete integration delta, not full-blacklist completion.',
 'credits':{'new_opcode':0,'new_native_format':0,'whole_route':0,'native_acceptance':0},
 'execution':'Only current source bytes, JSON text projection, hashing and git read custody; no target/API/SQL/codec/native/build/tests.'
}
js('source-change-proposal.json',proposal)
js('source-references.json',{'snapshot_head':head,'sources':refs,'cuts':cuts})
js('read-failures-and-corrections.json',{'wildcard_read_failure':'rg literal src/game/SharedTaiwanWorldRecordSource.* rejected by Windows path syntax; no authority derived, exact discovered sources subsequently selected.',
 'discovery_output_truncated':'Initial rg over artifacts yielded overbroad historic path inventory; excluded from absence/authority evidence; bounded current ledger and src paths used.',
 'tracked_edits':False,'target_execution':False})
for r in refs:
 data=(ROOT/r['path']).read_bytes()
 if sha(data)!=r['sha256']:raise RuntimeError('Source changed during capture')
js('custody.json',{'snapshot_head':head,'end_head':git('rev-parse','HEAD').decode().strip(),
 'tracked_status':git('status','--porcelain','--untracked-files=no').decode(),
 'source_hash_readback':True,'helper_executed_once':True,'code_delta':False})
members=[]
for p in sorted(OUT.rglob('*')):
 if p.is_file():
  data=p.read_bytes();members.append({'name':p.relative_to(OUT).as_posix(),'bytes':len(data),'sha256':sha(data)})
js('SEAL.json',{'schema':'individual-member-sha256-v1','head':head,'member_count':len(members),
 'total_bytes':sum(m['bytes'] for m in members),'native_complete_routes':0,'members':members})
for m in members:
 data=(OUT/m['name']).read_bytes()
 if len(data)!=m['bytes'] or sha(data)!=m['sha256']:raise RuntimeError('Sealed member mismatch')
seal=(OUT/'SEAL.json').read_bytes();helper=Path(__file__).read_bytes()
print(json.dumps({'head':head,'members':len(members),'bytes':sum(m['bytes'] for m in members),
 'seal_sha256':sha(seal),'seal_bytes':len(seal),'helper_bytes':len(helper),'helper_sha256':sha(helper)}))
