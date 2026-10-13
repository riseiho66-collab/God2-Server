from pathlib import Path
import hashlib
import json
import subprocess
import sys

S=Path('C:/Users/risei/Desktop/God2/God2-Server')
O=Path(__file__).resolve().parent
A=O.parent
T=A/'round363-owned-bootstrap-input-continuation-implementation'
HEAD='566923291db5de40dcc7d1a153cde60cfc94d87c'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(r,b):
    p=O/r;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b)
def js(r,v):put(r,(json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())
assert len(sys.argv)==4,'Require final T seal SHA/count/bytes'
tsha,tcount,tbytes=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
prior=[]
for name,seal,pin,count,total in [
    ('round362-owned-skill-bootstrap-independent-source-review','SEAL.json',
     'b144687f8bbbf98b631f04175a4e83a22979bdbe8b253513906db8e96d882e69',48,2975179),
    ('round363-owned-bootstrap-input-continuation-proposal','SEAL.json',
     'c699aa16e9422f8def65db463ec16bf30603a433494dc93d4a65b9700f6c843d',22,1121940),
    (T.name,'seal.json',tsha,tcount,tbytes)]:
    root=A/name;sb=(root/seal).read_bytes();v=json.loads(sb)
    size=v.get('member_bytes',v.get('total_bytes'))
    assert sha(sb)==pin and len(v['members'])==v['member_count']==count
    assert type(size) is int and size==sum(m['bytes'] for m in v['members'])==total
    seen=set()
    for m in v['members']:
        rel=m.get('path') or m['name'];assert rel not in seen;seen.add(rel)
        p=root/rel;assert p.resolve().is_relative_to(root.resolve())
        b=p.read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
    prior.append(dict(root=root.as_posix(),seal_sha256=pin,member_count=count,member_bytes=total,members=v['members']))
js('upstream-individual-verification.json',prior)
pins=json.loads((T/'final-current-pins-v7.json').read_bytes())
assert len(pins)==3
expected={'src/net/Session.h':(35781,'49875550c8033c246b38ca747c6e8672468597529e4bd6cdfb1612c01b622afa'),
    'src/net/Session.cpp':(252277,'9b86c261e4343f46c16523b26caee4b168aee35d36a064c596c1b0a81f9cdfdc'),
    'src/core/Application.cpp':(735319,'8bc08e5c100376bb255412341c0719772e748976226dfe49caf7fd64e0761ad4')}
current={};old={};refs=[]
for p in pins:
    rel=p['path'];b=(S/rel).read_bytes()
    assert (len(b),sha(b))==expected[rel]==(p['bytes'],p['sha256'])
    current[rel]=b;old[rel]=subprocess.check_output(['git','show',HEAD+':'+rel],cwd=S)
    for state,raw in [('current',b),('baseline',old[rel])]:
        retained=state+'/'+rel;put(retained,raw)
        refs.append(dict(actual_path=(S/rel).as_posix(),retained=retained,bytes=len(raw),sha256=sha(raw),
            source_state=state,baseline_head=HEAD))
frozen=['src/handlers/RecoveredBattleService.h','src/handlers/RecoveredBattleService.cpp',
    'src/db/SqliteCompanionRepository.h','src/db/SqliteCompanionRepository.cpp',
    'src/db/SqliteRecoveredCharacterRepository.h','src/db/SqliteRecoveredCharacterRepository.cpp',
    'src/game/Battle.cpp','src/db/SharedSkillDefinition.h','src/db/SharedSkillDefinition.cpp',
    'src/db/NativeSkillCatalog.cpp','src/core/Config.h','src/game/ShunyingSanshazhan.h',
    'src/game/ThousandBulls.h','src/cn/world/CnBattleSkillSelectionSource.cpp']
for rel in frozen:
    b=(S/rel).read_bytes();assert b==subprocess.check_output(['git','show',HEAD+':'+rel],cwd=S)
    retained='frozen/'+rel;put(retained,b)
    refs.append(dict(actual_path=(S/rel).as_posix(),retained=retained,bytes=len(b),sha256=sha(b),
        source_state='unchanged published dependency',source_head=HEAD))
js('source-references.json',refs)
work=current.copy();receipt_refs=[];edits=0
for name in ['correction-v7.json','correction-v6.json','correction-v5.json','correction-v3.json','exact-edits-and-inverse.json']:
    raw=(T/name).read_bytes();v=json.loads(raw);edits+=len(v['edits'])
    for e in reversed(v['edits']):
        before,after=bytes.fromhex(e['old_hex']),bytes.fromhex(e['new_hex'])
        assert after and work[e['path']].count(after)==e.get('count',1),e['path']
        work[e['path']]=work[e['path']].replace(after,before)
    put('custody/'+name,raw)
    receipt_refs.append(dict(actual_path=(T/name).as_posix(),retained='custody/'+name,bytes=len(raw),sha256=sha(raw)))
assert edits==42
for rel in current:assert work[rel]==old[rel],rel
js('three-whole-composed-inverse-proof.json',dict(source_head=HEAD,whole_inverses_equal=True,
    edit_count=42,source_count=3,new_files=0,correction_order=['v7','v6','v5','v3','initial18'],receipts=receipt_refs,pins=pins))
specs=[('src/net/Session.h',418,429),('src/net/Session.cpp',330,368),
    ('src/net/Session.cpp',600,609),('src/net/Session.cpp',1088,1127),
    ('src/net/Session.cpp',1967,2041),('src/net/Session.cpp',2042,2068),
    ('src/net/Session.cpp',2247,2279),('src/net/Session.cpp',2355,2449),
    ('src/net/Session.cpp',2502,2525),('src/net/Session.cpp',2540,2568),
    ('src/net/Session.cpp',2618,2699),('src/net/Session.cpp',2812,2838),
    ('src/core/Application.cpp',6499,6515)]
cuts=[]
for i,(rel,a,z) in enumerate(specs):
    lines=current[rel].splitlines(keepends=True);assert 1<=a<=z<=len(lines)
    b=b''.join(lines[a-1:z]);retained='cuts/%02d-%s-L%d-L%d.txt'%(i,Path(rel).name,a,z)
    put(retained,b);cuts.append(dict(actual_path=(S/rel).as_posix(),retained=retained,bytes=len(b),sha256=sha(b),
        first_line=a,last_line=z,boundary='selected excerpt; complete source retained'))
js('source-cuts.json',cuts)
put('REPORT.md',b'''# Round363 independent owned input continuation source review

PASS for corrected final v7 only. Twenty whole references retain current3/base3/frozen14; thirteen selected excerpts are separate. Forty-two exact literal inverses v7/v6/v5/v3/initial18 return all three whole files to566923291db5de40dcc7d1a153cde60cfc94d87c. No new source files. Final implementation, A363 proposal and prior I362 every member/contained path/integer count/sum/length/hash were verified without rerunning any successful helper. Source/hash/git/manual only; no product API/SQL/runtime/native/CRT/VM/parser/codec/compiler/build/tests or tracked edit.

Historical v2 was not a final PASS. Root identified old-read rejection and incomplete initiation/handoff containment; independent review identified close retirement's closing flag bypassing original cleanup, TLS being checked after a GAME pointer read, and catch identity being lost when failure cleared the hold. Additive v3/v5/v6 close these: was_closing snapshot, TLS-before-capture, persistent retired latch, entered-with-opted local flags, constchar/noexcept retirement before allocation/logger, outer complete handoff catch and full initiation/completion catches. V7 additionally checks remembered entry identity OR current atomic hold OR retired latch in the three catches, covering a new GAME arm during an older operation. Latest marker checks are not general executor convergence proof. Early candidates, preflight failures and all receipts remain immutable upstream history.

App arms only after actual362 typed qualifier and identity current succeeded, using the SAME actual original callback WorldResponseWrite. Arm validates own TLS before serial GAME fields, same private capture/receipt, Pending/current and duplicate restrictions. Exact atomic GAME Attempt hold precedes strand handoff; independent delivery Lease destructor retires dropped work despite the strong hold. Private Data/Attempt/session identity is not synthetic Pending metadata. IO reads only immutable receipt/weakSession plus transport-safe atomics, never bare game-owned account/character IDs or SQL/source callbacks.

Read/resume/feed reject retirement and hold before normal decoding; retained input still obeys16384 bytes, original frame/batch/record8192/deadline/battle-generation limits. Inflight suffix is appended in order, not dropped, split, reclassified or decoded while held. Pre-arm already parsed/posted GAME batch cannot be restored to raw: while any hold/latch exists it is rejected as a whole BEFORE callbacks/capture/owner mutation. This explicit limit is not automatic success or a native timing claim. Unarmed ordinary/PK/chat source behavior remains the old branch.

Accepted strand handoff checks same private Attempt/full returned response and original FIFO budgets, attaches Lease to that exact Write and starts the normal FIFO. Physical success requires the real target front/frame/wire/session/transferred identity and Pending-to-Written CAS. Every original observer/marker/log/pop/nextqueue operation completes before releasing the exact hold once. Written stays the passive physical fact. Release is CASArmed-to-Released then exact atomic hold removal; it calls original resume only if no older game_busy/read_inflight owner. Existing older completion owns its existing continuation, so no second read is launched. No callback or native ACK/cache/turn grant is invented.

Retired is persistent even after pointer removal, preventing legacy fallback. Pending Attempt/Lease drop atomically fails/marks close_requested; live strand retirement closes socket/input before logger/allocation. Exceptions in any opted handoff gate or async initiation/completion, including older FIFO prefix work, failclose under remembered entered identity. First opted close still runs the full original cleanup. Failure after release or Written never demotes the successful write, retries a durable prefix or resumes a successor phase. No unavailable-executor/general shutdown convergence is claimed; stopped/drop contexts remain bounded failure limits.

CUSTOM-0141 is an owned-bootstrap local continuation policy, not original native skill timing.362 Written admission,361 fresh selected saved readset/CAS/checkpoint, actual advertised keys/controlled actor and existing owner rules remain unchanged frozen dependencies. Same parsed Timer36/C35 batch is not retroactively split. CN453/current/host and full native list/control/auxiliary/actor grants stay separate OPEN suppliers; no raw row/zero reset/learned grant or unhosted factory is added. Runtime/native acceptance, native formulas/wide presentation/full route credits remain unclaimed0.
''')
js('capture-complete.json',dict(status='PASS_FINAL_V7',source_head=HEAD,current_count=3,baseline_count=3,
    frozen_count=len(frozen),whole_count=len(refs),cut_count=len(cuts),edits=42,
    prior_members=sum(p['member_count'] for p in prior),prior_bytes=sum(p['member_bytes'] for p in prior),
    product_execution=False,tracked_edits=False,native_route_credit=0))
for rel,b in current.items():assert (S/rel).read_bytes()==b
members=[]
for p in sorted(O.rglob('*')):
    if p.is_file() and p.name!='SEAL.json':
        b=p.read_bytes();members.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
total=sum(m['bytes'] for m in members);assert type(total) is int
js('SEAL.json',dict(status='PASS_FINAL_V7',member_count=len(members),member_bytes=total,members=members))
for m in members:
    b=(O/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
sb=(O/'SEAL.json').read_bytes();hb=Path(__file__).read_bytes()
assert b'\r' not in hb and not hb.startswith(b'\xef\xbb\xbf') and hb.endswith(b'\n') and not hb.endswith(b'\n\n')
print(json.dumps(dict(member_count=len(members),member_bytes=total,seal_bytes=len(sb),seal_sha256=sha(sb),
    helper_bytes=len(hb),helper_sha256=sha(hb))))
