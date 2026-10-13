from pathlib import Path
import hashlib
import json
import subprocess

S = Path('C:/Users/risei/Desktop/God2/God2-Server')
O = Path(__file__).resolve().parent
HEAD = '7b5efc911fd20d8d9254f80a080a1de2d5751297'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def put(r,b):
    p=O/r
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b)

def js(r,v):
    put(r,(json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode())

prior=[]
for name,pin,count,total in [
    ('round360-common-owner-skill-authority-frontier','e7bcca8b3b0230bcfe03c9c2a0a5bee422b0884eb5ab2bfaa4e1340bbb9bf122',48,1036127),
    ('round360-common-owner-skill-independent-source-review','65845c9b983a00d61b396c1addc2a7c5c487941cace8ea942dbf1e05e15b749f',38,2718050)]:
    root=O.parent/name
    sb=(root/'SEAL.json').read_bytes();v=json.loads(sb)
    assert sha(sb)==pin and len(v['members'])==v['member_count']==count
    assert type(v['member_bytes']) is int and v['member_bytes']==sum(m['bytes'] for m in v['members'])==total
    for m in v['members']:
        p=root/m['path'];assert p.resolve().is_relative_to(root.resolve())
        b=p.read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
    prior.append(dict(root=root.as_posix(),seal_sha256=pin,member_count=count,member_bytes=total,members=v['members']))
js('prior-individual-verification.json',prior)
files=['src/core/Application.cpp','src/net/Session.h','src/net/Session.cpp',
    'src/handlers/RecoveredBattleService.h','src/handlers/RecoveredBattleService.cpp',
    'src/game/SharedTaiwanIssuedSkillSource.h','src/game/SharedTaiwanIssuedSkillSource.cpp',
    'src/game/SharedTaiwanOwnedDeitySkillSource.h','src/game/SharedTaiwanOwnedDeitySkillSource.cpp',
    'src/cn/world/CnBattleSkillSelectionSource.h','src/cn/world/CnBattleSkillSelectionSource.cpp',
    'src/cn/world/SharedBattleSkillPublication.h','src/cn/world/SharedBattleSkillPublication.cpp',
    'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
    'src/protocol/TaiwanNativePrimarySkillList.h','src/core/SharedWorldHostPlan.h',
    'src/core/Application.h','src/core/Config.h','src/core/Config.cpp',
    'src/protocol/ShunyingSanshazhanReply.h','src/protocol/ThousandBullsReply.h']
data={};refs=[]
for rel in files:
    b=subprocess.check_output(['git','show',HEAD+':'+rel],cwd=S);data[rel]=b
    retained='published/'+rel;put(retained,b)
    refs.append(dict(actual_path=(S/rel).as_posix(),retained=retained,bytes=len(b),sha256=sha(b),
        source_head=HEAD,source_state='immutable published source; current candidate may change'))
js('source-references.json',refs)
b=(S/'src/core/Application.cpp').read_bytes()
js('working-Application-digest-observation.json',dict(actual_path=(S/'src/core/Application.cpp').as_posix(),
    bytes=len(b),sha256=sha(b),source_head=HEAD,equal_published=b==data['src/core/Application.cpp'],
    snapshot_only=True))
specs=[('src/core/Application.cpp',6122,6170),('src/core/Application.cpp',6220,6248),
    ('src/core/Application.cpp',6420,6455),('src/core/Application.cpp',6710,6729),
    ('src/handlers/RecoveredBattleService.cpp',459,543),('src/net/Session.h',108,125),
    ('src/net/Session.cpp',2633,2670),('src/net/Session.cpp',2235,2270),
    ('src/net/Session.cpp',2405,2420),('src/game/SharedTaiwanIssuedSkillSource.h',69,111),
    ('src/protocol/TaiwanNativePrimarySkillList.h',100,134),
    ('src/game/SharedTaiwanOwnedDeitySkillSource.cpp',47,94),
    ('src/cn/world/CnBattleSkillSelectionSource.cpp',9,19),
    ('src/cn/world/CnBattleSkillSelectionSource.cpp',87,124),
    ('src/cn/world/SharedBattleSkillPublication.cpp',174,199),
    ('src/cn/world/SharedWorldGameplay.h',94,107)]
cuts=[]
for i,(rel,a,z) in enumerate(specs):
    lines=data[rel].splitlines(keepends=True);assert 1<=a<=z<=len(lines)
    b=b''.join(lines[a-1:z]);retained='cuts/%02d-%s-L%d-L%d.txt'%(i,Path(rel).name,a,z)
    put(retained,b);cuts.append(dict(actual_path=(S/rel).as_posix(),retained=retained,bytes=len(b),sha256=sha(b),
        source_head=HEAD,first_line=a,last_line=z,boundary='selected excerpt; complete source retained'))
js('source-cuts.json',cuts)
js('typed-source-proposal.json',dict(status='READONLY_ACTUAL_BOOTSTRAP_SUPPLIER_PROPOSAL',
    actual_supplier='Application Timer36 owned126/150 S87 bootstrap appended to original vitals frame',
    actual_consumer='RecoveredBattleService bound controlled actor/C35 policy plus361 fresh learned readset and paired checkpoint source',
    proposed_primary_delta=['replace bare bootstrap booleans with owning full SelectedDeitySkillReadsets',
        'qualify exact existing owner rule independently from optional raw profiles',
        'retain actual Session/bound actor/phase/battle generation and final same-readset equality before original frame publication',
        'poison caught source reentry; retain old nonowned/manual/trial behavior and exact original wire'],
    optional_transport_custody='existing WorldResponseWrite of SAME final framed callback response; local Written/current only, not native adoption/turn/grant',
    formal_TW_missing=['complete linked16 auxiliary rows','control_a/control_b','actual primary/secondary actor','complete secondary snapshot','actual common presence ready incarnation'],
    CN_missing=['actual owner-custom definition/list/native actor/resources adapter','genuine learned event/revision and actual87flags/order supplier','real hosted publication owner'],
    new_grants=False,new_native_rows=False,native_route_credit=0,tracked_edits=False))
put('REPORT.md',b'''# Round362 actual owned skill bootstrap publication frontier

Readonly proposal at published7b5efc911fd20d8d9254f80a080a1de2d5751297. Twenty-two whole sources and sixteen selected cuts retain actual suppliers/consumers; working App digest is separate and not asserted equal to a later candidate. Prior A36048/I36038 individual members total3754177B are verified unchanged. No tracked edits, target API, native/CRT/VM/parser/codec/SQL/DB/import/build/compiler/tests/runtime occurred.

Actual minimal supplier exists in Main: the Timer36 owned bootstrap uses selected_deity_has_skill booleans, appends exact existing S87 triples87/id/80 to the original vitals frame, installs the actual RecoveredBattleService policy/controlled actor, and returns that already-framed response. The two owner keys are126/150; no metadata row or input grants them. Round361 now fresh-reads full saved selected skill at the authenticated actual command and carries it to paired same-transaction persistence. That later command proof does not qualify the earlier bootstrap/menu projection produced from bare booleans.

Supported smallest primary delta is to replace those bootstrap booleans with owning full actual SelectedDeitySkillReadsets, resolve existing formal OwnerRule separately from optional raw profiles, and recheck full same selection/deity/revision/provenance/skills plus actual bound actor/Session/phase/battle generation before publishing the same original frame. Caught reentry must poison the captured operation; observers must not leave a borrowed binding iterator live. Keep old trial/manual/nonowned policies, balances, target/MP/checkpoint behavior and TW effects exact. No new common grant, event ID, fake original CN row or unused publisher factory is needed. Proposed implementation files are actual Application and only the existing service/source helpers needed to retain that proof, subject to root authorization.

An additional real transport supplier already exists: Session::observe_world_response captures only the actual own world-records callback's complete original framed output. Its private WorldResponseWrite retains exact wire and Session/phase/account/character/battle/thread epoch; final callback equality, FIFO identity and async_write complete fact produce Pending/Written/Failed. This could retain the SAME actual bootstrap frame, without encode/decode/reframe. Written is local output proof, not remote list adoption/native ACK/turn grant. Requiring it as an action-admission condition would be an explicit narrow owner policy choice, not recovered native behavior or a reason to fabricate client initial state. It is an optional custody proposal, not implemented or a prerequisite to the primary full-readset bootstrap fix.

Do not force the real small bootstrap into SharedTaiwanIssuedSkillSource. Its original primary-list installation requires complete linked16 auxiliary definitions, roster count/selected row, control_a/control_b, primary/secondary actor, optional original86control and full secondary snapshot plus actual common presence/ready lease. Saved selected row and87triples do not provide those fields. Its publish_updates requires an existing exact private full ticket and full catalog requalification. Current Application only delegates an explicitly supplied native_skill_commands binding under an actual common-world host plan; this bounded search found no concrete producer of that complete ticket in the hosted custom bootstrap. No synthetic zero/reset/grant can fill it.

SharedTaiwanOwnedDeitySkillSource's original-native448 Observation cannot be renamed a custom126/150 issuer. Saved readsets can retain owner skills, but raw original-definition/private native qualification remains distinct. CN CnBattleSkillSelectionSource requires an actual native list snapshot and whole original453 row equality; its original kind0 count125 does not include126/150. SharedBattleSkillPublication is only an explicitly supplied CN postcommit source: real original87flags/order, event/revision, actor/list/resources, private native catalog and concrete WorldOwner qualification remain mandatory. SharedWorldGameplay installs/binds an already supplied source and emits no default skills. Those actual CN suppliers/host remain OPEN and are not replaced by the new common owner metadata or a fake committed-learning ID.

No new native method/format/opcode/whole-route/formula/acceptance credit. This is a concrete actual bootstrap supplier connection proposal, with optional exact original response custody separately labelled. Root must approve any source changes. No complete native primary cache, CN custom cast or learned acquisition is claimed.
''')
js('capture-complete.json',dict(status='PASS_BOUNDED_READONLY_PROPOSAL',source_head=HEAD,
    whole_count=len(refs),cut_count=len(cuts),prior_members=86,prior_bytes=3754177,
    tracked_edits=False,target_execution=False,native_route_credit=0))
members=[]
for p in sorted(O.rglob('*')):
    if p.is_file() and p.name!='SEAL.json':
        b=p.read_bytes();members.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=sha(b)))
total=sum(m['bytes'] for m in members);assert type(total) is int
js('SEAL.json',dict(status='PASS_BOUNDED_READONLY_PROPOSAL',member_count=len(members),member_bytes=total,members=members))
for m in members:
    b=(O/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
sb=(O/'SEAL.json').read_bytes();hb=Path(__file__).read_bytes()
assert b'\r' not in hb and hb.endswith(b'\n') and not hb.endswith(b'\n\n')
print(json.dumps(dict(member_count=len(members),member_bytes=total,seal_bytes=len(sb),seal_sha256=sha(sb),
    helper_bytes=len(hb),helper_sha256=sha(hb))))
