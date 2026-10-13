from pathlib import Path
import hashlib
import json
import subprocess
import sys

S=Path('C:/Users/risei/Desktop/God2/God2-Server')
O=Path(__file__).resolve().parent
A=O.parent
T=A/'round362-owned-skill-bootstrap-write-implementation'
HEAD='7b5efc911fd20d8d9254f80a080a1de2d5751297'

def sha(b):return hashlib.sha256(b).hexdigest()
def put(r,b):
    p=O/r;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b)
def js(r,v):put(r,(json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())
assert len(sys.argv)==4,'Require frozen T seal SHA/member count/bytes'
tsha,tcount,tbytes=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
prior=[]
for name,seal,pin,count,total in [
    ('round362-shared-owned-skill-publication-authority','SEAL.json',
     '9d28223c7297bdd9ab1a9ba3dc18e65ac179e1fc932f433f55d215be77c1050b',46,1360898),
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
pins=[dict(path='src/core/Application.cpp',bytes=735180,sha256='da82cc321fe4888ebbdf816e281f57251916adc2f8b94715b55e98fbc3d7e985'),
    dict(path='src/handlers/RecoveredBattleService.h',bytes=9053,sha256='6b72768cb05b77c8c064f17d814dec62650bc226db9ad668144f29d58d637fc5'),
    dict(path='src/handlers/RecoveredBattleService.cpp',bytes=48477,sha256='5a19c0bd5398e08817e69601e3ac9e39cb96e57cc9d4ba7519055a0a4834d87c')]
current={};old={};refs=[]
for p in pins:
    rel=p['path'];b=(S/rel).read_bytes()
    assert len(b)==p['bytes'] and sha(b)==p['sha256']
    current[rel]=b;old[rel]=subprocess.check_output(['git','show',HEAD+':'+rel],cwd=S)
    for state,raw in [('current',b),('baseline',old[rel])]:
        retained=state+'/'+rel;put(retained,raw)
        refs.append(dict(actual_path=(S/rel).as_posix(),retained=retained,bytes=len(raw),sha256=sha(raw),
            source_state=state,baseline_head=HEAD))
frozen=['src/net/Session.h','src/net/Session.cpp','src/db/SqliteCompanionRepository.h',
    'src/db/SqliteCompanionRepository.cpp','src/db/SqliteRecoveredCharacterRepository.h',
    'src/db/SqliteRecoveredCharacterRepository.cpp','src/game/ShunyingSanshazhan.h','src/game/ThousandBulls.h',
    'src/db/SharedSkillDefinition.h','src/db/SharedSkillDefinition.cpp','src/db/NativeSkillCatalog.cpp',
    'src/game/Battle.cpp','src/protocol/ShunyingSanshazhanReply.h','src/protocol/ThousandBullsReply.h',
    'src/core/Config.h','src/cn/world/CnBattleSkillSelectionSource.cpp','src/cn/world/SharedBattleSkillPublication.cpp']
frozen_data={}
for rel in frozen:
    b=(S/rel).read_bytes();assert b==subprocess.check_output(['git','show',HEAD+':'+rel],cwd=S)
    frozen_data[rel]=b;retained='frozen/'+rel;put(retained,b)
    refs.append(dict(actual_path=(S/rel).as_posix(),retained=retained,bytes=len(b),sha256=sha(b),
        source_state='unchanged published dependency',source_head=HEAD))
js('source-references.json',refs)

work=current.copy();receipts=[]
for name in ['transition-correction-v5.json','identity-correction-v4.json','exact-edits-and-inverse.json']:
    raw=(T/name).read_bytes();v=json.loads(raw)
    for e in reversed(v['edits']):
        before,after=bytes.fromhex(e['old_hex']),bytes.fromhex(e['new_hex'])
        assert after and work[e['path']].count(after)==e.get('count',1),e['path']
        work[e['path']]=work[e['path']].replace(after,before)
    receipts.append(dict(actual_path=(T/name).as_posix(),bytes=len(raw),sha256=sha(raw),retained='custody/'+name))
    put('custody/'+name,raw)
for rel in current:assert work[rel]==old[rel],rel
js('three-whole-composed-inverses.json',dict(source_head=HEAD,current_pins=pins,existing_count=3,new_count=0,
    whole_inverse_equal=True,correction_order=['v5','v4','initial'],receipts=receipts))

specs=[('src/core/Application.cpp',6124,6178),('src/core/Application.cpp',6205,6220),
    ('src/core/Application.cpp',6337,6354),('src/core/Application.cpp',6408,6420),
    ('src/core/Application.cpp',6497,6513),('src/handlers/RecoveredBattleService.h',76,92),
    ('src/handlers/RecoveredBattleService.h',135,146),
    ('src/handlers/RecoveredBattleService.cpp',33,63),('src/handlers/RecoveredBattleService.cpp',148,207),
    ('src/handlers/RecoveredBattleService.cpp',520,549),
    ('src/handlers/RecoveredBattleService.cpp',582,600),
    ('src/net/Session.cpp',2633,2670),('src/net/Session.cpp',2235,2270),('src/net/Session.cpp',2405,2420),
    ('src/net/Session.cpp',3696,3708)]
cuts=[]
for i,(rel,start,end) in enumerate(specs):
    b=current.get(rel,frozen_data.get(rel));lines=b.splitlines(keepends=True)
    assert 1<=start<=end<=len(lines)
    raw=b''.join(lines[start-1:end]);retained='cuts/%02d-%s-L%d-L%d.txt'%(i,Path(rel).name,start,end)
    put(retained,raw);cuts.append(dict(actual_path=(S/rel).as_posix(),retained=retained,bytes=len(raw),sha256=sha(raw),
        first_line=start,last_line=end,boundary='selected excerpt; complete source retained'))
js('source-cuts.json',cuts)
put('REPORT.md',b'''# Round362 independent owned bootstrap source review

PASS for corrected final v5 three candidates. Twenty-three whole references retain current3/base3/frozen17 with deliberate source state labels. Three complete byte-inverses v5 thenv4 theninitial equal immutable7b5efc911fd20d8d9254f80a080a1de2d5751297; no new files. Prior A362 and final implementation each member/contained path/integer counts/sums/length/hash were verified without rerunning any successful helper. Source/hash/git/manual only: no product API/SQL/native/CRT/VM/parser/codec/compiler/build/tests/runtime or tracked edit.

Historical initial candidate was NOT a final PASS: root found meaningful custody gaps after early review. Cosmetic pose epoch had been used for skill qualification, and observer changes could be hidden by a newly captured receipt/bind epoch. Additive v4 adds a separate owned-bootstrap generation, active/unconsumed action/control/initial-control checks and original tuple fences. V5 follows the actual existing set_state result rather than predicting+1. Initial and intermediate drafts/receipts remain upstream historical evidence, not silently refreshed.

Actual App observes one owning full deity roster for both126/150 keys and resolves only the existing common owner namespace. Same selected saved row decisions produce the known exact87/id/80 records and the policy's advertised saved-key set. No std::search or substring occurrence is promoted to native record boundary. Native profiles/original CN qualification remain separate. The original framed vitals vector is prepared and captured once; its exact bytes are returned without decode/re-encode after observation. Existing Session remains unchanged.

App fences its original Session/account/character/phase/battle generation immediately before the existing noexcept set_state(InBattle), then freezes only that actual local result. No observer/SQL rebase or assumed increment is allowed. Capture/bind and final return recheck that tuple. Qualifier retains arguments before repository observations, checks the private receipt's owning wire-object identity, real Session/controlled actor, exact saved-key set and active/unconsumed binding, then reads fullsame actual rosterCurrent under the inherited busy/reentry/deferred-remove guard. Caught handle/bind/remove reentry poisons the operation; active bindings are erased only after guard retirement. The independent bootstrap epoch does not use cosmetic pose metadata.

Only supplied bootstrap-bound owned C35 requires Written/current private WorldResponseWrite; Pending/Failed cannot authorize this CUSTOM-0140 source policy. Wrong thread/old Session/phase/battle generation fail the private current checks. Absent receipts preserve other explicitly trusted bindings. Written is exact local original callback output, not native ACK/list adoption/cache/turn grant. Actual Session final frame equality/FIFO identity/async_write checks and RAII failure are inherited unchanged. This is not SQL/network atomicCAS; early pending arrival/native timing and post-guard storage changes remain acceptance/source limits.

After the local write check, command handling still fresh-reads SelectedDeitySkillReadset, stages the original trusted action/encoder and onceMP rule, checks current/reentry, uses361 typed same-transaction saved validation and atomic checkpoint/resources/settlement paths before in-memory publication. A later throw cannot undo an already committed durable prefix; no rollback/retry/native adoption is promised. Manual/trial/ordinary policies, TW effects/formulas/wire, fixed class constants, native source907 pins, Session contract and originalCN453 sources remain byte-exact dependencies. CN actual actor/list/resources/event/host/custom client bridge and whole native issued-list/control/auxiliary state stay OPEN. No new native method/format/opcode/fullroute/formula/acceptance credit.
''')
js('capture-complete.json',dict(status='PASS',source_head=HEAD,current_count=3,baseline_count=3,
    frozen_count=len(frozen),whole_count=len(refs),cut_count=len(cuts),whole_inverses=3,
    prior_members=sum(p['member_count'] for p in prior),prior_bytes=sum(p['member_bytes'] for p in prior),
    tracked_edits=False,target_execution=False,native_route_credit=0))
for rel,b in current.items():assert (S/rel).read_bytes()==b
members=[]
for p in sorted(O.rglob('*')):
    if p.is_file() and p.name!='SEAL.json':
        b=p.read_bytes();members.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
total=sum(m['bytes'] for m in members);assert type(total) is int
js('SEAL.json',dict(status='PASS',member_count=len(members),member_bytes=total,members=members))
for m in members:
    b=(O/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
sb=(O/'SEAL.json').read_bytes();hb=Path(__file__).read_bytes()
assert b'\r' not in hb and hb.endswith(b'\n') and not hb.endswith(b'\n\n')
print(json.dumps(dict(member_count=len(members),member_bytes=total,seal_bytes=len(sb),seal_sha256=sha(sb),
    helper_bytes=len(hb),helper_sha256=sha(hb))))
