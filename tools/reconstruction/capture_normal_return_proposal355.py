"""Read/hash retained source only; no target or source-module execution."""
from pathlib import Path
import hashlib,json,subprocess
R=Path('C:/Users/risei/Desktop/God2/God2-Server')
O=Path(__file__).resolve().parent
PRIOR=O.parent/'round354-normal-control-response-custody-proposal'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
    p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise RuntimeError('Retain existing '+str(p))
    p.write_bytes(b if isinstance(b,bytes) else (json.dumps(b,indent=2)+'\n').encode())
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()
assert head=='b934e539e9d0cb279e2d6b58678afdb7b555dcf9',head
sealraw=(PRIOR/'seal.json').read_bytes();seal=json.loads(sealraw)
for x in seal['members']:
    n=x.get('path',x.get('name'));b=(PRIOR/n).read_bytes()
    assert len(b)==x['bytes'] and sha(b)==x['sha256'],n
assert len(seal['members'])==29 and sum(x['bytes'] for x in seal['members'])==1195049
put('prior354-proposal-verification.json',dict(seal_path=str(PRIOR/'seal.json'),seal_bytes=len(sealraw),seal_sha256=sha(sealraw),members=29,member_bytes=1195049,individual_readback=True,copied=False))
names=['src/core/Application.cpp','src/core/SharedWorldHostPlan.h','src/net/Session.h','src/net/Session.cpp','src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp','src/handlers/OwnedPkOutboxPublication.h','src/handlers/OwnedTaiwanPkRoomBackend.h','src/handlers/OwnedTaiwanPkEntryPreparation.h','src/db/SqliteDatabase.h','src/db/SqliteDatabase.cpp','src/game/OwnedTaiwanPkReturnRoleTextSource.h','src/game/OwnedTaiwanPkAppearanceSource.h','src/handlers/RecoveredMovementService.h','src/handlers/RecoveredMovementService.cpp','src/handlers/RecoveredBattleService.cpp','src/game/SharedTaiwanNativeWorldEntryOfferSource.h','src/game/SharedTaiwanNativeWorldEntryOfferSource.cpp']
refs=[];blobs={}
for n in names:
    p=R/n;b=p.read_bytes();blobs[n]=b
    put('sources/'+n,b)
    refs.append(dict(path=str(p),relative=n,bytes=len(b),sha256=sha(b),line_count=len(b.splitlines()),whole_source=True,head=head))
put('source-references.json',refs)
spans=[('main-null-room-owner','src/core/Application.cpp',2176,2186),('main-actual-room-provider','src/core/Application.cpp',2302,2321),('main-diagnostic-terminal-release','src/core/Application.cpp',6559,6583),('normal-init-current','src/net/Session.cpp',2596,2638),('actual-terminal-drain-source','src/net/Session.cpp',935,982),('future-init-preparation-only','src/net/Session.cpp',3324,3366),('actual-paired-return-retention','src/handlers/OwnedPkOutboxPublication.h',566,656),('same-db-backend-and-return-issuer','src/db/SqliteDatabase.cpp',427,524),('complete-return-scene-contract','src/cn/world/SharedActorVisibility.h',289,354),('private-return-plan-state','src/cn/world/SharedActorVisibility.cpp',44,80),('full-return-scene-readset','src/cn/world/SharedActorVisibility.cpp',146,287),('complete-return-preparation','src/cn/world/SharedActorVisibility.cpp',288,395),('movement-battle-resume','src/handlers/RecoveredMovementService.cpp',346,355),('movement-transfer-commit','src/handlers/RecoveredMovementService.cpp',428,455),('movement-transfer-final-receipt','src/handlers/RecoveredMovementService.cpp',501,514),('diagnostic-state-only-release','src/handlers/RecoveredBattleService.cpp',605,616),('full-entry-real-issuer-contract','src/game/SharedTaiwanNativeWorldEntryOfferSource.h',20,80),('appearance-actual-full-witness-contract','src/game/OwnedTaiwanPkAppearanceSource.h',22,67)]
cuts=[]
for label,n,lo,hi in spans:
    lines=blobs[n].splitlines(keepends=True);b=b''.join(lines[lo-1:hi])
    assert lo>0 and hi<=len(lines)
    put('cuts/'+label+'.txt',b)
    cuts.append(dict(label=label,path=n,first_line=lo,last_line=hi,bytes=len(b),sha256=sha(b),whole_method_claim=False,role='Exact source excerpt; complete surrounding source independently retained.'))
put('selected-source-cuts.json',cuts)
for n in names:assert (R/n).read_bytes()==blobs[n],n
put('capture-complete.json',dict(head=head,whole_sources=len(refs),whole_source_bytes=sum(x['bytes'] for x in refs),cuts=len(cuts),cut_bytes=sum(x['bytes'] for x in cuts),prior_members_verified=29,tracked_edits=False,proposal_only=True,new_method_opcode_format_route_credits=0))
print((O/'capture-complete.json').read_text())
